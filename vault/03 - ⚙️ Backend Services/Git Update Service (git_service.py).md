---
title: Git Update Service (git_service.py)
tags: [backend, git, updater, github]
related_files:
  - DUDC V3/server/git_service.py
  - Update_DUDC_V4.bat
---

# ⚙️ Git Update Service (`git_service.py`)

File: [`DUDC V3/server/git_service.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/git_service.py)

Enables one-click updating of the DUDC platform from GitHub directly through the web UI or via `Update_DUDC_V4.bat`.

---

## 🔍 Update Check Workflow (`check_git_updates`)
1. Locates `git.exe` in system PATH or standard Windows directories (`C:\Program Files\Git\cmd\git.exe`, `%LOCALAPPDATA%\Programs\Git\...`).
2. Runs `git fetch origin main` with an 8.0s timeout.
3. Compares local hash (`git rev-parse --short HEAD`) with remote hash (`git rev-parse --short origin/main`).
4. If hashes differ, extracts incoming commit logs:
   - Commit hash
   - Subject & message body
   - Author & relative date
5. Returns `update_available: true` and commit list to the client.

---

## 🚀 Conflict-Resistant Pull (`perform_git_update`)
Survey workstations often have untracked or local changes that would normally abort a standard `git pull`.
`perform_git_update()` uses an automatic recovery cascade:
1. Attempts `git pull origin main`.
2. If conflicts occur due to local changes:
   - Executes `git stash` to preserve modifications.
   - Retries `git pull origin main`.
3. If still blocked, executes `git checkout -- .` to restore tracked files and pulls cleanly.
4. Returns new HEAD commit information to confirm successful update.

