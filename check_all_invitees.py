from __future__ import annotations

import argparse
import csv

from check_ukr_invitees import (
    analyze,
    load_declined_names,
    load_invitees,
    load_message_names,
    read_guest_rows,
    write_uncounted,
)

DEFAULT_GUEST_CSV = "private_data/reports/guest_list_reconciled.csv"
DEFAULT_UKR_INVITEE_FILE = "private_data/ukr_invitees.txt"
DEFAULT_UKR_ALIAS_FILE = "private_data/ukr_invitee_aliases.csv"
DEFAULT_INTERNATIONAL_INVITEE_FILE = "private_data/en_it_invitees.txt"
DEFAULT_INTERNATIONAL_ALIAS_FILE = "private_data/en_it_invitee_aliases.csv"
DEFAULT_OUTPUT_CSV = "private_data/reports/all_invitee_status.csv"
DEFAULT_UNCOUNTED_CSV = "private_data/reports/all_uncounted_guests.csv"
DEFAULT_ACCEPTED_FILE = "private_data/accepted_invitees.txt"
DEFAULT_DECLINED_FILE = "private_data/declined_invitees.txt"


def load_grouped_invitees(
    ukr_path: str,
    ukr_alias_path: str | None,
    international_path: str,
    international_alias_path: str | None,
) -> list[dict]:
    grouped_invitees = []
    for invitee in load_invitees(ukr_path, ukr_alias_path):
        grouped_invitees.append({**invitee, "group": "ukrainian"})
    for invitee in load_invitees(international_path, international_alias_path):
        grouped_invitees.append({**invitee, "group": "international"})
    return grouped_invitees


def add_group_to_report(report_rows: list[dict], invitees: list[dict]) -> list[dict]:
    if len(report_rows) != len(invitees):
        raise ValueError("Invitee and report row counts do not match.")
    return [
        {
            "invitee_row_id": row["invitee_row_id"],
            "invitee_group": invitee["group"],
            **{key: value for key, value in row.items() if key != "invitee_row_id"},
        }
        for row, invitee in zip(report_rows, invitees)
    ]


def write_report(path: str, rows: list[dict]) -> None:
    headers = [
        "invitee_row_id",
        "invitee_group",
        "invitee_name",
        "aliases",
        "counted_present",
        "response_status",
        "accepted_by_message",
        "declined_by_message",
        "counted_via",
        "matched_form_codes",
        "contact_details",
        "contact_source_respondents",
        "responded_as_respondent",
        "response_count",
        "latest_response_id",
        "attendance_raw",
        "guest_count_total_including_respondent",
        "bringing_additional_guests",
        "listed_as_accompanying_count",
        "listed_by_respondents",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict], unknown_rows: list[dict]) -> None:
    counted = sum(1 for row in rows if row["counted_present"] == "yes")
    accepted = sum(1 for row in rows if row.get("response_status") == "accepted_by_message")
    declined = sum(1 for row in rows if row.get("response_status") == "declined_by_message")
    pending = sum(1 for row in rows if row.get("response_status") == "pending_response")
    direct = sum(1 for row in rows if row["responded_as_respondent"] == "yes")
    print("Consolidated invitee cross-check summary")
    print(f"- Invitees across all master lists: {len(rows)}")
    print(f"- Invitees counted present: {counted}")
    print(f"- Invitees accepted by message: {accepted}")
    print(f"- Invitees declined by message: {declined}")
    print(f"- Invitees still pending an answer: {pending}")
    print(f"- Invitees who responded directly: {direct}")
    print(f"- Uncounted external guests: {len(unknown_rows)}")
    for group in ("ukrainian", "international"):
        group_rows = [row for row in rows if row["invitee_group"] == group]
        group_counted = sum(1 for row in group_rows if row["counted_present"] == "yes")
        print(f"- {group.title()}: {group_counted} of {len(group_rows)} counted")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-check all invitee master lists against reconciled RSVP responses."
    )
    parser.add_argument("--guest-csv", default=DEFAULT_GUEST_CSV)
    parser.add_argument("--ukr-invitees", default=DEFAULT_UKR_INVITEE_FILE)
    parser.add_argument("--ukr-aliases", default=DEFAULT_UKR_ALIAS_FILE)
    parser.add_argument("--international-invitees", default=DEFAULT_INTERNATIONAL_INVITEE_FILE)
    parser.add_argument("--international-aliases", default=DEFAULT_INTERNATIONAL_ALIAS_FILE)
    parser.add_argument("--accepted", default=DEFAULT_ACCEPTED_FILE)
    parser.add_argument("--declined", default=DEFAULT_DECLINED_FILE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--uncounted-output", default=DEFAULT_UNCOUNTED_CSV)
    args = parser.parse_args()

    invitees = load_grouped_invitees(
        args.ukr_invitees,
        args.ukr_aliases,
        args.international_invitees,
        args.international_aliases,
    )
    accepted_names = load_message_names(args.accepted)
    declined_names = load_declined_names(args.declined)
    guest_rows = read_guest_rows(args.guest_csv)
    report_rows, unknown_rows = analyze(invitees, guest_rows, "all", declined_names, accepted_names)
    grouped_rows = add_group_to_report(report_rows, invitees)
    write_report(args.output, grouped_rows)
    write_uncounted(args.uncounted_output, unknown_rows)
    print_summary(grouped_rows, unknown_rows)
    print(f"Saved consolidated invitee report to: {args.output}")
    print(f"Saved consolidated uncounted guest report to: {args.uncounted_output}")


if __name__ == "__main__":
    main()
