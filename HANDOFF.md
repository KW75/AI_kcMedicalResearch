AI kcMedicalResearch — Project Handoff Document
Version 2.2.0 | Date: 2026-07-26

Project Overview:

AI kcMedicalResearch is a Python-based medical research assistant with six AI-powered modes (Coding, Writing, Appraisal, RCT Search, Search, Systematic Review) accessible via both a terminal launcher and a Streamlit web UI. The project runs locally using Ollama or cloud providers (OpenAI, Anthropic, DeepSeek, Groq, Qwen).

Repository and File Structure:

The GitHub repository is at https://github.com/KW75/AI_kcMedicalResearch (private). The latest commit is 350cc15 on branch main. The key files and folders are as follows — src/main.py is the core application entry point, src/ui/app.py is the Streamlit UI, launcher.py is the terminal menu launcher, requirements.txt lists all Python dependencies, AI_kcMedicalResearch_setup.bat is the first-run setup script, AI_kcMedicalResearch_run.bat launches the app, .streamlit/config.toml sets the UI font size, .env holds API keys (not in repo), and assets/ contains the six mode icons.

Current Project State:

All 300 unit tests pass. The following features are confirmed working as of this handoff.

The Streamlit UI launches correctly via python src/main.py --ui or by double-clicking AI_kcMedicalResearch_run.bat. Six mode cards display on the home page with correct icons (transparent PNG, 96×96, RGBA preserved), coloured borders, file counts, and Input/Output/Navigate/Exit buttons. The two info banners at the top of the home page inform users that uploaded files are automatically transferred to their respective input folders and that outputs are available for download. Home and Exit navigation buttons are left-aligned side by side on all mode pages. File uploads auto-refresh the file list without manual intervention. Font size is increased via MutationObserver JavaScript injection and .streamlit/config.toml with baseFontSize = 18. All six input() calls in src/main.py are wrapped with EOFError/KeyboardInterrupt handlers so the UI terminal launch never crashes on missing stdin. The launcher (launcher.py) handles Ctrl+C gracefully at all menu levels, returning to the menu instead of showing "Terminate batch job".

Completed Steps This Session (Steps 90b–92b):

Step 90b wrapped all input() calls in src/main.py with EOFError and KeyboardInterrupt handlers, covering choose_role() at line 658, delete confirmation at line 705, rename at line 743, revision task at line 1008, research topic at line 1148, PICO confirmation at line 1295, search type at line 1510, topic multiline input at line 1522, and the main task prompt at line 1703. Step 91 fixed icon display by replacing the white-background compositing in _icon_b64() with transparency-preserving RGBA conversion, increased font size via MutationObserver and config.toml, added blue and green info banners to the home page, and implemented auto-refresh after file upload on both home and mode pages. Step 91b and 91c placed Home and Exit buttons side by side, left-aligned, using a [2, 2, 8] column layout on mode pages. Step 92 updated AI_kcMedicalResearch_setup.bat to six steps including automatic .streamlit/config.toml creation. Step 92b added .gitattributes to prevent CRLF warnings on .toml files.

Known Issues and Pending Items:

The baseFontSize = 18 in config.toml is read correctly by Streamlit 1.60 but has no visible effect on button text — the MutationObserver workaround in src/ui/app.py handles this instead. The with nav_r: pass block on the mode page is a placeholder retained for future use. Tesseract OCR (pytesseract) and Poppler (pdf2image) require separate non-Python installers on any new machine — they are not installed by setup.bat. The output/ folder is excluded from the laptop zip to keep file size small — users must re-generate outputs on the new machine.

Laptop Duplication Workflow:

On the source PC, run the following to create the transfer zip:

$stage = "D:\AI_kcMedicalResearch_stage"
$zip   = "D:\AI_kcMedicalResearch_laptop.zip"
robocopy "D:\AI_kcMedicalResearch" $stage /E `
    /XD ".venv" "__pycache__" ".git" "output" `
    /XF "*.pyc" "*.log" "*.zip" /NFL /NDL /NJH /NJS
Compress-Archive -Path "$stage\*" -DestinationPath $zip -Force
Remove-Item $stage -Recurse -Force

On the laptop, after unzipping to C:\AI_kcMedicalResearch or D:\AI_kcMedicalResearch, complete the following checklist in order. Install Python 3.11 or 3.12 with "Add Python to PATH" ticked. Copy .env into the project root. Double-click AI_kcMedicalResearch_setup.bat and wait for "Setup complete". Install Ollama from https://ollama.com if using local models, then run ollama pull llama3. Double-click AI_kcMedicalResearch_run.bat. Open http://localhost:8501 and press Ctrl+Shift+R for a hard refresh. If pytesseract is needed install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki. If pdf2image fails install Poppler from https://github.com/oschwartz10612/poppler-windows/releases and add its bin/ folder to PATH.

Key Technical Decisions Made This Session:

The _icon_b64() function now uses .convert("RGBA") without compositing onto any background colour, preserving full transparency so icons float naturally on card backgrounds. The MutationObserver approach was chosen over CSS !important rules because Streamlit's React components set inline styles after render that override stylesheet rules. The config.toml baseFontSize is retained for future Streamlit versions that may honour it more reliably. All input() calls use nested try/except rather than a global wrapper so each call site can provide a context-appropriate default value. The laptop zip excludes .venv and .git — .venv because virtual environments contain absolute paths that break when moved between machines, and .git because the laptop copy is a deployment, not a development clone.

Dependencies (requirements.txt):

The full list is chromadb, pypdf, python-dotenv, requests, pymupdf, python-docx, pytest, pytest-cov, anyio, pandas, numpy, scipy, matplotlib, pyyaml, pytesseract, pdf2image, pillow, streamlit, and anthropic. Confirmed installed versions are pillow==12.3.0 and streamlit==1.60.0.

Quick Reference — Common Commands:

# Run all tests
.venv\Scripts\python.exe -m pytest --tb=short -q

# Launch terminal menu
python launcher.py

# Launch Streamlit UI
.venv\Scripts\python.exe src\main.py --ui

# Check Streamlit version
.venv\Scripts\python.exe -c "import streamlit; print(streamlit.__version__)"

# Check icon files
Get-ChildItem D:\AI_kcMedicalResearch\assets\icon_*.png

# Verify config.toml
Get-Content D:\AI_kcMedicalResearch\.streamlit\config.toml

# Commit and push
git add -A
git commit -m "message"
git push

Next Session Starting Points:

The following items are ready to be tackled in the next session. End-to-end testing of all six modes via UI terminal launch is the highest priority — confirm each mode opens a new terminal, runs without EOFError, saves output, and the output appears in the Output folder browser. The docs/flashcard-help.html file needs updating to reflect the new UI layout, renamed folders, and --ui flag. The with nav_r: pass placeholder on the mode page could be used for a future "Run" shortcut button. Icon replacement — the current icons are dark artwork on transparent backgrounds; if lighter or more colourful icons become available, simply drop them into assets/ with the same filenames and the UI picks them up automatically with no code changes needed.