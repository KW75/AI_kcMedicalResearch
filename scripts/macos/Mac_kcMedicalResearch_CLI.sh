#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_CLI.sh
#  v2.5.0  |  Menu-driven CLI launcher (scripts/launcher.py)
#
#  Run with:  bash scripts/macos/Mac_kcMedicalResearch_CLI.sh
#  (Running via bash avoids zsh choking on '#' comment lines.)
# =============================================================================
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

PY="$PROJECT_DIR/.venv/bin/python"
LAUNCHER="$PROJECT_DIR/scripts/launcher.py"

echo ""
echo "  ============================================================"
echo "   AI kcMedical Research  |  CLI Launcher  |  v2.5.0"
echo "   Project: $PROJECT_DIR"
echo "  ============================================================"
echo ""

show_install_message() {
    echo ""
    echo "  ------------------------------------------------------------"
    echo "   This app needs Python 3.11."
    echo ""
    echo "   1. Download it here:"
    echo "      https://www.python.org/downloads/release/python-3119/"
    echo "      (choose \"macOS 64-bit universal2 installer\")"
    echo ""
    echo "   2. Open the downloaded file and click through Install."
    echo ""
    echo "   3. Start this app again."
    echo "  ------------------------------------------------------------"
    echo ""
    read -r -p "  Press Enter to close..."
}

# --- MOVED FOLDER? -----------------------------------------------------------
# pip and the other console scripts in .venv store the absolute path of the
# folder the venv was built in. After the app folder is moved or renamed they
# fail. pyvenv.cfg's "command" line records where the venv was built; if it
# is not this folder, offer a rebuild. The old tree is kept as .venv.old
# until the new one installs.
REBUILT=""

restore_old_venv() {
    if [ -n "$REBUILT" ]; then
        rm -rf "$PROJECT_DIR/.venv"
        mv "$PROJECT_DIR/.venv.old" "$PROJECT_DIR/.venv" \
            && echo "  Your previous app environment was restored."
    fi
}

CFG="$PROJECT_DIR/.venv/pyvenv.cfg"
if [ -f "$CFG" ]; then
    VENV_CMD="$(grep -i '^command *=' "$CFG" | head -n 1)"
    if [ -n "$VENV_CMD" ]; then
        case "$VENV_CMD" in
            *"$PROJECT_DIR/.venv"*) ;;
            *)
                echo "  ------------------------------------------------------------"
                echo "   This app folder was moved since setup."
                echo "   The app environment was built in: ${VENV_CMD##*-m venv }"
                echo "   Tools such as pip and pytest will not start until it is rebuilt."
                echo "  ------------------------------------------------------------"
                if [ -e "$PROJECT_DIR/.venv.old" ]; then
                    echo "  A previous rebuild left the folder .venv.old behind."
                    echo "  Delete .venv.old, or rename it back to .venv, then start again."
                    read -r -p "  Press Enter to close..."
                    exit 1
                fi
                ANS=""
                read -r -p "  Rebuild the app environment now? [Y/n] " ANS
                case "$ANS" in
                    [nN]|[nN][oO]) ;;
                    *)
                        mv "$PROJECT_DIR/.venv" "$PROJECT_DIR/.venv.old" || {
                            echo "  [ERROR] Could not rename .venv. Close other windows using it, then try again."
                            read -r -p "  Press Enter to close..."
                            exit 1
                        }
                        REBUILT=1
                        ;;
                esac
                ;;
        esac
    fi
fi

# --- CHECK / CREATE .venv ----------------------------------------------------
if [ ! -x "$PY" ]; then
    # Find a genuine python.org / non-conda Python 3.11.
    PYBIN=""
    for candidate in \
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
        /usr/local/bin/python3.11 \
        /opt/homebrew/bin/python3.11 \
        python3.11; do
        found="$(command -v "$candidate" 2>/dev/null || true)"
        [ -z "$found" ] && continue
        case "$found" in *conda*|*anaconda*|*miniconda*) continue ;; esac
        if "$found" -c 'import sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) else 1)' 2>/dev/null; then
            PYBIN="$found"; break
        fi
    done

    if [ -z "$PYBIN" ]; then
        restore_old_venv
        show_install_message
        exit 1
    fi

    echo "  Using Python: $PYBIN"
    echo ""
    if ! "$PYBIN" -m venv .venv; then
        echo "  [ERROR] Could not create the app environment."
        restore_old_venv
        read -r -p "  Press Enter to close..."
        exit 1
    fi

    echo "  Setting up, please wait - this can take a few minutes."
    echo "  The screen may look frozen. That is normal - do NOT close this window."
    echo ""
    "$PY" -m pip install --upgrade pip
    if ! "$PY" -m pip install -r requirements-local.txt; then
        echo ""
        echo "  [ERROR] Could not install the app's components."
        restore_old_venv
        show_install_message
        exit 1
    fi
    if [ -n "$REBUILT" ]; then
        rm -rf "$PROJECT_DIR/.venv.old"
        echo "  Old app environment removed."
    fi
    echo ""
    echo "  Setup complete."
    echo ""
fi

# --- WARN IF .env MISSING ----------------------------------------------------
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "  ------------------------------------------------------------"
    echo "   NOTE: no .env file found."
    echo "   To use a cloud provider, copy .env.example to .env and add"
    echo "   your API key. To use the free local option, set up Ollama"
    echo "   (see README Step 2)."
    echo "  ------------------------------------------------------------"
    echo ""
fi

# --- LAUNCH ------------------------------------------------------------------
"$PY" "$LAUNCHER" "$@"
RC=$?
echo ""
[ "$RC" -ne 0 ] && echo "  App exited with code $RC." || echo "  Session ended."
exit "$RC"
