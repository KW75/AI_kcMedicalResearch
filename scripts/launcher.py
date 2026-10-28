# =============================================================================
#  launcher.py  |  AI kcMedicalResearch
#  (version shown in the banner is parsed live from SOURCE_CODE/main.py)
# =============================================================================

import getpass
import re
import subprocess
import sys
import os
import shutil
from pathlib import Path

# -----------------------------------------------------------------------------
#  Colorama bootstrap
# -----------------------------------------------------------------------------
try:
    import colorama
    colorama.init()
    _COLORAMA = True
except ImportError:
    os.system('')
    _COLORAMA = False

BASE   = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Ollama model list, default and descriptions, shared with the app so the
# launcher and the UI show the same thing. ollama_models.py is stdlib only.
_SOURCE_DIR = str(BASE / 'SOURCE_CODE')
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from ollama_models import (  # noqa: E402
    RANKS_SOURCE, choose_default, describe, list_ollama_models,
    missing_ranked, model_capabilities,
)
from time_limits import CHOICES as TIME_CHOICES, DEFAULT as TIME_DEFAULT, LABELS as TIME_LABELS  # noqa: E402
import env_file  # noqa: E402


def _project_meta() -> tuple[str, str]:
    """Parse (VERSION, supported-Python range) from SOURCE_CODE/main.py.

    Parsed live rather than hardcoded: the previous banner claimed
    v2.4.3 / '400 passed - 3 skipped' nine versions after either was
    true - a displayed claim nobody re-verifies. Parsed with a regex,
    not an import, so the banner doesn't pay main.py's import chain.
    A test count is deliberately NOT displayed: it decays every
    session and nothing here can verify it.
    """
    version, py_range = '?', '3.x'
    try:
        src = (BASE / 'SOURCE_CODE' / 'main.py').read_text(
            encoding='utf-8', errors='replace')
        m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', src, re.M)
        if m:
            version = m.group(1)
        lo = re.search(r'^MIN_PYTHON\s*=\s*\((\d+),\s*(\d+)\)', src, re.M)
        hi = re.search(r'^MAX_PYTHON_EXCLUSIVE\s*=\s*\((\d+),\s*(\d+)\)', src, re.M)
        if lo and hi:
            py_range = (f'{lo.group(1)}.{lo.group(2)} - '
                        f'{hi.group(1)}.{int(hi.group(2)) - 1}')
    except OSError:
        pass
    return version, py_range

# -----------------------------------------------------------------------------
#  Background detection  (4-layer strategy)
# -----------------------------------------------------------------------------
def _detect_background() -> str:
    """Return 'dark' or 'light'."""

    override = os.environ.get('CLI_THEME', '').strip().lower()
    if override in ('dark', 'light'):
        return override

    colorfgbg = os.environ.get('COLORFGBG', '')
    if colorfgbg:
        try:
            return 'dark' if int(colorfgbg.split(';')[-1]) < 8 else 'light'
        except ValueError:
            pass

    if os.name == 'nt':
        try:
            import ctypes
            import ctypes.wintypes

            class _COORD(ctypes.Structure):
                _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]

            class _SMALL_RECT(ctypes.Structure):
                _fields_ = [
                    ('Left',   ctypes.c_short), ('Top',    ctypes.c_short),
                    ('Right',  ctypes.c_short), ('Bottom', ctypes.c_short),
                ]

            class _CSBI(ctypes.Structure):
                _fields_ = [
                    ('dwSize',               _COORD),
                    ('dwCursorPosition',     _COORD),
                    ('wAttributes',          ctypes.c_ushort),
                    ('srWindow',             _SMALL_RECT),
                    ('dwMaximumWindowSize',  _COORD),
                ]

            k32    = ctypes.windll.kernel32
            handle = k32.GetStdHandle(-11)
            if handle and handle != ctypes.wintypes.HANDLE(-1).value:
                csbi = _CSBI()
                if k32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi)):
                    bg = (csbi.wAttributes >> 4) & 0x0F
                    return 'light' if bg >= 7 else 'dark'
        except Exception:
            pass

    return 'dark'


