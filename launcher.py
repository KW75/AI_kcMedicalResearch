import subprocess
import sys
import os
import shutil
from pathlib import Path

BASE   = Path(__file__).resolve().parent
PYTHON = sys.executable
os.system('')

# ANSI colors
RESET    = '\033[0m'
FRAME    = '\033[94m'
LOGO     = '\033[38;5;51m'
LOGO_TXT = '\033[32m'
TEXT     = '\033[97m'
DIM      = '\033[0;31;40m'
ACCENT   = '\033[38;5;121m'

MODES = [
    ('1', 'Coding',      '--mode coding'),
    ('2', 'Writing',     '--mode writing'),
    ('3', 'Appraisal',   '--mode appraisal'),
    ('4', 'Search',      '--mode search'),
    ('5', 'RCT Search',  '--mode rct_search'),
    ('6', 'SR Pipeline', '--mode sr'),
    ('7', 'Dry Run',     '--dry-run'),
    ('8', 'Pipeline UI',   '--ui'),
]

PROVIDERS = [
    ('1', 'Ollama (local - default)',     ''),
    ('2', 'Qwen (Alibaba - recommended)', '--provider qwen'),
    ('3', 'Groq',                         '--provider groq'),
    ('4', 'DeepSeek',                     '--provider deepseek'),
    ('5', 'OpenAI',                       '--provider openai'),
    ('6', 'Anthropic',                    '--provider anthropic'),
]

# Vision providers for SR pipeline
VISION_PROVIDERS = ['qwen', 'openai', 'anthropic', 'groq']

# Fallback destinations for input file overflow (tried in order)
_MOVE_DESTINATIONS = [
    Path('C:/temp'),
    Path.home() / 'Downloads',
    Path.home() / 'Documents',
]


def clear():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except KeyboardInterrupt:
        pass


def safe_input(prompt, default=''):
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return default


def banner():
    print()
    print(f'  {FRAME}+=========================================================+{RESET}')
    print(f'  {FRAME}|{RESET}                                                         {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##   ##    ####{RESET}                                      {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##  ##    ##  ##{RESET}                                     {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}## ##    ##{RESET}       {LOGO_TXT}AI kcMedical Research{RESET}              {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}####     ##{RESET}       {LOGO_TXT}Version 2.2.0{RESET}                      {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}## ##    ##{RESET}       {LOGO_TXT}300 tests passing{RESET}                  {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##  ##    ##  ##{RESET}                                     {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##   ##    ####{RESET}   {LOGO_TXT}AI Medical  | Research  | Review{RESET}   {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}                                                         {FRAME}|{RESET}')
    print(f'  {FRAME}+=========================================================+{RESET}')
    print()
    print(f'  {DIM}Modes:{RESET}      {ACCENT}coding  writing  appraisal  search  rct_search  sr  ui{RESET}')
    print(f'  {DIM}Providers:{RESET}  {ACCENT}ollama (default)  qwen  groq  deepseek  openai  anthropic{RESET}')
    print()
    print(f'  {DIM}For help:{RESET}   {ACCENT}python src/main.py --help-guide{RESET}')
    print()


def _find_move_destination(mode: str) -> Path:
    """Return the first available destination folder for displaced input files."""
    for dest in _MOVE_DESTINATIONS:
        try:
            dest.mkdir(parents=True, exist_ok=True)
            return dest / f'AI_kcMedicalResearch_input_{mode}'
        except (PermissionError, OSError):
            continue
    # Last resort: user home
    fallback = Path.home() / f'AI_kcMedicalResearch_input_{mode}'
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def check_input_folder(mode: str) -> None:
    """
    Check if input/<mode>/ has files.
    If yes, ask the user whether they were intentionally placed there.
    If no (or no answer), move them to C:/temp or Downloads.
    """
    input_dir = BASE / 'input' / mode
    if not input_dir.exists():
        return

    files = [f for f in input_dir.iterdir() if f.is_file()]
    if not files:
        return

    print()
    print(f'  {ACCENT}[INPUT CHECK]{RESET} Found {len(files)} file(s) in input/{mode}/:')
    for f in files:
        print(f'    {DIM}•{RESET} {TEXT}{f.name}{RESET}')
    print()
    print(f'  {TEXT}Were these files intentionally placed here for this session?{RESET}')
    answer = safe_input(
        f'  {ACCENT}Keep them? [Y = yes, keep / N = move them out]: {RESET}',
        default='N'
    ).upper()

    if answer == 'Y':
        print(f'  {LOGO_TXT}Files kept in input/{mode}/. They will be used in this session.{RESET}')
        return

    # Move files out
    dest = _find_move_destination(mode)
    dest.mkdir(parents=True, exist_ok=True)
    moved = []
    failed = []
    for f in files:
        try:
            shutil.move(str(f), str(dest / f.name))
            moved.append(f.name)
        except Exception as exc:
            failed.append(f'{f.name} ({exc})')

    if moved:
        print(f'  {LOGO_TXT}Moved {len(moved)} file(s) to:{RESET}')
        print(f'    {ACCENT}{dest}{RESET}')
        for name in moved:
            print(f'    {DIM}•{RESET} {TEXT}{name}{RESET}')
    if failed:
        print(f'  {ACCENT}Could not move:{RESET}')
        for name in failed:
            print(f'    {DIM}•{RESET} {TEXT}{name}{RESET}')
    print()


