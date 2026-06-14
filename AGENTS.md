# Agent Instructions

Read `STEERING.md` before making project or Git workflow changes.

## Git Safety

- Treat `credentials.json`, `token.json`, `.env*`, private keys, OAuth client secrets, and service account files as local-only secrets.
- Treat `private_data/`, generated guest CSVs, invitee lists, RSVP exports, and alias files as local-only planning data.
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
- `fetch_form_responses.py` reads current Google Form responses and writes reconciled guest exports under `private_data/reports/`.
- `check_ukr_invitees.py` is the shared invitee-matching engine used for the Ukrainian and international reports.
- `check_all_invitees.py` combines the separate Ukrainian and international master lists into one consolidated report while preserving an `invitee_group` column.
- `refresh_invitee_reports.py` is the preferred end-to-end workflow: it fetches all active forms, rebuilds the English/Italian response subset, and regenerates all invitee reports.
- The refresh summary must report unique guests from affirmative responses as currently coming, plus master-list rows with `counted_present = no` as the practical outstanding count.
- `refresh_invitee_reports.cmd` is the Windows double-click launcher for the same refresh workflow.
- Keep the master lists separate:
  - `private_data/ukr_invitees.txt`
  - `private_data/en_it_invitees.txt`
- Keep alternate spellings and submitted-name variants in the corresponding alias files rather than changing canonical invitee names solely to match a response:
  - `private_data/ukr_invitee_aliases.csv`
  - `private_data/en_it_invitee_aliases.csv`
- Consolidated reports are written to `private_data/reports/all_invitee_status.csv` and `private_data/reports/all_uncounted_guests.csv`. The uncounted report must include both unmatched respondents and unmatched accompanying guests, distinguished by `guest_roles`.
- Status and uncounted reports include `contact_details` and `contact_source_respondents`. Accompanying guests inherit the contact supplied by the respondent who listed them.
- To refresh responses and all reports, run:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" refresh_invitee_reports.py
```

- Use `refresh_invitee_reports.py --reports-only` when only the private master lists or aliases changed and the existing reconciled response CSV is current.
- Run Python scripts with the local Conda environment Python:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" create_google_form.py
```

- Avoid `py -3` unless Python Launcher is configured. Prefer direct environment Python over `conda run -n expenses python ...` because `conda run` has hit Windows Unicode output errors.
- Keep website assets local unless the user explicitly asks for external assets.
- Keep generated RSVP analysis outputs in `private_data/reports/`; do not place new private CSV exports at the repository root unless they are temporary and ignored.

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