_BG = _detect_background()

# -----------------------------------------------------------------------------
#  Raw ANSI codes
# -----------------------------------------------------------------------------
_R  = '\033[0m'
_BD = '\033[1m'
_DM = '\033[2m'

_BLK = '\033[30m'; _RED = '\033[31m'; _GRN = '\033[32m'; _YLW = '\033[33m'
_BLU = '\033[34m'; _MAG = '\033[35m'; _CYN = '\033[36m'; _WHT = '\033[37m'

_BBLK = '\033[90m'; _BRED = '\033[91m'; _BGRN = '\033[92m'; _BYLW = '\033[93m'
_BBLU = '\033[94m'; _BMAG = '\033[95m'; _BCYN = '\033[96m'; _BWHT = '\033[97m'

# -----------------------------------------------------------------------------
#  Semantic palette
# -----------------------------------------------------------------------------
if _BG == 'dark':
    FRAME    = _BBLU
    LOGO     = _BCYN
    LOGO_TXT = _BGRN
    TITLE    = _BD + _BWHT
    TEXT     = _BYLW
    ACCENT   = _BCYN
    GOOD     = _BGRN
    WARN     = _BYLW
    ERR      = _BRED
    INFO     = _DM
    HILITE   = _BD + _BMAG
    SEP      = _BBLK
else:
    FRAME    = _BLU
    LOGO     = _BD + _CYN
    LOGO_TXT = _BD + _GRN
    TITLE    = _BD + _BLK
    TEXT     = _BLU
    ACCENT   = _BD + _MAG
    GOOD     = _GRN
    WARN     = _YLW
    ERR      = _RED
    INFO     = _BBLK
    HILITE   = _BD + _MAG
    SEP      = _DM

RESET = _R

# -----------------------------------------------------------------------------
#  Pipeline / provider tables
# -----------------------------------------------------------------------------
MODES = [
    ('1',  'Coding',        '--mode coding'),
    ('2',  'Writing',       '--mode writing'),
    ('3',  'Appraisal',     '--mode appraisal'),
    ('4',  'Search',        '--mode search'),
    ('5',  'RCT Search',    '--mode rct_search'),
    ('6',  'SR Pipeline',   '--mode sr'),
    ('7',  'Data Analysis', None),        # coming soon
    ('8',  'OCR',           None),        # coming soon
    ('9',  'Dry Run',       '--dry-run'),
    ('10', 'Setup',         'setup'),     # launcher sub-menu, not a main.py flag
]

HELP_FILE = BASE / "Readme" / "flashcard-help.html"
ENV_FILE     = BASE / ".env"
ENV_TEMPLATE = BASE / ".env.example"


PROVIDERS = [
    ('1', 'Ollama',    'local - free - default',  '--provider ollama'),
    ('2', 'Qwen',      'Alibaba - recommended',   '--provider qwen'),
    ('3', 'Groq',      'fast inference',          '--provider groq'),
    ('4', 'DeepSeek',  'cost-efficient',          '--provider deepseek'),
    ('5', 'OpenAI',    'GPT-4 vision',            '--provider openai'),
    ('6', 'Anthropic', 'Claude vision',           '--provider anthropic'),
]

VISION_PROVIDERS  = {'qwen', 'openai', 'anthropic', 'groq'}
BLOCKED_FOR_SR    = {'ollama', 'deepseek'}

_MODE_INPUT_MAP = {
    '--mode coding':     'coding',
    '--mode writing':    'writing',
    '--mode appraisal':  'appraisal',
    '--mode search':     'search',
    '--mode rct_search': 'rct_search',
    '--mode sr':         'sr',
}

_MOVE_DESTINATIONS = [
    Path('C:/temp'),
    Path.home() / 'Downloads',
    Path.home() / 'Documents',
]

# -----------------------------------------------------------------------------
#  Helper utilities
# -----------------------------------------------------------------------------
def _W(n: int) -> str:
    return ' ' * n


def clear() -> None:
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except KeyboardInterrupt:
        pass


