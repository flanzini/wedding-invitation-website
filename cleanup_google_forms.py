from __future__ import print_function

import argparse
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from create_google_form import FORM_LINKS_FILE, get_credentials


FORM_MIME_TYPE = "application/vnd.google-apps.form"
CONFIRMATION_PHRASE = "TRASH ONLY OBSOLETE WEDDING FORMS"

# Only forms explicitly identified during this project's RSVP iterations can
# ever be touched by this script. Add another ID only after checking it first.
OBSOLETE_FORMS = {
    "1duTMs-vyU9hSuxBOVKBEnNmLcBSap_gz33PilI2iNs4": "RSVP | Antonina & Filippo",
    "1Cv4mz4EacvK02sVGx_bFo51lA7KPBd4QVUsweDK-mco": "Conferma presenza | Antonina & Filippo",
    "17vS2uPV1JgM-rV8rTjIWGgL1WhsdgDDcUKfOHZHzVY4": "Підтвердження участі | Антоніна та Філіппо",
    "1PDROYaBFyA4vqQZ-J0gRXdkO85A-4exOCsC2aIeK95M": "RSVP | Antonina & Filippo",
    "1KrgErqq06C24zh2p5Sil5dXPt0TcKK_lE-iCnwTHGC8": "Conferma presenza | Antonina & Filippo",
    "1xLWiE5Cv08HYWJEB0RJoHDBKtg6bRDdk3qweBquGPPs": "Підтвердження участі | Антоніна та Філіппо",
    "1mO6vqVl5wS3iVjnHRERGNNtSywlq3YrpNftmkVVon24": "RSVP | Antonina & Filippo",
    "1S2FOh7rwEb-QauEwO-tip8FB3fnX7ykgxYS576VK6wo": "Опитування щодо поїздки на весілля",
    "1CQ56J2MJvDljqpUHOTXWJMmQfaIdQhMz7bNRsdDJHOQ": "Підтвердження участі | Антоніна та Філіппо",
    "1fnpf_jGlq9ORYbTZ1OUgGgI_88vbux_GkJhdpcEgYNs": "Conferma presenza | Antonina & Filippo",
    "11r6UwnM9i-W-Zm4IJIfMlpHgYkuDA5ThcyWYJH2HitQ": "RSVP | Antonina & Filippo",
    "17NybdMpDgYoV18-zO_ILnyuSY3DpGyLmxV0TlXeNwxQ": "Wedding travel interest survey",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Safely inspect or trash explicitly allowlisted obsolete wedding forms."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--discover",
        action="store_true",
        help="Read-only listing of accessible Google Forms and their internal titles.",
    )
    mode.add_argument(
        "--trash",
        action="store_true",
        help="Move verified obsolete forms to Google Drive trash. Default is read-only.",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help="Required with --trash: exact confirmation phrase printed in the instructions.",
    )
    return parser.parse_args()


def get_active_ids():
    with open(FORM_LINKS_FILE, encoding="utf-8") as links_file:
        return {form["form_id"] for form in json.load(links_file)["forms"]}


def get_allowlisted_form(drive, form_id):
    return drive.files().get(
        fileId=form_id,
        fields="id,name,mimeType,trashed",
    ).execute()


def get_form_title(forms, form_id):
    form = forms.forms().get(formId=form_id).execute()
    return form["info"]["title"]


def validate_candidate(drive_file, form_title, expected_title, active_ids):
    if drive_file["id"] in active_ids:
        return "ACTIVE form ID: refusing to touch it"
    if drive_file.get("mimeType") != FORM_MIME_TYPE:
        return "not a Google Form: refusing to touch it"
    if form_title != expected_title:
        return f"unexpected form title {form_title!r}: refusing to touch it"
    return ""


def discover_forms(drive, forms, active_ids):
    files = drive.files().list(
        q=f"mimeType='{FORM_MIME_TYPE}' and trashed=false",
        spaces="drive",
        fields="files(id,name,mimeType,trashed)",
        pageSize=100,
    ).execute().get("files", [])

    for drive_file in files:
        form_id = drive_file["id"]
        try:
            form_title = get_form_title(forms, form_id)
        except HttpError as error:
            print(f"UNREADABLE {form_id}: Forms API returned {error.resp.status}")
            continue
        state = "ACTIVE" if form_id in active_ids else "NOT ACTIVE"
        print(
            f"{state} {form_id}: internal title={form_title!r}; "
            f"Drive name={drive_file.get('name')!r}"
        )

    print("\nDiscovery mode only. No Google Drive resources were changed.")


def main():
    args = parse_args()
    if args.trash and args.confirm != CONFIRMATION_PHRASE:
        raise SystemExit(
            "Refusing destructive mode. Re-run with "
            f'--trash --confirm "{CONFIRMATION_PHRASE}" after reviewing dry-run output.'
        )

    active_ids = get_active_ids()
    overlap = active_ids.intersection(OBSOLETE_FORMS)
    if overlap:
        raise SystemExit(
            "Safety stop: an active form ID is present in the obsolete allowlist: "
            + ", ".join(sorted(overlap))
        )

    credentials = get_credentials()
    drive = build("drive", "v3", credentials=credentials)
    forms = build("forms", "v1", credentials=credentials)
    if args.discover:
        discover_forms(drive, forms, active_ids)
        return

    verified = []
    for form_id, expected_title in OBSOLETE_FORMS.items():
        try:
            drive_file = get_allowlisted_form(drive, form_id)
            form_title = get_form_title(forms, form_id)
        except HttpError as error:
            print(f"SKIP {form_id}: not accessible ({error.resp.status})")
            continue

        reason = validate_candidate(drive_file, form_title, expected_title, active_ids)
        if reason:
            print(f"REFUSE {form_id}: {reason}")
            continue
        if drive_file.get("trashed"):
            print(f"ALREADY TRASHED {form_id}: {form_title}")
            continue
        print(f"VERIFIED OBSOLETE {form_id}: {form_title}")
        verified.append({"id": form_id, "name": form_title})

    if not args.trash:
        print("\nDry run only. No Google Drive resources were changed.")
        print(
            f'To trash the {len(verified)} verified obsolete form(s), re-run with '
            f'--trash --confirm "{CONFIRMATION_PHRASE}".'
        )
        return

    for form in verified:
        drive.files().update(
            fileId=form["id"],
            body={"trashed": True},
            fields="id,trashed",
        ).execute()
        print(f"TRASHED {form['id']}: {form['name']}")

    print("\nCompleted. Active forms were never considered for modification.")


if __name__ == "__main__":
    main()
