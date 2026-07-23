import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
PYTHON = sys.executable

MODES = [
    ('1', 'Coding',      '--mode coding'),
    ('2', 'Writing',     '--mode writing'),
    ('3', 'Appraisal',   '--mode appraisal'),
    ('4', 'Search',      '--mode search'),
    ('5', 'RCT Search',  '--mode rct_search'),
    ('6', 'SR Pipeline', '--mode sr'),
    ('7', 'Dry Run',     '--dry-run'),
]

PROVIDERS = [
    ('1', 'Ollama (local - default)', ''),
    ('2', 'Anthropic',  '--provider anthropic'),
    ('3', 'OpenAI',     '--provider openai'),
    ('4', 'DeepSeek',   '--provider deepseek'),
    ('5', 'Groq',       '--provider groq'),
]

def clear():
    os.system('cls')

def banner():
    print()
    print('  +=========================================================+')
    print('  |                                                         |')
    print('  |    ##   ##    ####                                      |')
    print('  |    ##  ##    ##  ##                                     |')
    print('  |    ## ##    ##       AI kcMedical Research              |')
    print('  |    ####     ##       Version 2.1.0                      |')
    print('  |    ## ##    ##       258 tests passing                  |')
    print('  |    ##  ##    ##  ##                                     |')
    print('  |    ##   ##    ####   AI Medical  | Research  | Review   |')
    print('  |                                                         |')
    print('  +=========================================================+')
    print()
    print('  Modes:  coding  writing  appraisal  search  rct_search  sr')
    print('  Providers: ollama (default)  openai  anthropic  deepseek  groq')
    print()
    print('  For help:  python src/main.py --help-guide')
    print()

def pick_mode():
    while True:
        clear()
        banner()
        print('  SELECT MODE')
        print('  -----------')
        for key, label, _ in MODES:
            print(f'  {key}  {label}')
        print('  8  Custom  (type your own flags)')
        print('  H  Help guide')
        print('  X  Exit')
        print()
        print('  TIP: Press Ctrl+C inside a session to stop and return here.')
        print()
        try:
            choice = input('  Enter choice [1-8 H X]: ').strip().upper()
        except KeyboardInterrupt:
            return None, None, False, False
        if choice == 'X':
            return None, None, False, False
        if choice == 'H':
            return None, None, False, True
        if choice == '8':
            return None, None, True, False
        for key, label, flag in MODES:
            if choice == key:
                return label, flag, False, False
        print('  Invalid choice.')
        input('  Press Enter to try again...')

def pick_provider():
    while True:
        print()
        print('  SELECT PROVIDER')
        print('  ---------------')
        for key, label, _ in PROVIDERS:
            print(f'  {key}  {label}')
        print()
        try:
            choice = input('  Enter choice [1-5] or Enter for Ollama: ').strip()
        except KeyboardInterrupt:
            return ''
        if choice == '':
            return ''
        for key, label, flag in PROVIDERS:
            if choice == key:
                return flag
        print('  Invalid choice.')

def run_custom():
    print()
    print('  Type flags e.g. --mode writing --report --provider anthropic')
    print('  Leave blank and press Enter to return to menu.')
    print()
    try:
        custom = input('  > python src/main.py ').strip()
    except KeyboardInterrupt:
        return
    if not custom:
        return
    cmd = [PYTHON, str(BASE / 'src' / 'main.py')] + custom.split()
    print()
    try:
        subprocess.run(cmd, cwd=str(BASE))
    except KeyboardInterrupt:
        print('\n\nSession stopped. Returning to menu...\n')

def main():
    os.chdir(BASE)
    while True:
        label, mode_flag, is_custom, is_help = pick_mode()
        if label is None and not is_custom and not is_help:
            clear()
            print()
            print('  Goodbye.')
            print()
            break
        if is_help:
            try:
                subprocess.run([PYTHON, str(BASE / 'src' / 'main.py'), '--help-guide'], cwd=str(BASE))
            except KeyboardInterrupt:
                pass
            input('  Press Enter to return to menu...')
            continue
        if is_custom:
            run_custom()
            input('  Press Enter to return to menu...')
            continue
        prov_flag = pick_provider()
        flags = [f for f in [mode_flag, prov_flag] if f]
        cmd = [PYTHON, str(BASE / 'src' / 'main.py')] + ' '.join(flags).split()
        print()
        print('  -------------------------------------------------------')
        print(f"  Running: python src/main.py {' '.join(flags)}")
        print('  Ctrl+C stops the session and returns here.')
        print('  -------------------------------------------------------')
        print()
        try:
            subprocess.run(cmd, cwd=str(BASE))
        except KeyboardInterrupt:
            print('\n\nSession stopped. Returning to menu...\n')
        input('  Press Enter to return to menu...')

if __name__ == '__main__':
    main()