def safe_input(prompt: str, default: str = '') -> str:
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return default


def hr(width: int = 57, char: str = '-') -> str:
    return f'  {FRAME}{char * width}{RESET}'


def section_header(title: str) -> None:
    pad   = 55 - len(title)
    left  = pad // 2
    right = pad - left
    print(f'  {FRAME}{"-" * left}{RESET}  {TITLE}{title}{RESET}  {FRAME}{"-" * right}{RESET}')


# -----------------------------------------------------------------------------
#  Banner
# -----------------------------------------------------------------------------
def banner() -> None:
    W = _W

    print()
    print(f'  {FRAME}╔═══════════════════════════════════════════════════════╗{RESET}')
    print(f'  {FRAME}║{RESET}                                                       {FRAME}║{RESET}')

    print(f'  {FRAME}║{RESET}   {LOGO}██╗  ██╗ ██████╗{RESET}{W(4)}'
          f'{LOGO_TXT}AI kcMedical Research{RESET}{W(9)}{FRAME}  ║{RESET}')
    print(f'  {FRAME}║{RESET}   {LOGO}██║ ██╔╝██╔════╝{RESET}{W(4)}'
          f'{INFO}─────────────────────{RESET}{W(11)}{FRAME}║{RESET}')
    _ver, _py = _project_meta()
    _ver = _ver[:23]
    print(f'  {FRAME}║{RESET}   {LOGO}█████╔╝ ██║{RESET}{W(9)}'
          f'{ACCENT}Version  {RESET}{HILITE}{_ver}{RESET}{W(23 - len(_ver))}{FRAME}║{RESET}')
    _py = _py[:23]
    print(f'  {FRAME}║{RESET}   {LOGO}██╔═██╗ ██║{RESET}{W(9)}'
          f'{ACCENT}Python   {RESET}{GOOD}{_py}{RESET}{W(23 - len(_py))}{FRAME}║{RESET}')
    _run = 'local first / cloud API'
    print(f'  {FRAME}║{RESET}   {LOGO}██║  ██╗╚██████╗{RESET}{W(4)}'
          f'{ACCENT}Runs     {RESET}{INFO}{_run}{RESET}{W(23 - len(_run))}{FRAME}║{RESET}')
    print(f'  {FRAME}║{RESET}   {LOGO}╚═╝  ╚═╝ ╚═════╝{RESET}{W(36)}{FRAME}║{RESET}')

    print(f'  {FRAME}║{RESET}                                                       {FRAME}║{RESET}')

    tagline = 'Medical Research  -  Review  -  Analysis'
    pad = (53 - len(tagline)) // 2
    print(f'  {FRAME}║{RESET}{W(pad)}  {SEP}{tagline}{RESET}{W(pad + 1)}{FRAME}║{RESET}')

    print(f'  {FRAME}║{RESET}                                                       {FRAME}║{RESET}')
    print(f'  {FRAME}╠═══════════════════════════════════════════════════════╣{RESET}')

    print(f'  {FRAME}║{RESET}  {INFO}Modes  :{RESET}  '
          f'{TEXT}coding  writing  appraisal  search{RESET}{W(8)}{FRAME} ║{RESET}')
    _modes2 = 'rct_search  sr  data_analysis  ocr'
    print(f'  {FRAME}║{RESET}  {INFO}         {RESET}  '
          f'{TEXT}{_modes2}{RESET}{W(42 - len(_modes2))}{FRAME}║{RESET}')
    print(f'  {FRAME}║{RESET}  {INFO}Providers:{RESET} '
          f'{ACCENT}ollama  qwen  groq  openai  anthropic{RESET}{W(3)}{FRAME}  ║{RESET}')
    print(f'  {FRAME}║{RESET}  {INFO}Help   :{RESET}  '
          f'{INFO}python SOURCE_CODE/main.py --help-guide{RESET}{W(2)}{FRAME}  ║{RESET}')

    print(f'  {FRAME}╚═══════════════════════════════════════════════════════╝{RESET}')

    theme_hint = (f'{INFO}  theme: {_BG}'
                  + (' - set CLI_THEME=light to change' if _BG == 'dark' else
                     ' - set CLI_THEME=dark to change')
                  + f'{RESET}')
    print(theme_hint)
    print()


