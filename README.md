# Wedding Invitation Website and RSVP Forms

This workspace includes:

- `create_google_form.py` to create three Google Forms, one each in English, Italian, and Ukrainian.
- `fetch_form_responses.py` to read submitted responses from the active forms listed in `form_links.json`.
- `form_links.json` to store generated form URLs and Google Form IDs.
- `index.html` as the standalone wedding invitation page.

The form script does not rewrite the website. Edit `index.html` directly for layout, copy, styling, and mobile behavior.

## Setup

1. Create a Google Cloud project at https://console.cloud.google.com.
2. Enable the **Google Forms API** for the project.
3. Create OAuth 2.0 credentials:
   - Go to **APIs & Services > Credentials**
   - Create **OAuth client ID**
   - Choose **Desktop app**
   - Download the JSON file and save it as `credentials.json` in this folder

## Install Dependencies

This project currently uses the local Conda environment named `expenses`.

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" -m pip install --upgrade google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## Create Forms

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" create_google_form.py
```

The script will:

- open a browser window for Google sign-in
- save a `token.json` file after authorization
- create one Google Form per language
- save the generated links and form IDs to `form_links.json`

It will not modify `index.html`.

## Fetch Form Responses (Test)

Use the active form IDs in `form_links.json` and print responses:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" fetch_form_responses.py --code all --limit 20
```

Fetch one language only:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" fetch_form_responses.py --code en --limit 20
```

`--code` supports `en`, `it`, `uk`, or `all`.

To also generate a reconciled guest CSV while fetching responses:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" fetch_form_responses.py --code all --limit 200 --export-csv private_data/reports/guest_list_reconciled.csv
```

## Cross-Check UKR Invitees

Store the private mother list in:

```text
private_data/ukr_invitees.txt
```

Optional transliterations or alternate spellings can be stored in:

```text
private_data/ukr_invitee_aliases.csv
```

Then compare it against the reconciled guest list:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" check_ukr_invitees.py --guest-csv private_data/reports/guest_list_reconciled.csv --invitees private_data/ukr_invitees.txt --aliases private_data/ukr_invitee_aliases.csv --form-code all --output private_data/reports/ukr_invitee_status.csv --uncounted-output private_data/reports/ukr_uncounted_guests.csv
```

The report includes:

- whether each invitee is counted (`counted_present`) either through an RSVP match or a message acceptance
- whether each invitee is coming, accepted by message, declined by message, or still pending (`response_status`)
- how they were counted (`counted_via`)
- which language form(s) matched (`matched_form_codes`)
- respondent details and guest counts for planning

It also writes a separate file for people found in responses but not in the mother list:

```text
private_data/reports/ukr_uncounted_guests.csv
```

## Consolidated Invitee Report

Keep the Ukrainian and international master lists separate in:

```text
private_data/ukr_invitees.txt
private_data/en_it_invitees.txt
```

When someone tells you by message that they are coming but will not fill the form, add their name to:

```text
private_data/accepted_invitees.txt
```

When someone tells you by message that they are not coming, add their name to:

```text
private_data/declined_invitees.txt
```

Use one invitee per line in both files. The reports mark accepted invitees as `response_status = accepted_by_message` and declined invitees as `response_status = declined_by_message`; invitees without a matched RSVP or message status remain `pending_response`. If a message-accepted invitee later submits the RSVP form, the form match takes precedence on the next refresh.

Generate one report across both lists and all three RSVP forms:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" check_all_invitees.py
```

The consolidated report adds an `invitee_group` column and writes:

```text
private_data/reports/all_invitee_status.csv
private_data/reports/all_uncounted_guests.csv
```

Matching all invitees in one pass prevents guests who answer through a different language form from being incorrectly reported as external guests. The uncounted report includes both unmatched respondents and unmatched accompanying guests; use `guest_roles` to distinguish them.

Future cleanup: `check_ukr_invitees.py` now contains shared invitee reconciliation logic used by Ukrainian, English/Italian, and consolidated reports. Consider moving that shared logic into a neutrally named module such as `invitee_reconciliation.py`, while keeping `check_ukr_invitees.py` as the Ukrainian report CLI wrapper.

### One-command refresh

