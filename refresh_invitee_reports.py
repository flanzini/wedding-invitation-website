from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

from check_ukr_invitees import normalize_name

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "private_data" / "reports"
GUEST_CSV = REPORTS_DIR / "guest_list_reconciled.csv"
EN_IT_GUEST_CSV = REPORTS_DIR / "guest_list_reconciled_en_it.csv"
ALL_INVITEE_STATUS_CSV = REPORTS_DIR / "all_invitee_status.csv"
ALL_UNCOUNTED_GUESTS_CSV = REPORTS_DIR / "all_uncounted_guests.csv"


def run_script(script: str, *args: str) -> None:
    command = [sys.executable, str(ROOT / script), *args]
    print(f"\nRunning {script}...", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def write_en_it_guest_csv() -> None:
    if not GUEST_CSV.exists():
        raise FileNotFoundError(f"Reconciled guest CSV not found: {GUEST_CSV}")

    with GUEST_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = [row for row in reader if row.get("form_code", "").strip() in {"en", "it"}]
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise ValueError(f"Reconciled guest CSV has no header: {GUEST_CSV}")

    with EN_IT_GUEST_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Saved English/Italian response rows to: {EN_IT_GUEST_CSV.relative_to(ROOT)}",
        flush=True,
    )


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def is_affirmative(value: str) -> bool:
    return value.strip().lower() == "true"


def print_planning_summary() -> None:
    guest_rows = read_csv(GUEST_CSV)
    status_rows = read_csv(ALL_INVITEE_STATUS_CSV)
    uncounted_rows = read_csv(ALL_UNCOUNTED_GUESTS_CSV)

    attending_names = {
        normalize_name(row.get("guest_name", ""))
        for row in guest_rows
        if is_affirmative(row.get("attendance_bool", "")) and normalize_name(row.get("guest_name", ""))
    }
    uncounted_names = {
        row.get("guest_name_normalized", "").strip()
        for row in uncounted_rows
        if row.get("guest_name_normalized", "").strip() in attending_names
    }
    accepted_by_message = sum(1 for row in status_rows if row.get("response_status", "") == "accepted_by_message")
    declined_by_message = sum(1 for row in status_rows if row.get("response_status", "") == "declined_by_message")
    practical_outstanding = sum(1 for row in status_rows if row.get("response_status", "") == "pending_response")
    matched_attending = len(attending_names - uncounted_names)
    people_currently_coming = len(attending_names) + accepted_by_message

    print("\nCurrent planning summary")
    print(f"- People currently coming: {people_currently_coming}")
    print(f"- Matched master-list guests coming: {matched_attending}")
    print(f"- Unlisted guests coming: {len(uncounted_names)}")
    print(f"- Master-list invitees accepted by message: {accepted_by_message}")
    print(f"- Master-list invitees declined by message: {declined_by_message}")
    print(f"- Master-list invitees still needing an answer: {practical_outstanding}")


def refresh_reports(fetch_responses: bool, limit: int) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if fetch_responses:
        run_script(
            "fetch_form_responses.py",
            "--code",
            "all",
            "--limit",
            str(limit),
            "--export-csv",
            str(GUEST_CSV.relative_to(ROOT)),
        )

    write_en_it_guest_csv()

    run_script("check_ukr_invitees.py")
    run_script(
        "check_ukr_invitees.py",
        "--guest-csv",
        str(EN_IT_GUEST_CSV.relative_to(ROOT)),
        "--invitees",
        "private_data/en_it_invitees.txt",
        "--aliases",
        "private_data/en_it_invitee_aliases.csv",
        "--form-code",
        "all",
        "--output",
        "private_data/reports/en_it_invitee_status.csv",
        "--uncounted-output",
        "private_data/reports/en_it_uncounted_guests.csv",
    )
    run_script("check_all_invitees.py")
    print_planning_summary()

    print("\nRefresh complete.")
    print("Main report: private_data/reports/all_invitee_status.csv")
    print("Uncounted guests: private_data/reports/all_uncounted_guests.csv")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch all wedding RSVP responses and regenerate invitee reports."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum responses fetched per form. Default: 500.",
    )
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Regenerate reports from the existing reconciled CSV without contacting Google.",
    )
    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be greater than 0.")

    refresh_reports(fetch_responses=not args.reports_only, limit=args.limit)


if __name__ == "__main__":
    main()