# -----------------------------------------------------------------------------
#  Mode selection menu
# -----------------------------------------------------------------------------
def pick_mode():
    while True:
        clear()
        banner()

        section_header('SELECT PIPELINE')
        print()

        col_items = [(k, lbl, flag) for k, lbl, flag in MODES]
        mid       = (len(col_items) + 1) // 2
        left_col  = col_items[:mid]
        right_col = col_items[mid:]

        # column inner width = 1 + 2 (key, right-aligned) + 2 + 18 + 2 = 25
        CW = 25

        # -- top border --------------------------------------------------------
        print(f'  {FRAME}┌{"-" * CW}┬{"-" * CW}┐{RESET}')

        # -- data rows ---------------------------------------------------------
        for i in range(mid):
            l_key, l_lbl, _ = left_col[i]
            left_cell  = f' {ACCENT}{l_key:>2}{RESET}  {TEXT}{l_lbl:<18}{RESET}  '
            if i < len(right_col):
                r_key, r_lbl, _ = right_col[i]
                right_cell = f' {ACCENT}{r_key:>2}{RESET}  {TEXT}{r_lbl:<18}{RESET}  '
            else:
                right_cell = ' ' * CW
            print(f'  {FRAME}│{RESET}{left_cell}{FRAME}│{RESET}{right_cell}{FRAME}│{RESET}')

        # -- divider before footer ---------------------------------------------
        print(f'  {FRAME}├{"-" * CW}┼{"-" * CW}┤{RESET}')

        # -- footer row 1: C / H -----------------------------------------------
        print(f'  {FRAME}│{RESET} {ACCENT} C{RESET}  {TEXT}{"Custom flags":<18}{RESET}  '
              f'{FRAME}│{RESET} {ACCENT} H{RESET}  {TEXT}{"Help guide":<18}{RESET}  {FRAME}│{RESET}')

        # -- footer row 2: X / blank -------------------------------------------
        print(f'  {FRAME}│{RESET} {ACCENT} X{RESET}  {TEXT}{"Exit":<18}{RESET}  '
              f'{FRAME}│{RESET}{" " * CW}{FRAME}│{RESET}')

        # -- bottom border -----------------------------------------------------
        print(f'  {FRAME}└{"-" * CW}┴{"-" * CW}┘{RESET}')

        print()
        print(f'  {INFO}Tip: Press {ACCENT}Ctrl+C{RESET}{INFO} inside any session to stop and return here.{RESET}')
        print()

        choice = safe_input(
            f'  {ACCENT}>> Enter choice [1-10 / C / H / X]: {RESET}',
            default='X'
        ).upper()

        if choice in ('X', '0', ''):
            return None, None, False, False
        if choice == 'H':
            return None, None, False, True
        if choice == 'C':
            return None, None, True, False
        for key, label, flag in MODES:
            if choice == key:
                return label, flag, False, False

        print(f'\n  {ERR}Invalid choice - please enter 1-10, C, H, or X.{RESET}')
        safe_input(f'  {INFO}Press Enter to try again...{RESET}')