def pick_mode():
    while True:
        clear()
        banner()
        print(f'  {ACCENT}SELECT MODE{RESET}')
        print(f'  {DIM}-----------{RESET}')
        for key, label, _ in MODES:
            print(f'  {TEXT}{key}{RESET}  {TEXT}{label}{RESET}')
        print(f'  {TEXT}9{RESET}  {TEXT}Custom  (type your own flags){RESET}')
        print(f'  {TEXT}H{RESET}  {TEXT}Help guide{RESET}')
        print(f'  {TEXT}X{RESET}  {TEXT}Exit{RESET}')
        print()
        print(f'  {DIM}TIP:{RESET} {TEXT}Press Ctrl+C inside a session to stop and return here.{RESET}')
        print()
        choice = safe_input(
            f'  {ACCENT}Enter choice [1-9 / H / X]: {RESET}',
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

        print(f'  {ACCENT}Invalid choice. Please enter 1-9, H, or X.{RESET}')
        safe_input(f'  {DIM}Press Enter to try again...{RESET}')


def pick_provider(mode_flag: str = ""):
    """Select provider with validation for SR mode."""
    while True:
        print()
        print(f'  {ACCENT}SELECT PROVIDER{RESET}')
        print(f'  {DIM}---------------{RESET}')
        for key, label, _ in PROVIDERS:
            print(f'  {TEXT}{key}{RESET}  {TEXT}{label}{RESET}')
        print()
        
        # Show warning for SR mode
        if mode_flag == '--mode sr':
            print(f'  {ACCENT}⚠️  SR Pipeline requires a vision-capable provider{RESET}')
            print(f'  {DIM}   Supported: qwen, openai, anthropic, groq{RESET}')
            print(f'  {DIM}   NOT supported: ollama, deepseek{RESET}')
            print()
        
        choice = safe_input(
            f'  {ACCENT}Enter choice [1-6] or Enter for Ollama: {RESET}',
            default=''
        )
        
        if choice == '':
            selected_provider = ''
        else:
            found = False
            for key, label, flag in PROVIDERS:
                if choice == key:
                    selected_provider = flag
                    found = True
                    break
            if not found:
                print(f'  {ACCENT}Invalid choice.{RESET}')
                continue
        
        # --- Validate provider for SR mode ---
        if mode_flag == '--mode sr':
            # Get the provider name from the flag
            provider_name = selected_provider.split()[-1] if selected_provider and ' ' in selected_provider else selected_provider
            if not provider_name:
                provider_name = 'ollama'  # default
            
            if provider_name not in VISION_PROVIDERS:
                print()
                print(f'  {ACCENT}❌ ERROR: "{provider_name}" does NOT support vision API{RESET}')
                print(f'  {DIM}The SR pipeline requires vision-based extraction (images of PDF pages).{RESET}')
                print()
                print(f'  {TEXT}Supported providers for SR mode:{RESET}')
                print(f'    • {ACCENT}qwen{RESET}     (recommended) - Qwen vision model')
                print(f'    • {ACCENT}openai{RESET}   - GPT-4 vision')
                print(f'    • {ACCENT}anthropic{RESET} - Claude vision')
                print(f'    • {ACCENT}groq{RESET}     - Vision models available')
                print()
                print(f'  {DIM}Please select a supported provider.{RESET}')
                input(f'  {DIM}Press Enter to try again...{RESET}')
                continue
        
        return selected_provider


def run_custom():
    print()
    print(f'  {ACCENT}Custom flags{RESET}')
    print(f'  {TEXT}Type flags e.g. --mode writing --report --provider qwen{RESET}')
    print(f'  {DIM}Leave blank and press Enter to return to menu.{RESET}')
    print()
    custom = safe_input(f'  {ACCENT}> python src/main.py {RESET}', default='')
    if not custom:
        return
    cmd = [PYTHON, str(BASE / 'src' / 'main.py')] + custom.split()
    print()
    try:
        subprocess.run(cmd, cwd=str(BASE))
    except (KeyboardInterrupt, EOFError):
        print(f'\n\n{ACCENT}Session stopped. Returning to menu...{RESET}\n')


def run_ui():
    cmd = [PYTHON, str(BASE / 'src' / 'main.py'), '--ui']
    print()
    print(f'  {DIM}-------------------------------------------------------{RESET}')
    print(f'  {ACCENT}Launching UI:{RESET} {TEXT}http://localhost:8501{RESET}')
    print(f'  {DIM}Close the browser tab and press Ctrl+C here to stop.{RESET}')
    print(f'  {DIM}-------------------------------------------------------{RESET}')
    print()
    try:
        proc = subprocess.Popen(cmd, cwd=str(BASE))
        proc.wait()
    except (KeyboardInterrupt, EOFError):
        proc.terminate()
        print(f'\n\n{ACCENT}UI stopped. Returning to menu...{RESET}\n')


# Map mode flags to input folder names
_MODE_INPUT_MAP = {
    '--mode coding':     'coding',
    '--mode writing':    'writing',
    '--mode appraisal':  'appraisal',
    '--mode search':     'search',
    '--mode rct_search': 'rct_search',
    '--mode sr':         'sr',
}


def main():
    _cflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0

    while True:
        try:
            label, mode_flag, is_custom, is_help = pick_mode()
        except (KeyboardInterrupt, EOFError):
            clear()
            print(f'\n  {ACCENT}Goodbye!{RESET}\n')
            break

        try:
            if is_help:
                import webbrowser
                webbrowser.open(str(BASE / 'docs' / 'flashcard-help.html'))
                safe_input(f'  {DIM}Press Enter to return to menu...{RESET}')
                continue

            if label is None and not is_custom:
                clear()
                print(f'\n  {ACCENT}Goodbye!{RESET}\n')
                break

            if is_custom:
                run_custom()
                safe_input(f'  {DIM}Press Enter to return to menu...{RESET}')
                continue

            if mode_flag == '--ui':
                run_ui()
                safe_input(f'  {DIM}Press Enter to return to menu...{RESET}')
                continue

            # --- Input folder check before provider selection ---
            input_mode = _MODE_INPUT_MAP.get(mode_flag)
            if input_mode:
                check_input_folder(input_mode)

            prov_flag = pick_provider(mode_flag)
            flags = [f for f in [mode_flag, prov_flag] if f]
            cmd   = [PYTHON, str(BASE / 'src' / 'main.py')] + ' '.join(flags).split()

            print()
            print(f'  {DIM}-------------------------------------------------------{RESET}')
            print(f'  {ACCENT}Running:{RESET} {TEXT}python src/main.py {" ".join(flags)}{RESET}')
            print(f'  {DIM}Ctrl+C stops the session and returns here.{RESET}')
            print(f'  {DIM}-------------------------------------------------------{RESET}')
            print()

            try:
                subprocess.run(cmd, cwd=str(BASE), creationflags=_cflags)
            except (KeyboardInterrupt, EOFError):
                print(f'\n\n{ACCENT}Session stopped. Returning to menu...{RESET}\n')

            safe_input(f'  {DIM}Press Enter to return to menu...{RESET}')

        except (KeyboardInterrupt, EOFError):
            print(f'\n\n{ACCENT}Session stopped. Returning to menu...{RESET}\n')
            safe_input(f'  {DIM}Press Enter to return to menu...{RESET}')
            continue


if __name__ == '__main__':
    main()