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

## Website Editing Safety

- Treat website copy, translation strings, form links, form behavior, routes, and section order as locked unless the user explicitly requests changes to them.
- For a visual-only request, change CSS and decorative markup only. Before finishing, review the diff for unintended edits to translation values, `href` values, IDs used by JavaScript, or form-related content.
- The three language versions are not always word-for-word equivalents. Before removing a repeated heading or label, check whether it remains meaningful in English, Italian, and Ukrainian; use language-specific visibility when needed.
- Keep decorative asset placement tied to text alignment: ornaments above left-aligned headings should be left-aligned, while centered headings should have centered ornaments. Re-check this at desktop and mobile breakpoints.
- When adjusting typography, distinguish small section labels (`.kicker`) from primary section titles (`h2`) and body text; modify only the requested level.
- Prefer a meaningful document order that reads naturally on mobile before relying on desktop grid placement. Supporting images should follow the explanatory text they illustrate.
- Treat personal photographs as meaningful content images with localized `alt` text when the site changes language; reserve empty `alt` text and `aria-hidden="true"` for purely decorative imagery.
- After visual changes, preview each language at desktop and mobile widths, especially the invitation, location, weekend, travel/stay, attire, and RSVP sections.
- Reuse assets from `decorative-assets/` and mark decorative images with empty `alt` text and `aria-hidden="true"`.
- Before staging a website update, list all new assets referenced by `index.html` and explicitly stage only those files; leave moodboards, source references, and unused experiments untracked unless they are intentionally part of the published site.

## Google Forms Cleanup Safety

- `cleanup_google_forms.py` is the only approved path for cleaning up obsolete RSVP forms.
- Treat Google Drive operations as destructive: run read-only discovery or dry-run verification first and review the output before any trash operation.
- Never permanently delete Google Drive resources. Cleanup may only move explicitly allowlisted obsolete wedding forms to trash.
- Never modify or trash active form IDs listed in `form_links.json`.
- Do not add an ID to the cleanup allowlist unless it has been identified as a project-created obsolete wedding form and its internal Google Forms title has been verified.
- Preserve the restricted Google Drive OAuth scope (`drive.file`); do not broaden access to the user's Google Drive.