# -----------------------------------------------------------------------------
#  Provider selection menu
# -----------------------------------------------------------------------------
def pick_ollama_model() -> str:
    """Ask which pulled Ollama model to use.

    Returns the model name, or '' if Ollama cannot be reached (the app then
    chooses a model itself). Enter picks the default.
    """
    models = list_ollama_models()
    if not models:
        print()
        print(f'  {WARN}!  Could not list Ollama models. Is the Ollama app running?{RESET}')
        print(f'  {INFO}   Continuing without a model choice; the app will pick one.{RESET}')
        return ''

    default = choose_default(models)
    caps = {m['name']: model_capabilities(None, m['name']) for m in models}
    missing = missing_ranked(models)

    while True:
        print()
        section_header('SELECT  LOCAL  MODEL')
        print()
        for i, m in enumerate(models, start=1):
            mark = f'  {GOOD}(default){RESET}' if m['name'] == default else ''
            print(f'  {ACCENT}{i}{RESET}  {TEXT}{describe(m, caps[m["name"]])}{RESET}{mark}')
        print()
        print(f'  {INFO}Ranks: {RANKS_SOURCE}. Image/OCR = the model can read images;{RESET}')
        print(f'  {INFO}the app does not send images to Ollama yet (OCR mode is planned).{RESET}')
        if missing:
            print()
            print(f'  {INFO}Also in the comparison, not installed yet:{RESET}')
            for name in missing:
                print(f'     {INFO}ollama pull {name}{RESET}')
        print()

        choice = safe_input(
            f'  {ACCENT}>> Enter choice [1-{len(models)}] or Enter for {default}: {RESET}',
            default='',
        ).strip()
        if choice == '':
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            return models[int(choice) - 1]['name']
        print(f'\n  {ERR}Invalid choice. Please enter 1-{len(models)} or press Enter.{RESET}')


def pick_time_limit() -> str:
    """Ask the maximum time per AI call.

    Returns '' for the default (15 min), so the command is unchanged,
    otherwise '--time-limit 30' / '60' / 'none'.
    """
    keys = list(TIME_CHOICES)
    print()
    print(f'  {TEXT}Time limit per AI call (large local models may need longer):{RESET}')
    for i, key in enumerate(keys, 1):
        print(f'    {ACCENT}{i}{RESET}  {TEXT}{TIME_LABELS[key]}{RESET}')
    while True:
        raw = (safe_input(f'  {ACCENT}>> Enter choice [1-{len(keys)}] '
                          f'or Enter for 15 minutes:{RESET} ') or '').strip()
        if raw == '':
            return ''
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            key = keys[int(raw) - 1]
            return '' if key == TIME_DEFAULT else f'--time-limit {key}'
        print(f'  {WARN}!  Please type a number from 1 to {len(keys)}.{RESET}')


def time_limit_flag(mode_flag: str) -> str:
    """--dry-run never calls the AI, so it is not asked."""
    if mode_flag == '--dry-run':
        return ''
    return pick_time_limit()


def pick_provider(mode_flag: str = '') -> str:
    is_sr = (mode_flag == '--mode sr')

    while True:
        print()
        section_header('SELECT  PROVIDER')
        print()

        BADGE_W = 12  # fixed visible width for the badge column, ASCII-only so it
                      # renders identically regardless of terminal locale/font
                      # (Unicode marks like the old checkmark are ambiguous-width
                      # and render as 2 columns in CJK-locale terminals, which
                      # was throwing the right-hand border out of alignment)

        for key, name, desc, flag in PROVIDERS:
            prov_id = flag.split()[-1] if flag else 'ollama'

            if is_sr and prov_id in BLOCKED_FOR_SR:
                badge = f'{ERR}{"x no vision":<{BADGE_W}}{RESET}'
                prow  = (f'  {FRAME}│{RESET}  {INFO}{key}{RESET}  '
                         f'{INFO}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{badge}{FRAME}│{RESET}')
            elif is_sr and prov_id in VISION_PROVIDERS:
                badge = f'{GOOD}{"+ vision":<{BADGE_W}}{RESET}'
                prow  = (f'  {FRAME}│{RESET}  {ACCENT}{key}{RESET}  '
                         f'{TEXT}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{badge}{FRAME}│{RESET}')
            else:
                prow  = (f'  {FRAME}│{RESET}  {ACCENT}{key}{RESET}  '
                         f'{TEXT}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{" " * BADGE_W}{FRAME}│{RESET}')
            print(prow)

        print()

        if is_sr:
            print(f'  {WARN}⚠  SR Pipeline requires a vision-capable provider.{RESET}')
            print(f'  {INFO}   Supported: {GOOD}qwen, openai, anthropic, groq{RESET}')
            print(f'  {INFO}   Blocked:   {ERR}ollama, deepseek{RESET}')
            print()

        choice = safe_input(
            f'  {ACCENT}>> Enter choice [1-6] or Enter for Ollama: {RESET}',
            default='',
        ).strip()

        if choice == '':
            prov_flag = '--provider ollama'
            prov_id   = 'ollama'
        else:
            matched = False
            for key, name, desc, flag in PROVIDERS:
                if choice == key:
                    prov_flag = flag
                    prov_id   = flag.split()[-1] if flag else 'ollama'
                    matched   = True
                    break
            if not matched:
                print(f'\n  {ERR}Invalid choice. Please enter 1-6 or press Enter.{RESET}')
                safe_input(f'  {INFO}Press Enter to try again...{RESET}')
                continue

        if is_sr and prov_id in BLOCKED_FOR_SR:
            print()
            print(f'  {ERR}x  "{prov_id}" does not support the vision API.{RESET}')
            print(f'  {INFO}  The SR pipeline extracts data from PDF images -{RESET}')
            print(f'  {INFO}  a vision-capable model is required.{RESET}')
            print()
            print(f'  {GOOD}  Supported vision providers:{RESET}')
            for p in sorted(VISION_PROVIDERS):
                print(f'     {GOOD}.{RESET}  {TEXT}{p}{RESET}')
            print()
            safe_input(f'  {INFO}Press Enter to choose again...{RESET}')
            continue

        if prov_id == 'ollama':
            model = pick_ollama_model()
            if model:
                return f'{prov_flag} --model {model}'
        return prov_flag



