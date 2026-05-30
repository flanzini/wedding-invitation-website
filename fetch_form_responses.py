from __future__ import annotations

import argparse
import csv
import json
import os.path
import re
import sys
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/forms.body.readonly",
]

CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
FORM_LINKS_FILE = "form_links.json"
DEFAULT_CSV_FILE = "private_data/reports/guest_list_reconciled.csv"


def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        else:
            creds = None
        if creds is None:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(
                    f"Google OAuth credentials file not found: {CREDS_FILE}."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return creds


def load_forms():
    with open(FORM_LINKS_FILE, "r", encoding="utf-8") as links_file:
        payload = json.load(links_file)
    forms = payload.get("forms", [])
    if not forms:
        raise ValueError(f"No forms found in {FORM_LINKS_FILE}.")
    return forms


def build_question_map(service, form_id):
    form = service.forms().get(formId=form_id).execute()
    question_map = {}
    for item in form.get("items", []):
        question_item = item.get("questionItem")
        if not question_item:
            continue
        question = question_item.get("question", {})
        question_id = question.get("questionId")
        if question_id:
            question_map[question_id] = item.get("title", question_id)
    return question_map


def parse_answers(answer):
    if "textAnswers" in answer:
        return ", ".join(
            text_answer.get("value", "")
            for text_answer in answer["textAnswers"].get("answers", [])
            if text_answer.get("value")
        )
    if "fileUploadAnswers" in answer:
        files = answer["fileUploadAnswers"].get("answers", [])
        return ", ".join(file_item.get("fileId", "") for file_item in files if file_item.get("fileId"))
    return "<unsupported answer type>"


def parse_int_from_text(value):
    if not value:
        return None
    lowered = value.lower()
    if "not sure" in lowered or "non lo sappiamo" in lowered or "поки не знаю" in lowered:
        return None
    if "not attending" in lowered or "non parteciperemo" in lowered or "не братиму участі" in lowered:
        return 0
    if "only me" in lowered or "solo io" in lowered or "тільки я" in lowered:
        return 1
    if "4 or more" in lowered or "4 o più" in lowered or "4 або більше" in lowered:
        return 4
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def looks_like_attending(value):
    if not value:
        return None
    lowered = value.lower()
    yes_markers = ["yes", "sì", "так"]
    no_markers = ["no, i/we", "no, purtroppo", "ні, на жаль"]
    maybe_markers = ["maybe", "forse", "можливо"]
    if any(marker in lowered for marker in no_markers):
        return False
    if any(marker in lowered for marker in maybe_markers):
        return None
    if any(marker in lowered for marker in yes_markers):
        return True
    return None


def extract_structured_fields(question_answers):
    fields = {
        "respondent_name": "",
        "attendance_raw": "",
        "attendance_bool": None,
        "guest_count_raw": "",
        "guest_count_num": None,
        "accompanying_names_raw": "",
        "contact_raw": "",
        "notes_raw": "",
    }

    for question_title, answer_value in question_answers:
        title = question_title.lower()
        if any(k in title for k in ["full name of the person", "nome e cognome della persona", "ім'я та прізвище особи"]):
            fields["respondent_name"] = answer_value
        elif any(k in title for k in ["will you join us", "potrete essere con noi", "чи зможете ви бути"]):
            fields["attendance_raw"] = answer_value
            fields["attendance_bool"] = looks_like_attending(answer_value)
        elif any(k in title for k in ["how many guests", "quante persone", "скільки гостей"]):
            fields["guest_count_raw"] = answer_value
            fields["guest_count_num"] = parse_int_from_text(answer_value)
        elif any(k in title for k in ["please list the full names", "indicate nome e cognome", "будь ласка, вкажіть ім'я"]):
            fields["accompanying_names_raw"] = answer_value
        elif any(k in title for k in ["email address and/or phone", "indirizzo email e/o numero", "email та/або номер"]):
            fields["contact_raw"] = answer_value
        elif any(k in title for k in ["is there anything we should know", "c'è qualcosa che dovremmo sapere", "чи є щось важливе"]):
            fields["notes_raw"] = answer_value

    return fields


def build_conflict_flags(fields):
    flags = []
    attending = fields["attendance_bool"]
    count = fields["guest_count_num"]
    if attending is False and count and count > 0:
        flags.append("attendance_no_but_guest_count_positive")
    if attending is True and count == 0:
        flags.append("attendance_yes_but_guest_count_zero")
    if count and count > 1 and not fields["accompanying_names_raw"]:
        flags.append("guest_count_gt_1_but_no_guest_names")
    return flags


def split_accompanying_names(raw_value):
    if not raw_value:
        return []
    normalized = raw_value.replace("\r", "\n")
    for token in [";", "&", ",", " і ", " and "]:
        normalized = normalized.replace(token, "\n")
    names = []
    for part in normalized.split("\n"):
        cleaned = part.strip(" -\t")
        if cleaned:
            names.append(cleaned)
    if len(names) == 1:
        only = names[0]
        words = only.split()
        # Heuristic: if one compact chunk looks like multiple two-word names,
        # split into pairs (e.g. "Козій Михайло Козій Уляна Емануель Клатзер").
        if (
            len(words) >= 4
            and len(words) % 2 == 0
            and all(word and word[0].isalpha() and word[0].isupper() for word in words)
        ):
            paired = [" ".join(words[i : i + 2]) for i in range(0, len(words), 2)]
            return paired
    return names


def split_person_names(raw_value):
    return split_accompanying_names(raw_value)


def normalize_name(value):
    return " ".join(value.lower().split())


def iso_to_local(iso_value):
    if not iso_value:
        return ""
    dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def fetch_responses_for_form(service, form_data, limit):
    form_id = form_data["form_id"]
    question_map = build_question_map(service, form_id)
    responses = []
    next_page_token = None

    while True:
        response_page = service.forms().responses().list(
            formId=form_id,
            pageSize=min(limit - len(responses), 500) if limit else 500,
            pageToken=next_page_token,
        ).execute()
        responses.extend(response_page.get("responses", []))
        next_page_token = response_page.get("nextPageToken")
        if not next_page_token:
            break
        if limit and len(responses) >= limit:
            break

    if limit:
        responses = responses[:limit]

    print(f"\n[{form_data['code']}] {form_data['name']} | {form_data['title']}")
    print(f"Form ID: {form_id}")
    print(f"Responses found: {len(responses)}")

    normalized_rows = []
    for idx, response in enumerate(responses, start=1):
        created = iso_to_local(response.get("createTime"))
        submitted = iso_to_local(response.get("lastSubmittedTime"))
        response_id = response.get("responseId", "")
        print(f"\nResponse #{idx}")
        if created:
            print(f"Created: {created}")
        if submitted:
            print(f"Submitted: {submitted}")
        answers = response.get("answers", {})
        if not answers:
            print("No answers recorded.")
            continue
        question_answers = []
        for _, answer in answers.items():
            question_id = answer.get("questionId", "")
            question_title = question_map.get(question_id, question_id or "<unknown question>")
            answer_value = parse_answers(answer)
            question_answers.append((question_title, answer_value))
            print(f"- {question_title}: {answer_value}")

        fields = extract_structured_fields(question_answers)
        conflicts = build_conflict_flags(fields)
        accompanying_names = split_accompanying_names(fields["accompanying_names_raw"])
        respondent_parts = split_person_names(fields["respondent_name"])
        respondent_guest_name = respondent_parts[0] if respondent_parts else fields["respondent_name"]

        respondent_primary_norm = normalize_name(respondent_guest_name) if respondent_guest_name else ""
        output_accompanying = []
        for name in accompanying_names:
            norm = normalize_name(name)
            if not norm:
                continue
            if norm == respondent_primary_norm:
                continue
            output_accompanying.append(name)

        # If respondent field contains multiple names (e.g. "A & B"), preserve extra names as accompanying guests.
        output_norms = {normalize_name(name) for name in output_accompanying}
        for extra_name in respondent_parts[1:]:
            norm = normalize_name(extra_name)
            if not norm or norm == respondent_primary_norm or norm in output_norms:
                continue
            output_norms.add(norm)
            output_accompanying.append(extra_name)

        base_row = {
            "form_code": form_data["code"],
            "form_name": form_data["name"],
            "response_id": response_id,
            "submitted_local": submitted or created,
            "respondent_name": fields["respondent_name"],
            "attendance_raw": fields["attendance_raw"],
            "attendance_bool": fields["attendance_bool"],
            "guest_count_raw": fields["guest_count_raw"],
            "guest_count_num": fields["guest_count_num"],
            "contact": fields["contact_raw"],
            "notes": fields["notes_raw"],
            "accompanying_names_raw": fields["accompanying_names_raw"],
            "conflict_flags": "|".join(conflicts),
        }
        normalized_rows.append({**base_row, "guest_name": respondent_guest_name, "guest_role": "respondent"})
        for name in output_accompanying:
            normalized_rows.append({**base_row, "guest_name": name, "guest_role": "accompanying"})
    return normalized_rows


def write_guest_csv(rows, csv_file):
    headers = [
        "form_code",
        "form_name",
        "response_id",
        "submitted_local",
        "guest_role",
        "guest_name",
        "respondent_name",
        "attendance_raw",
        "attendance_bool",
        "guest_count_raw",
        "guest_count_num",
        "contact",
        "notes",
        "accompanying_names_raw",
        "conflict_flags",
    ]
    with open(csv_file, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_reconciliation_summary(rows):
    response_ids = {row["response_id"] for row in rows if row["response_id"]}
    unique_guest_names = {row["guest_name"].strip().lower() for row in rows if row["guest_name"].strip()}
    conflicts = [row for row in rows if row.get("conflict_flags")]
    print("\nReconciliation summary")
    print(f"- Responses reconciled: {len(response_ids)}")
    print(f"- Guest rows exported: {len(rows)}")
    print(f"- Unique guest names (case-insensitive): {len(unique_guest_names)}")
    print(f"- Rows with conflict flags: {len(conflicts)}")


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(description="Fetch Google Form responses for wedding RSVP forms.")
    parser.add_argument(
        "--code",
        choices=["en", "it", "uk", "all"],
        default="all",
        help="Language code to fetch. Default: all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum responses to print per form. Default: 20.",
    )
    parser.add_argument(
        "--export-csv",
        default=DEFAULT_CSV_FILE,
        help=f"CSV output path for reconciled guest list. Default: {DEFAULT_CSV_FILE}.",
    )
    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be greater than 0.")

    creds = get_credentials()
    service = build("forms", "v1", credentials=creds)
    forms = load_forms()

    selected = forms if args.code == "all" else [form for form in forms if form.get("code") == args.code]
    if not selected:
        raise ValueError(f"No forms found for code '{args.code}' in {FORM_LINKS_FILE}.")

    print(f"UTC now: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    all_rows = []
    for form_data in selected:
        all_rows.extend(fetch_responses_for_form(service, form_data, args.limit))

    write_guest_csv(all_rows, args.export_csv)
    print_reconciliation_summary(all_rows)
    print(f"Saved reconciled guest list to: {args.export_csv}")


if __name__ == "__main__":
    main()