Fetch all active English, Italian, and Ukrainian forms and regenerate every invitee report with:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" refresh_invitee_reports.py
```

On Windows, you can also double-click `refresh_invitee_reports.cmd` in File Explorer. A browser may open if Google authorization needs to be renewed.

After rebuilding the reports, the refresh command prints the current attending guest count, its matched/unlisted/message-accepted split, the number of master-list invitees who declined by message, and the practical number still pending an answer.

To rebuild the reports from the most recently fetched responses without contacting Google:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" refresh_invitee_reports.py --reports-only
```

Avoid `py -3` on this machine unless Python Launcher is configured with a Python 3 install. Also prefer the direct environment Python command above over `conda run -n expenses python create_google_form.py`; `conda run` has hit a Windows Unicode output issue even when the script itself succeeds.

## Website

Open `index.html` directly in a browser to test the invitation page. The website has static links to the RSVP forms. If you recreate the forms, copy the new URLs from `form_links.json` into the matching links in `index.html`.

## RSVP Content

Each form asks for the name of the person responding, attendance, the number of guests joining them, any dietary or accessibility needs, and a required email address and/or phone number for confirmed wedding details. If two or more guests will attend together, a conditional section also requests the names of accompanying guests and the ages of any children.

Accommodation is provided for guests and is no longer a form question. Vyshyvanka rental is not collected through the form; interested guests can contact the couple directly.

Each form description includes a short privacy note explaining that submitted information is used only to organise the wedding and communicate with guests, is kept private, and is deleted when no longer needed.

The English and Italian forms provide the international guest context for the planned Carpathian celebration and travel arrangements.

The Ukrainian form is written for guests living in Ukraine and focuses on attendance and organisational details rather than explaining the Carpathian location or international travel.

## Deployment

The intended public URL is:

```text
https://antoninafilippo.info
```

The site is hosted with GitHub Pages from:

```text
https://github.com/flanzini/wedding-invitation-website
```

GitHub Pages should use the custom domain:

```text
antoninafilippo.info
```

GoDaddy DNS should keep the default `NS` and `SOA` records and use these website records:

```text
A      @      185.199.108.153
A      @      185.199.109.153
A      @      185.199.110.153
A      @      185.199.111.153
CNAME  www    flanzini.github.io
```

Do not use GoDaddy forwarding for this site. The old `A @ WebsiteBuilder Site` record and `CNAME www antoninafilippo.info.` should be removed.

Useful DNS checks from PowerShell:

```powershell
Resolve-DnsName antoninafilippo.info -Type A -Server ns11.domaincontrol.com
Resolve-DnsName www.antoninafilippo.info -Type CNAME -Server ns11.domaincontrol.com
```

As of the latest setup pass, GoDaddy's authoritative nameserver was returning the expected GitHub Pages records. If GitHub still reports `InvalidDNSError`, wait for DNS/cache propagation, then remove and re-add the custom domain in GitHub Pages settings.

## Notes

- If you change `SCOPES`, delete `token.json` and rerun the script.
- `fetch_form_responses.py` uses read-only response scopes. If your existing `token.json` does not include them, delete `token.json` and run the script again to re-authorize.
- If you rerun the script, it will create additional forms.
- Keep `credentials.json` and `token.json` private.

## Cleanup Obsolete Forms

`cleanup_google_forms.py` is intentionally limited in destructive mode to an explicit allowlist of obsolete wedding form IDs. It never permanently deletes Google Drive files, refuses to touch any active form ID in `form_links.json`, verifies the expected Google Form title, and only moves verified forms to trash.

Cleanup requires the Google Drive API to be enabled for the same Google Cloud project. The OAuth scope remains limited to `drive.file`; do not replace it with broader Google Drive access.

If additional obsolete forms need to be identified, run the separate read-only discovery mode. It lists only accessible Google Form files and their internal form titles; it cannot trash anything:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" cleanup_google_forms.py --discover
```

Run a read-only check first:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" cleanup_google_forms.py
```

Only after reviewing the dry-run output, move the verified obsolete forms to trash:

```powershell
& "C:\Users\filip\Miniconda3\envs\expenses\python.exe" cleanup_google_forms.py --trash --confirm "TRASH ONLY OBSOLETE WEDDING FORMS"
```
