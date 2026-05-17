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

## Notes

- If you change `SCOPES`, delete `token.json` and rerun the script.
- If you rerun the script, it will create additional forms.
- Keep `credentials.json` and `token.json` private.
