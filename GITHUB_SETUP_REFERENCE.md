# GitHub Setup Reference

## Project

```text
D:\ai-automation-tool
```

## Scope of this reference

This reference summarizes the steps completed after the previous Ollama handoff, up to creation of the empty GitHub repository.

Current stop point:

```text
Local Git repository exists.
First local commit exists.
Branch is named main.
Empty GitHub repository exists.
Remote has not been added yet.
Code has not been pushed yet.
```

## Important user rule

Proceed one step at a time.

Do not continue to the next step until the user says:

```text
OK
```

---

# Steps completed

## 1. Reopened VS Code and reactivated the virtual environment

When VS Code was reopened, the terminal no longer showed:

```text
(.venv)
```

This is normal.

Command used:

```powershell
cd D:\ai-automation-tool
.\.venv\Scripts\Activate.ps1
```

Function:

- Moves into the project folder.
- Reactivates the Python virtual environment.
- Expected prompt:

```text
(.venv) PS D:\ai-automation-tool>
```

Note:

```text
(.venv)
```

means the Python virtual environment is active.

---

## 2. Verified previous handoff files

Command used:

```powershell
dir HANDOFF.*
```

Function:

- Checks that the previous handoff files exist.

Expected files:

```text
HANDOFF.md
HANDOFF.html
```

Optional command:

```powershell
Start-Process .\HANDOFF.html
```

Function:

- Opens the HTML handoff file in the browser.

---

## 3. Checked Git installation

Command used:

```powershell
git --version
```

Function:

- Confirms Git is installed and available in PowerShell.

Expected output example:

```text
git version 2.x.x
```

---

## 4. Checked Git identity settings

Commands used:

```powershell
git config --global user.name
git config --global user.email
```

Function:

- Checks the name and email Git will attach to commits.

Initial result:

- Values were blank.
- Then placeholder values were accidentally saved.
- They were later corrected.

---

## 5. Set Git name and email

Commands used:

```powershell
git config --global user.name "Your GitHub Username Or Name"
git config --global user.email "your-github-email@example.com"
```

Function:

- Sets the global Git identity.
- This identity is used when making commits.

Important:

- `user.name` is not the repository name.
- `user.name` is the person/username making the commit.
- The repository name remains:

```text
ai-automation-tool
```

Verification commands:

```powershell
git config --global user.name
git config --global user.email
```

Function:

- Confirms the correct name and email are saved.

---

## 6. Initialized Git locally

Command used:

```powershell
git init
```

Function:

- Creates a local Git repository inside:

```text
D:\ai-automation-tool
```

This creates a hidden folder:

```text
.git/
```

---

## 7. Checked Git status before committing

Command used:

```powershell
git status
```

Short version used:

```powershell
git status --short
```

Function:

- Shows which files Git sees.
- Helps confirm private files are ignored.

Important check:

These should not appear:

```text
.env
.venv/
```

This is safe to appear:

```text
.env.example
```

Reason:

- `.env` contains local/private settings and is ignored.
- `.venv/` contains the Python virtual environment and is ignored.
- `.env.example` is a safe template and should be committed.

Important note:

```text
.env
.venv/
```

are file/folder names to check inside `git status`.

They are not commands to run.

---

## 8. Added project files to Git

Command used:

```powershell
git add .
```

Function:

- Stages all non-ignored project files for the first commit.

Then checked again:

```powershell
git status --short
```

Function:

- Confirms which files are staged.
- Confirms `.env` and `.venv/` are not staged.

---

## 9. Made the first local commit

Command used:

```powershell
git commit -m "Initial local Ollama AI automation tool"
```

Function:

- Saves the current project state into Git history.
- Creates the first local commit.

Then checked status:

```powershell
git status
```

Expected result:

```text
nothing to commit, working tree clean
```

Function:

- Confirms all staged files were committed.
- Confirms there are no uncommitted changes.

---

## 10. Renamed branch to main

Command used:

```powershell
git branch -M main
```

Function:

- Renames the current branch to:

```text
main
```

Verification command:

```powershell
git branch --show-current
```

Expected output:

```text
main
```

Commit verification command:

```powershell
git log --oneline -1
```

Expected result includes:

```text
Initial local Ollama AI automation tool
```

Function:

- Shows the most recent commit.

---

## 11. Created empty GitHub repository

GitHub page used:

```text
https://github.com/new
```

Repository settings used:

```text
Repository name: ai-automation-tool
Visibility: Private
```

Important:

The following boxes were not checked:

```text
Add a README file
Add .gitignore
Choose a license
```

Reason:

- The local project already has files.
- The local project already has `.gitignore`.
- The first push should go from local project to empty GitHub repo.

---

# Current state

Local project:

```text
D:\ai-automation-tool
```

Local Git status:

```text
Repository initialized.
First commit completed.
Branch renamed to main.
Working tree was clean after commit.
```

GitHub status:

```text
Empty private repository created.
Remote not connected yet.
No push completed yet.
```

Not done yet:

```text
git remote add origin ...
git push -u origin main
```

---

# Next recommended step

The next step should be:

```text
Add GitHub remote and push local main branch.
```

Example future commands:

```powershell
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/ai-automation-tool.git
git remote -v
git push -u origin main
```

Do not run these until the user says OK and confirms the correct GitHub repository URL.

---

# Safety notes

Do not commit:

```text
.env
.venv/
```

Safe to commit:

```text
.env.example
.gitignore
requirements.txt
src/
docs/
ai/
reports/
tests/
HANDOFF.md
HANDOFF.html
GITHUB_SETUP_REFERENCE.md
GITHUB_SETUP_REFERENCE.html
```

Continue one step at a time.
