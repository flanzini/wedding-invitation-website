# Wedding Invitation Website and RSVP Forms

This workspace includes:

- `create_google_form.py` to create three Google Forms, one each in English, Italian, and Ukrainian.
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

Avoid `py -3` on this machine unless Python Launcher is configured with a Python 3 install. Also prefer the direct environment Python command above over `conda run -n expenses python create_google_form.py`; `conda run` has hit a Windows Unicode output issue even when the script itself succeeds.

## Website

Open `index.html` directly in a browser to test the invitation page. The website has static links to the RSVP forms. If you recreate the forms, copy the new URLs from `form_links.json` into the matching links in `index.html`.

## RSVP Content

Each form collects the guest's full name in one required field, then asks for attendance, party size, accommodation needs, optional interest in renting a traditional Ukrainian vyshyvanka, other planning needs, and optional contact details.

The English and Italian forms provide the international guest context for the planned Carpathian celebration and travel arrangements.

The Ukrainian form is written for guests living in Ukraine and focuses on attendance, accommodation, and organisational details rather than explaining the Carpathian location or international travel.

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
- If you rerun the script, it will create additional forms.
- Keep `credentials.json` and `token.json` private.
