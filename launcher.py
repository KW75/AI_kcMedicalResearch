import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
PYTHON = sys.executable
os.system('')

# ANSI colors
RESET =     '\033[0m'
FRAME =     '\033[94m'         # blue
LOGO =      '\033[38;5;51m'    # bright teal
LOGO_TXT =  '\033[32m'         # softer green
TEXT =      '\033[97m'         # bright white
DIM =       '\033[0;31;40m'    # red
ACCENT =    '\033[38;5;121m'   # mint green

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
    ('2', 'Qwen (Alibaba - recommended)', '--provider qwen'),
    ('3', 'Groq',                         '--provider groq'),
    ('4', 'DeepSeek',                     '--provider deepseek'),
    ('5', 'OpenAI',                        '--provider openai'),
    ('6', 'Anthropic',                     '--provider anthropic'),
]


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print()
    print(f'  {FRAME}+=========================================================+{RESET}')
    print(f'  {FRAME}|{RESET}                                                         {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##   ##    ####{RESET}                                      {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##  ##    ##  ##{RESET}                                     {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}## ##    ##{RESET}       {LOGO_TXT}AI kcMedical Research{RESET}              {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}####     ##{RESET}       {LOGO_TXT}Version 2.1.0{RESET}                      {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}## ##    ##{RESET}       {LOGO_TXT}291 tests passing{RESET}                  {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##  ##    ##  ##{RESET}                                     {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}    {LOGO}##   ##    ####{RESET}   {LOGO_TXT}AI Medical  | Research  | Review{RESET}   {FRAME}|{RESET}')
    print(f'  {FRAME}|{RESET}                                                         {FRAME}|{RESET}')
    print(f'  {FRAME}+=========================================================+{RESET}')
    print()
    print(f'  {DIM}Modes:{RESET}      {ACCENT}coding  writing  appraisal  search  rct_search  sr{RESET}')
    print(f'  {DIM}Providers:{RESET}  {ACCENT}ollama (default) qwen groq deepseek openai anthropic{RESET}')
    print()
    print(f'  {DIM}For help:{RESET}   {ACCENT}python src/main.py --help-guide{RESET}')
    print()

def pick_mode():
    while True:
        clear()
        banner()
        print(f'  {ACCENT}SELECT MODE{RESET}')
        print(f'  {DIM}-----------{RESET}')
        for key, label, _ in MODES:
            print(f'  {TEXT}{key}{RESET}  {TEXT}{label}{RESET}')
        print(f'  {TEXT}8{RESET}  {TEXT}Custom  (type your own flags){RESET}')
        print(f'  {TEXT}H{RESET}  {TEXT}Help guide{RESET}')
        print(f'  {TEXT}X{RESET}  {TEXT}Exit{RESET}')
        print()
        print(f'  {DIM}TIP:{RESET} {TEXT}Press Ctrl+C inside a session to stop and return here.{RESET}')
        print()
        try:
            choice = input(f'  {ACCENT}Enter choice [1-8 H X]: {RESET}').strip().upper()
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
        print(f'  {ACCENT}Invalid choice.{RESET}')
        input(f'  {DIM}Press Enter to try again...{RESET}')

def pick_provider():
    while True:
        print()
        print(f'  {ACCENT}SELECT PROVIDER{RESET}')
        print(f'  {DIM}---------------{RESET}')
        for key, label, _ in PROVIDERS:
            print(f'  {TEXT}{key}{RESET}  {TEXT}{label}{RESET}')
        print()
        try:
            choice = input(f'  {ACCENT}Enter choice [1-6] or Enter for Ollama: {RESET}').strip()
        except KeyboardInterrupt:
            return ''
        if choice == '':
            return ''
        for key, label, flag in PROVIDERS:
            if choice == key:
                return flag
        print(f'  {ACCENT}Invalid choice.{RESET}')

def run_custom():
    print()
    print(f'  {ACCENT}Custom flags{RESET}')
    print(f'  {TEXT}Type flags e.g. --mode writing --report --provider anthropic{RESET}')
    print(f'  {DIM}Leave blank and press Enter to return to menu.{RESET}')
    print()
    try:
        custom = input(f'  {ACCENT}> python src/main.py {RESET}').strip()
    except KeyboardInterrupt:
        return
    if not custom:
        return
    cmd = [PYTHON, str(BASE / 'src' / 'main.py')] + custom.split()
    print()
    try:
        subprocess.run(cmd, cwd=str(BASE))
    except KeyboardInterrupt:
        print(f'\n\n{ACCENT}Session stopped. Returning to menu...{RESET}\n')

def main():
    os.chdir(BASE)
    while True:
        label, mode_flag, is_custom, is_help = pick_mode()
        if label is None and not is_custom and not is_help:
            clear()
            print()
            print(f'  {ACCENT}Goodbye.{RESET}')
            print()
            break
        if is_help:
            try:
                subprocess.run([PYTHON, str(BASE / 'src' / 'main.py'), '--help-guide'], cwd=str(BASE))
            except KeyboardInterrupt:
                pass
            input(f'  {DIM}Press Enter to return to menu...{RESET}')
            continue
        if is_custom:
            run_custom()
            input(f'  {DIM}Press Enter to return to menu...{RESET}')
            continue
        prov_flag = pick_provider()
        flags = [f for f in [mode_flag, prov_flag] if f]
        cmd = [PYTHON, str(BASE / 'src' / 'main.py')] + ' '.join(flags).split()
        print()
        print(f'  {DIM}-------------------------------------------------------{RESET}')
        print(f'  {ACCENT}Running:{RESET} {TEXT}python src/main.py {" ".join(flags)}{RESET}')
        print(f'  {DIM}Ctrl+C stops the session and returns here.{RESET}')
        print(f'  {DIM}-------------------------------------------------------{RESET}')
        print()
        try:
            subprocess.run(cmd, cwd=str(BASE))
        except KeyboardInterrupt:
            print(f'\n\n{ACCENT}Session stopped. Returning to menu...{RESET}\n')
        input(f'  {DIM}Press Enter to return to menu...{RESET}')

if __name__ == '__main__':
    main()
