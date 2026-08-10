# =============================================================================
#  launcher.py  繚  AI kcMedicalResearch  繚  v2.3.0
# =============================================================================

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

BASE   = Path(__file__).resolve().parent
PYTHON = sys.executable

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
    ('1', 'Coding',       '--mode coding'),
    ('2', 'Writing',      '--mode writing'),
    ('3', 'Appraisal',    '--mode appraisal'),
    ('4', 'Search',       '--mode search'),
    ('5', 'RCT Search',   '--mode rct_search'),
    ('6', 'SR Pipeline',  '--mode sr'),
    ('7', 'Dry Run',      '--dry-run'),
    ('8', 'Pipeline UI',  '--ui'),
]

PROVIDERS = [
    ('1', 'Ollama',    'local 繚 free 繚 default',  ''),
    ('2', 'Qwen',      'Alibaba 繚 recommended',   '--provider qwen'),
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


def hr(width: int = 57, char: str = '?') -> str:
    return f'  {FRAME}{char * width}{RESET}'


def section_header(title: str) -> None:
    pad   = 55 - len(title)
    left  = pad // 2
    right = pad - left
    print(f'  {FRAME}{"?" * left}{RESET}  {TITLE}{title}{RESET}  {FRAME}{"?" * right}{RESET}')


# -----------------------------------------------------------------------------
#  Banner  v2.3.0
# -----------------------------------------------------------------------------
def banner() -> None:
    W = _W

    print()
    print(f'  {FRAME}?????????????????????????????????????????????????????????RESET}')
    print(f'  {FRAME}?RESET}                                                       {FRAME}?RESET}')

    print(f'  {FRAME}?RESET}   {LOGO}???? ???????????RESET}{W(4)}'
          f'{LOGO_TXT}AI kcMedical Research{RESET}{W(9)}{FRAME}  ?RESET}')
    print(f'  {FRAME}?RESET}   {LOGO}????????????????{RESET}{W(4)}'
          f'{INFO}?????????????????????{RESET}{W(11)}{FRAME}?RESET}')
    print(f'  {FRAME}?RESET}   {LOGO}???????????RESET}{W(9)}'
          f'{ACCENT}Version  {RESET}{HILITE}2.3.0{RESET}{W(14)}{FRAME}    ?RESET}')
    print(f'  {FRAME}?RESET}   {LOGO}???????????RESET}{W(9)}'
          f'{ACCENT}Tests    {RESET}{GOOD}254 passed 繚 6 skipped{RESET}{W(1)}{FRAME}?RESET}')
    print(f'  {FRAME}?RESET}   {LOGO}???? ???????????RESET}{W(4)}'
          f'{ACCENT}Deploy   {RESET}{INFO}render.com / local{RESET}{W(5)}{FRAME}?RESET}')
    print(f'  {FRAME}?RESET}   {LOGO}???? ???????????RESET}{W(36)}{FRAME}?RESET}')

    print(f'  {FRAME}?RESET}                                                       {FRAME}?RESET}')

    tagline = 'Medical Research  繚  Review  繚  Analysis'
    pad = (53 - len(tagline)) // 2
    print(f'  {FRAME}?RESET}{W(pad)}  {SEP}{tagline}{RESET}{W(pad + 1)}{FRAME}?RESET}')

    print(f'  {FRAME}?RESET}                                                       {FRAME}?RESET}')
    print(f'  {FRAME}?????????????????????????????????????????????????????????ㄌRESET}')

    print(f'  {FRAME}?RESET}  {INFO}Modes  :{RESET}  '
          f'{TEXT}coding  writing  appraisal  search{RESET}{W(8)}{FRAME} ?RESET}')
    print(f'  {FRAME}?RESET}  {INFO}         {RESET}  '
          f'{TEXT}rct_search  sr  dry-run  ui{RESET}{W(12)}{FRAME}   ?RESET}')
    print(f'  {FRAME}?RESET}  {INFO}Providers:{RESET} '
          f'{ACCENT}ollama  qwen  groq  openai  anthropic{RESET}{W(3)}{FRAME}  ?RESET}')
    print(f'  {FRAME}?RESET}  {INFO}Help   :{RESET}  '
          f'{INFO}python SOURCE_CODE/main.py --help-guide{RESET}{W(10)}{FRAME}  ?RESET}')

    print(f'  {FRAME}?????????????????????????????????????????????????????????RESET}')

    theme_hint = (f'{INFO}  theme: {_BG}'
                  + (' 繚 set CLI_THEME=light to change' if _BG == 'dark' else
                     ' 繚 set CLI_THEME=dark to change')
                  + f'{RESET}')
    print(theme_hint)
    print()


# -----------------------------------------------------------------------------
#  Mode selection menu  v2.3.0
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

        # column inner width = 2 + 1 + 2 + 18 + 2 = 25
        CW = 25

        # -- top border --------------------------------------------------------
        print(f'  {FRAME}?"?" * CW}?洌"?" * CW}?RESET}')

        # -- data rows ---------------------------------------------------------
        for i in range(mid):
            l_key, l_lbl, _ = left_col[i]
            left_cell  = f'  {ACCENT}{l_key}{RESET}  {TEXT}{l_lbl:<18}{RESET}  '
            if i < len(right_col):
                r_key, r_lbl, _ = right_col[i]
                right_cell = f'  {ACCENT}{r_key}{RESET}  {TEXT}{r_lbl:<18}{RESET}  '
            else:
                right_cell = ' ' * CW
            print(f'  {FRAME}?RESET}{left_cell}{FRAME}?RESET}{right_cell}{FRAME}?RESET}')

        # -- divider before footer ---------------------------------------------
        print(f'  {FRAME}?"?" * CW}?慮"?" * CW}?廾RESET}')

        # -- footer row 1: 9 / H -----------------------------------------------
        print(f'  {FRAME}?RESET}  {ACCENT}9{RESET}  {TEXT}{"Custom flags":<18}{RESET}  '
              f'{FRAME}?RESET}  {ACCENT}H{RESET}  {TEXT}{"Help guide":<18}{RESET}  {FRAME}?RESET}')

        # -- footer row 2: X / blank -------------------------------------------
        print(f'  {FRAME}?RESET}  {ACCENT}X{RESET}  {TEXT}{"Exit":<18}{RESET}  '
              f'{FRAME}?RESET}{" " * CW}{FRAME}?RESET}')

        # -- bottom border -----------------------------------------------------
        print(f'  {FRAME}?"?" * CW}?揩"?" * CW}?RESET}')

        print()
        print(f'  {INFO}Tip: Press {ACCENT}Ctrl+C{RESET}{INFO} inside any session to stop and return here.{RESET}')
        print()

        choice = safe_input(
            f'  {ACCENT}?? Enter choice [1-9 / H / X]: {RESET}',
            default='X'
        ).upper()

        if choice in ('X', '0', ''):
            return None, None, False, False
        if choice == 'H':
            return None, None, False, True
        if choice == '9':
            return None, None, True, False
        for key, label, flag in MODES:
            if choice == key:
                return label, flag, False, False

        print(f'\n  {ERR}Invalid choice ??please enter 1-9, H, or X.{RESET}')
        safe_input(f'  {INFO}Press Enter to try again...{RESET}')


# -----------------------------------------------------------------------------
#  Provider selection menu
# -----------------------------------------------------------------------------
def pick_provider(mode_flag: str = '') -> str:
    is_sr = (mode_flag == '--mode sr')

    while True:
        print()
        section_header('SELECT  PROVIDER')
        print()

        for key, name, desc, flag in PROVIDERS:
            prov_id = flag.split()[-1] if flag else 'ollama'

            if is_sr and prov_id in BLOCKED_FOR_SR:
                badge = f'{ERR}??no vision{RESET}'
                prow  = (f'  {FRAME}?RESET}  {INFO}{key}{RESET}  '
                         f'{INFO}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{badge}  {FRAME}?RESET}')
            elif is_sr and prov_id in VISION_PROVIDERS:
                badge = f'{GOOD}??vision  {RESET}'
                prow  = (f'  {FRAME}?RESET}  {ACCENT}{key}{RESET}  '
                         f'{TEXT}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{badge}  {FRAME}?RESET}')
            else:
                prow  = (f'  {FRAME}?RESET}  {ACCENT}{key}{RESET}  '
                         f'{TEXT}{name:<12}{RESET}  {INFO}{desc:<26}{RESET}'
                         f'{" " * 12}{FRAME}?RESET}')
            print(prow)

        print()

        if is_sr:
            print(f'  {WARN}?? SR Pipeline requires a vision-capable provider.{RESET}')
            print(f'  {INFO}   Supported: {GOOD}qwen, openai, anthropic, groq{RESET}')
            print(f'  {INFO}   Blocked:   {ERR}ollama, deepseek{RESET}')
            print()

        choice = safe_input(
            f'  {ACCENT}?? Enter choice [1-6] or Enter for Ollama: {RESET}',
            default='',
        ).strip()

        if choice == '':
            prov_flag = ''
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
                safe_input(f'  {INFO}Press Enter to try again?州RESET}')
                continue

        if is_sr and prov_id in BLOCKED_FOR_SR:
            print()
            print(f'  {ERR}?? "{prov_id}" does not support the vision API.{RESET}')
            print(f'  {INFO}  The SR pipeline extracts data from PDF images ?RESET}')
            print(f'  {INFO}  a vision-capable model is required.{RESET}')
            print()
            print(f'  {GOOD}  Supported vision providers:{RESET}')
            for p in sorted(VISION_PROVIDERS):
                print(f'     {GOOD}?┐RESET}  {TEXT}{p}{RESET}')
            print()
            safe_input(f'  {INFO}Press Enter to choose again?州RESET}')
            continue

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
    input_dir = BASE / 'input' / mode
    if not input_dir.exists():
        return
    files = [f for f in input_dir.iterdir() if f.is_file()]
    if not files:
        return

    print()
    print(f'  {WARN}?? INPUT FOLDER CHECK{RESET}')
    print(f'  {INFO}Found {len(files)} existing file(s) in {ACCENT}input/{mode}/{RESET}')
    print()
    for f in files:
        print(f'     {SEP}繚{RESET}  {TEXT}{f.name}{RESET}')
    print()
    print(f'  {TEXT}Were these files intentionally placed here for this run?{RESET}')

    ans = safe_input(
        f'  {ACCENT}?? Keep them? [Y = keep  /  N = move out]: {RESET}',
        default='N',
    ).strip().upper()

    if ans == 'Y':
        print(f'  {GOOD}?? Files kept ??they will be used in this session.{RESET}')
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
        print(f'\n  {GOOD}?? Moved {len(moved)} file(s) ??{ACCENT}{dest}{RESET}')
        for name in moved:
            print(f'     {SEP}繚{RESET}  {TEXT}{name}{RESET}')
    if failed:
        print(f'\n  {ERR}?? Could not move:{RESET}')
        for name in failed:
            print(f'     {SEP}繚{RESET}  {TEXT}{name}{RESET}')
    print()


# -----------------------------------------------------------------------------
#  Run helpers
# -----------------------------------------------------------------------------
def _run_cmd(cmd: list, label: str = '') -> None:
    flags_str = ' '.join(cmd[2:])
    display   = flags_str if len(flags_str) <= 33 else flags_str[:30] + '...'
    print()
    print(f'  {FRAME}????Running ?????????????????????????????????????????????RESET}')
    print(f'  {FRAME}?RESET}  {ACCENT}python SOURCE_CODE/main.py {display:<33}{RESET}  {FRAME}?RESET}')
    print(f'  {FRAME}????Ctrl+C stops and returns to menu ????????????????????{RESET}')
    print()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    try:
        subprocess.run(cmd, cwd=str(BASE), creationflags=creationflags)
    except (KeyboardInterrupt, EOFError):
        print(f'\n  {WARN}Session stopped.  Returning to menu?州RESET}\n')


def run_custom() -> None:
    print()
    section_header('CUSTOM  FLAGS')
    print()
    print(f'  {INFO}Type flags, e.g.  {ACCENT}--mode writing --report --provider qwen{RESET}')
    print(f'  {INFO}Leave blank and press Enter to cancel.{RESET}')
    print()
    custom = safe_input(f'  {ACCENT}?? python SOURCE_CODE/main.py  {RESET}', default='')
    if not custom.strip():
        print(f'  {INFO}Cancelled.{RESET}')
        return
    cmd = [PYTHON, str(BASE / 'SOURCE_CODE' / 'main.py')] + custom.split()
    _run_cmd(cmd, label='custom')


def run_ui() -> None:
    cmd = [PYTHON, str(BASE / 'SOURCE_CODE' / 'main.py'), '--ui']
    print()
    print(f'  {FRAME}????Streamlit UI ????????????????????????????????????????{RESET}')
    print(f'  {FRAME}?RESET}  {GOOD}Opening :{RESET}  {ACCENT}http://localhost:8501{RESET}{"  " * 12}{FRAME}?RESET}')
    print(f'  {FRAME}?RESET}  {INFO}Stop    :{RESET}  {INFO}Close browser tab then press Ctrl+C{RESET}  {FRAME}?RESET}')
    print(f'  {FRAME}?????????????????????????????????????????????????????????RESET}')
    print()
    try:
        proc = subprocess.Popen(cmd, cwd=str(BASE))
        proc.wait()
    except (KeyboardInterrupt, EOFError):
        proc.terminate()
        print(f'\n  {WARN}UI stopped.  Returning to menu?州RESET}\n')


def show_help() -> None:
    help_file = BASE / 'SOURCE_CODE' / 'docs' / 'flashcard-help.html'
    opened = False
    if help_file.exists():
        try:
            import webbrowser
            webbrowser.open(str(help_file))
            opened = True
        except Exception:
            pass

    if not opened:
        clear()
        banner()
        section_header('QUICK  HELP')
        print()
        entries = [
            ('coding',     'AI-assisted manuscript coding'),
            ('writing',    'AI writing pipeline'),
            ('appraisal',  'Critical appraisal of studies'),
            ('search',     'Literature search'),
            ('rct_search', 'PubMed + Europe PMC RCT search'),
            ('sr',         '6-stage systematic review (vision)'),
            ('dry-run',    'Test without calling APIs'),
            ('--ui',       'Launch Streamlit web interface'),
        ]
        for mode, desc in entries:
            print(f'  {ACCENT}{mode:<14}{RESET}  {TEXT}{desc}{RESET}')
        print()
        print(f'  {INFO}Full guide:{RESET}  {ACCENT}python SOURCE_CODE/main.py --help-guide{RESET}')
        print()

    safe_input(f'  {INFO}Press Enter to return to menu?州RESET}')


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
                print(f'\n  {ACCENT}Goodbye!  ??{RESET}\n')
                break

            if is_help:
                show_help()
                continue

            if is_custom:
                run_custom()
                safe_input(f'  {INFO}Press Enter to return to menu?州RESET}')
                continue

            if mode_flag == '--ui':
                run_ui()
                safe_input(f'  {INFO}Press Enter to return to menu?州RESET}')
                continue

            input_mode = _MODE_INPUT_MAP.get(mode_flag)
            if input_mode:
                check_input_folder(input_mode)

            prov_flag = pick_provider(mode_flag)

            flags = [f for f in [mode_flag, prov_flag] if f]
            cmd   = [PYTHON, str(BASE / 'SOURCE_CODE' / 'main.py')] + ' '.join(flags).split()
            _run_cmd(cmd, label=label or '')

            safe_input(f'  {INFO}Press Enter to return to menu?州RESET}')

        except (KeyboardInterrupt, EOFError):
            print(f'\n\n  {WARN}Session stopped.  Returning to menu?州RESET}\n')
            safe_input(f'  {INFO}Press Enter to continue?州RESET}')
            continue


if __name__ == '__main__':
    main()
