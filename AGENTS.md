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
- Keep website assets local unless the user explicitly asks for external assets.
