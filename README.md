# Google Forms API Wedding Survey

This workspace includes:

- `create_google_form.py` to create three Google Forms, one each in English, Italian, and Ukrainian.
- `form_links.json` to store the generated form URLs.
- `index.html` as the standalone wedding landing page.

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

```bash
py -3 -m pip install --upgrade google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## Create Forms

```bash
py -3 create_google_form.py
```

The script will:

- open a browser window for Google sign-in
- save a `token.json` file after authorization
- create one Google Form per language
- save the generated links to `form_links.json`

It will not modify `index.html`.

## Website

Open `index.html` directly in a browser to test the landing page. The website currently has static links to the form URLs. If you recreate the forms, copy the new URLs from `form_links.json` into the matching buttons in `index.html`.

## Survey Content

Each form collects first name and last name as required fields.

The English and Italian forms ask whether guests would feel comfortable and interested in travelling to the planned Ukraine celebration, plus party size, possible Italy fallback interest, travel concerns, and optional contact details.

The Ukrainian form is written for guests living in Ukraine. It is framed as a tentative save-the-date and availability check for the Carpathian celebration on 14/15/16 May 2027, with more practical details to follow closer to the date.

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