# -----------------------------------------------------------------------------
#  Input-folder guard
# -----------------------------------------------------------------------------
def _find_move_destination(mode: str) -> Path:
    for dest in _MOVE_DESTINATIONS:
        try:
            dest.mkdir(parents=True, exist_ok=True)
            return dest / f'AI_kcMedicalResearch_input_{mode}'
        except (PermissionError, OSError):
            continue
    fallback = Path.home() / f'AI_kcMedicalResearch_input_{mode}'
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def check_input_folder(mode: str) -> None:
    input_dir = BASE / "input" / mode
    if not input_dir.exists():
        return
    files = [f for f in input_dir.iterdir() if f.is_file()]
    if not files:
        return

    print()
    print(f'  {WARN}⚠  INPUT FOLDER CHECK{RESET}')
    print(f'  {INFO}Found {len(files)} existing file(s) in {ACCENT}input/{mode}/{RESET}')
    print()
    for f in files:
        print(f'     {SEP}.{RESET}  {TEXT}{f.name}{RESET}')
    print()
    print(f'  {TEXT}Were these files intentionally placed here for this run?{RESET}')

    ans = safe_input(
        f'  {ACCENT}>> Keep them? [Y = keep  /  N = move out]: {RESET}',
        default='N',
    ).strip().upper()

    if ans == 'Y':
        print(f'  {GOOD}✓  Files kept - they will be used in this session.{RESET}')
        return

    dest = _find_move_destination(mode)
    dest.mkdir(parents=True, exist_ok=True)
    moved, failed = [], []
    for f in files:
        try:
            shutil.move(str(f), str(dest / f.name))
            moved.append(f.name)
        except Exception as exc:
            failed.append(f'{f.name}  ({exc})')

    if moved:
        print(f'\n  {GOOD}✓  Moved {len(moved)} file(s) -> {ACCENT}{dest}{RESET}')
        for name in moved:
            print(f'     {SEP}.{RESET}  {TEXT}{name}{RESET}')
    if failed:
        print(f'\n  {ERR}x  Could not move:{RESET}')
        for name in failed:
            print(f'     {SEP}.{RESET}  {TEXT}{name}{RESET}')
    print()


