# Agent Instructions

Read `STEERING.md` before making project or Git workflow changes.

## Git Safety

- Treat `credentials.json`, `token.json`, `.env*`, private keys, OAuth client secrets, and service account files as local-only secrets.
- Never stage or commit those files.
- Preserve `.gitignore` and `.githooks/pre-commit`; they are intentional safety guardrails.
- This repo should use the tracked hooks directory:

```bash
git config core.hooksPath .githooks
```

- Before every commit, run:

```bash
git status --short --ignored
git diff --cached --name-only
```

- Prefer explicit staging, for example `git add index.html README.md`, over `git add .`.
- Do not rewrite history, reset work, remove remotes, or bypass hooks unless the user explicitly asks for it.
- Before pushing, verify the remote with `git remote -v`.

## Project Shape

- `index.html` is the website source of truth.
- `create_google_form.py` creates Google Forms and writes links to `form_links.json`; it must not regenerate or overwrite `index.html`.
- Run Python scripts with the local Conda environment Python:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" create_google_form.py
```

- Avoid `py -3` unless Python Launcher is configured. Prefer direct environment Python over `conda run -n expenses python ...` because `conda run` has hit Windows Unicode output errors.
- Keep website assets local unless the user explicitly asks for external assets.

## Google Forms Cleanup Safety

- `cleanup_google_forms.py` is the only approved path for cleaning up obsolete RSVP forms.
- Treat Google Drive operations as destructive: run read-only discovery or dry-run verification first and review the output before any trash operation.
- Never permanently delete Google Drive resources. Cleanup may only move explicitly allowlisted obsolete wedding forms to trash.
- Never modify or trash active form IDs listed in `form_links.json`.
- Do not add an ID to the cleanup allowlist unless it has been identified as a project-created obsolete wedding form and its internal Google Forms title has been verified.
- Preserve the restricted Google Drive OAuth scope (`drive.file`); do not broaden access to the user's Google Drive.