# -----------------------------------------------------------------------------
#  Run helpers
# -----------------------------------------------------------------------------
def _run_cmd(cmd: list, label: str = '') -> None:
    flags_str = ' '.join(cmd[2:])
    display   = flags_str if len(flags_str) <= 33 else flags_str[:30] + '...'
    print()
    print(f'  {FRAME}╔══ Running ═════════════════════════════════════════════════════╗{RESET}')
    print(f'  {FRAME}║{RESET}  {ACCENT}python SOURCE_CODE/main.py {display:<33}{RESET}  {FRAME}║{RESET}')
    print(f'  {FRAME}╚══ Ctrl+C stops and returns to menu ════════════════════════════╝{RESET}')
    print()
    print(f'  {WARN}⏳ Starting up... this can take several seconds while dependencies load. Please wait...{RESET}')
    print()
    try:
        subprocess.run(cmd, cwd=str(BASE), stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print(f'\n  {WARN}Session stopped.  Returning to menu...{RESET}\n')


def run_custom() -> None:
    print()
    section_header('CUSTOM  FLAGS')
    print()
    print(f'  {INFO}Type flags, e.g.  {ACCENT}--mode writing --report --provider qwen{RESET}')
    print(f'  {INFO}Leave blank and press Enter to cancel.{RESET}')
    print()
    custom = safe_input(f'  {ACCENT}>> python SOURCE_CODE/main.py  {RESET}', default='')
    if not custom.strip():
        print(f'  {INFO}Cancelled.{RESET}')
        return
    cmd = [PYTHON, str(BASE / "SOURCE_CODE" / 'main.py')] + custom.split()
    _run_cmd(cmd, label='custom')


def coming_soon(label: str) -> None:
    print()
    print(f'  {WARN}{label}: coming soon.{RESET}')
    safe_input(f'  {INFO}Press Enter to return to menu...{RESET}')


def open_help() -> bool:
    """Open Readme/flashcard-help.html in the browser. True if opened."""
    if not HELP_FILE.is_file():
        print()
        print(f'  {ERR}Help page not found:{RESET}  {TEXT}{HELP_FILE}{RESET}')
        safe_input(f'  {INFO}Press Enter to return to menu...{RESET}')
        return False
    import webbrowser
    try:
        opened = webbrowser.open(HELP_FILE.resolve().as_uri())
    except Exception:
        opened = False
    if not opened:
        print()
        print(f'  {WARN}Could not open a browser. Open this file yourself:{RESET}')
        print(f'  {TEXT}{HELP_FILE}{RESET}')
        safe_input(f'  {INFO}Press Enter to return to menu...{RESET}')
        return False
    return True


API_KEY_ITEMS = [
    ('1', 'Qwen',      'DASHSCOPE_API_KEY'),
    ('2', 'Groq',      'GROQ_API_KEY'),
    ('3', 'DeepSeek',  'DEEPSEEK_API_KEY'),
    ('4', 'OpenAI',    'OPENAI_API_KEY'),
    ('5', 'Anthropic', 'ANTHROPIC_API_KEY'),
]


def _save_api_key(label: str, var: str) -> None:
    """Ask for one key (hidden) and save it to .env. Never prints the value."""
    print()
    try:
        # Plain prompt: getpass writes it straight to the console, where
        # colour codes may show up as raw characters on Windows.
        secret = getpass.getpass(f'  Paste the {label} key (hidden; Enter = keep current): ')
    except (KeyboardInterrupt, EOFError):
        print(f'\n  {INFO}Cancelled - nothing changed.{RESET}')
        return
    if not secret.strip():
        print(f'  {INFO}No change - kept the current {var}.{RESET}')
        return
    try:
        env_file.set_value(ENV_FILE, var, secret, template=ENV_TEMPLATE)
    except ValueError as e:
        print(f'  {ERR}{e} Nothing was saved.{RESET}')
        return
    except OSError as e:
        print(f'  {ERR}Could not save .env ({e.strerror or type(e).__name__}). Nothing was changed.{RESET}')
        return
    shown = env_file.mask(env_file.read_values(ENV_FILE).get(var, ''))
    print(f'  {ACCENT}Saved {var} ({shown}) to .env{RESET}')
    if os.environ.get(var):
        print(f'  {WARN}Note: {var} is also set in your system environment variables.{RESET}')
        print(f'  {WARN}That copy wins, so the .env value is ignored until you remove it.{RESET}')


def api_keys_menu() -> None:
    while True:
        clear()
        section_header('SETUP - API KEYS')
        values = env_file.read_values(ENV_FILE)
        print()
        for key, label, var in API_KEY_ITEMS:
            print(f'  {ACCENT}{key}{RESET}  {TEXT}{label:<10}{RESET} '
                  f'{INFO}{var:<18}{RESET}  {TEXT}{env_file.mask(values.get(var, ""))}{RESET}')
        print(f'  {ACCENT}0{RESET}  {TEXT}Back{RESET}')
        print()
        print(f'  {INFO}Keys are saved to .env in the project folder (never committed).{RESET}')
        print()
        choice = safe_input(f'  {ACCENT}>> Enter choice [0-5]: {RESET}', default='0')
        if choice in ('0', ''):
            return
        item = next((i for i in API_KEY_ITEMS if i[0] == choice), None)
        if item is None:
            print(f'\n  {ERR}Invalid choice - please enter 0-5.{RESET}')
        else:
            _save_api_key(item[1], item[2])
        safe_input(f'  {INFO}Press Enter to continue...{RESET}')


SETUP_ITEMS = [
    ('1', 'API keys',          'saved to .env, typed hidden'),
    ('2', 'Local AI (Ollama)', 'check install, default model, pull models'),
    ('3', 'Open Help',         'help page in your browser'),
]


def setup_menu() -> None:
    while True:
        clear()
        banner()
        section_header('SETUP')
        print()
        for key, label, desc in SETUP_ITEMS:
            print(f'  {ACCENT}{key}{RESET}  {TEXT}{label:<20}{RESET}  {INFO}{desc}{RESET}')
        print(f'  {ACCENT}0{RESET}  {TEXT}Back to main menu{RESET}')
        print()
        choice = safe_input(f'  {ACCENT}>> Enter choice [0-3]: {RESET}', default='0')
        if choice in ('0', ''):
            return
        if choice == '1':
            api_keys_menu()
        elif choice == '2':
            coming_soon('Local AI (Ollama)')
        elif choice == '3':
            open_help()
        else:
            print(f'\n  {ERR}Invalid choice - please enter 0-3.{RESET}')
            safe_input(f'  {INFO}Press Enter to try again...{RESET}')


# -----------------------------------------------------------------------------
#  Main loop
# -----------------------------------------------------------------------------
def main() -> None:
    while True:
        try:
            label, mode_flag, is_custom, is_help = pick_mode()
        except (KeyboardInterrupt, EOFError):
            clear()
            print(f'\n  {ACCENT}Goodbye!{RESET}\n')
            break

        try:
            if label is None and not is_custom and not is_help:
                clear()
                print(f'\n  {ACCENT}Goodbye!  👋{RESET}\n')
                break

            if is_help:
                open_help()
                continue

            if is_custom:
                run_custom()
                safe_input(f'  {INFO}Press Enter to return to menu...{RESET}')
                continue

            if mode_flag is None:          # 7 Data Analysis, 8 OCR
                coming_soon(label)
                continue

            if mode_flag == 'setup':       # 10 Setup
                setup_menu()
                continue

            input_mode = _MODE_INPUT_MAP.get(mode_flag)
            if input_mode:
                check_input_folder(input_mode)

            prov_flag = pick_provider(mode_flag)
            time_flag = time_limit_flag(mode_flag)

            flags = [f for f in [mode_flag, prov_flag, time_flag] if f]
            cmd   = [PYTHON, str(BASE / "SOURCE_CODE" / 'main.py')] + ' '.join(flags).split()
            _run_cmd(cmd, label=label or '')

            safe_input(f'  {INFO}Press Enter to return to menu...{RESET}')

        except (KeyboardInterrupt, EOFError):
            print(f'\n\n  {WARN}Session stopped.  Returning to menu...{RESET}\n')
            safe_input(f'  {INFO}Press Enter to continue...{RESET}')
            continue


if __name__ == '__main__':
    main()