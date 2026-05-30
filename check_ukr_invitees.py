from __future__ import annotations

import argparse
import csv
import difflib
import os.path
import re
from collections import Counter, defaultdict, deque

DEFAULT_GUEST_CSV = "private_data/reports/guest_list_reconciled.csv"
DEFAULT_INVITEE_FILE = "private_data/ukr_invitees.txt"
DEFAULT_ALIAS_FILE = "private_data/ukr_invitee_aliases.csv"
DEFAULT_OUTPUT_CSV = "private_data/reports/ukr_invitee_status.csv"
DEFAULT_UNCOUNTED_CSV = "private_data/reports/ukr_uncounted_guests.csv"


def normalize_name(value: str) -> str:
    value = value.lower().strip()
    value = value.replace("’", "'").replace("`", "'").replace("ʼ", "'")
    value = re.sub(r"\b\d+\s*(?:р|р\.|роки|років|року|years?|yrs?)\b", " ", value)
    value = re.sub(r"\b(?:вік|age)\s*[-:]?\s*\d+\b", " ", value)
    value = re.sub(r"[()\".,;:!?]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def name_signature(value: str) -> str:
    words = normalize_name(value).split()
    return " ".join(sorted(words))


def split_aliases(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def load_invitees(path: str, alias_path: str | None) -> list[dict]:
    alias_map: dict[str, list[str]] = defaultdict(list)
    if alias_path and os.path.exists(alias_path):
        with open(alias_path, "r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                invitee_name = row.get("invitee_name", "").strip()
                aliases = split_aliases(row.get("aliases", ""))
                if invitee_name and aliases:
                    alias_map[invitee_name].extend(aliases)

    invitees = []
    with open(path, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            name = line.strip()
            if name:
                invitees.append({"name": name, "aliases": alias_map.get(name, [])})
    return invitees


def read_guest_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def best_match(name: str, candidates: list[str], threshold: float = 0.88) -> str | None:
    if not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=threshold)
    return matches[0] if matches else None


def add_match_key(match_keys: dict[str, str], key: str, canonical_norm: str) -> None:
    norm = normalize_name(key)
    if not norm:
        return
    match_keys.setdefault(norm, canonical_norm)
    signature = name_signature(norm)
    if signature:
        match_keys.setdefault(signature, canonical_norm)


def build_match_indexes(invitees: list[dict]) -> tuple[list[str], dict[str, str]]:
    invitee_norms = sorted({normalize_name(row["name"]) for row in invitees if normalize_name(row["name"])})
    match_keys = {norm: norm for norm in invitee_norms}
    for row in invitees:
        canonical_norm = normalize_name(row["name"])
        add_match_key(match_keys, row["name"], canonical_norm)
        for alias in row["aliases"]:
            add_match_key(match_keys, alias, canonical_norm)
    return invitee_norms, match_keys


def match_invitee_name(name: str, invitee_norms: list[str], match_keys: dict[str, str]) -> str | None:
    norm = normalize_name(name)
    if not norm:
        return None
    if norm in match_keys:
        return match_keys[norm]
    signature = name_signature(norm)
    if signature in match_keys:
        return match_keys[signature]
    return best_match(norm, invitee_norms)


def build_response_index(rows: list[dict], form_code: str) -> dict[str, dict]:
    selected_rows = rows if form_code == "all" else [r for r in rows if r.get("form_code", "").strip() == form_code]
    by_response: dict[str, dict] = {}
    for row in selected_rows:
        response_id = row.get("response_id", "").strip()
        if not response_id:
            continue
        payload = by_response.setdefault(
            response_id,
            {
                "form_code": row.get("form_code", ""),
                "respondent_name": row.get("respondent_name", "").strip(),
                "attendance_raw": row.get("attendance_raw", "").strip(),
                "guest_count_num": row.get("guest_count_num", "").strip(),
                "guest_names": [],
            },
        )
        guest_name = row.get("guest_name", "").strip()
        if guest_name:
            payload["guest_names"].append(guest_name)
    return by_response


def analyze(invitees: list[dict], guest_rows: list[dict], form_code: str) -> tuple[list[dict], list[dict]]:
    responses = build_response_index(guest_rows, form_code)
    invitee_norms, match_keys = build_match_indexes(invitees)
    invitee_norm_counts = Counter(normalize_name(row["name"]) for row in invitees if normalize_name(row["name"]))

    respondent_hits: dict[str, list[dict]] = defaultdict(list)
    accompanying_hits: dict[str, list[dict]] = defaultdict(list)
    unknown_guest_hits: dict[str, list[dict]] = defaultdict(list)

    for response_id, payload in responses.items():
        respondent_raw = payload["respondent_name"]
        respondent_match = match_invitee_name(respondent_raw, invitee_norms, match_keys)
        if respondent_match:
            respondent_hits[respondent_match].append(
                {
                    "response_id": response_id,
                    "form_code": payload["form_code"],
                    "respondent_name": respondent_raw,
                    "attendance_raw": payload["attendance_raw"],
                    "guest_count_num": payload["guest_count_num"],
                }
            )

        respondent_guest_name_norm = normalize_name(payload["guest_names"][0]) if payload["guest_names"] else ""
        for guest_name in payload["guest_names"][1:]:
            guest_norm = normalize_name(guest_name)
            if not guest_norm or guest_norm == respondent_guest_name_norm:
                continue
            guest_match = match_invitee_name(guest_name, invitee_norms, match_keys)
            if guest_match:
                accompanying_hits[guest_match].append(
                    {
                        "response_id": response_id,
                        "form_code": payload["form_code"],
                        "listed_as_guest_name": guest_name,
                        "listed_by_respondent": respondent_raw,
                    }
                )
            else:
                unknown_guest_hits[guest_norm].append(
                    {
                        "guest_name": guest_name,
                        "response_id": response_id,
                        "form_code": payload["form_code"],
                        "listed_by_respondent": respondent_raw,
                    }
                )

    respondent_queues = {norm: deque(entries) for norm, entries in respondent_hits.items()}
    accompanying_queues = {norm: deque(entries) for norm, entries in accompanying_hits.items()}
    report_rows = []
    for ordinal, invitee in enumerate(invitees, start=1):
        canonical = invitee["name"]
        norm = normalize_name(canonical)
        if invitee_norm_counts[norm] > 1:
            respondent_entries = [respondent_queues[norm].popleft()] if respondent_queues.get(norm) else []
            accompanying_entries = [accompanying_queues[norm].popleft()] if accompanying_queues.get(norm) else []
        else:
            respondent_entries = list(respondent_hits.get(norm, []))
            accompanying_entries = list(accompanying_hits.get(norm, []))

        responded = "yes" if respondent_entries else "no"
        latest_response = respondent_entries[-1] if respondent_entries else {}
        guest_count_num = latest_response.get("guest_count_num", "")
        try:
            bringing_additional = max(int(guest_count_num) - 1, 0) if guest_count_num else ""
        except ValueError:
            bringing_additional = ""

        counted_via = []
        if respondent_entries:
            counted_via.append("respondent")
        if accompanying_entries:
            counted_via.append("accompanying")

        report_rows.append(
            {
                "invitee_row_id": ordinal,
                "invitee_name": canonical,
                "aliases": "; ".join(invitee["aliases"]),
                "counted_present": "yes" if counted_via else "no",
                "counted_via": "|".join(counted_via),
                "matched_form_codes": "; ".join(sorted({e["form_code"] for e in respondent_entries + accompanying_entries})),
                "responded_as_respondent": responded,
                "response_count": len(respondent_entries),
                "latest_response_id": latest_response.get("response_id", ""),
                "attendance_raw": latest_response.get("attendance_raw", ""),
                "guest_count_total_including_respondent": guest_count_num,
                "bringing_additional_guests": bringing_additional,
                "listed_as_accompanying_count": len(accompanying_entries),
                "listed_by_respondents": "; ".join(sorted({e["listed_by_respondent"] for e in accompanying_entries})),
            }
        )

    unknown_rows = []
    for norm, entries in unknown_guest_hits.items():
        unknown_rows.append(
            {
                "guest_name_normalized": norm,
                "guest_name_raw_examples": "; ".join(sorted({e["guest_name"] for e in entries})),
                "times_seen": len(entries),
                "form_codes": "; ".join(sorted({e["form_code"] for e in entries})),
                "listed_by_respondents": "; ".join(sorted({e["listed_by_respondent"] for e in entries})),
                "response_ids": "; ".join(sorted({e["response_id"] for e in entries})),
            }
        )
    unknown_rows.sort(key=lambda r: (-int(r["times_seen"]), r["guest_name_normalized"]))
    return report_rows, unknown_rows


def write_report(path: str, rows: list[dict]) -> None:
    headers = [
        "invitee_row_id",
        "invitee_name",
        "aliases",
        "counted_present",
        "counted_via",
        "matched_form_codes",
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


def write_uncounted(path: str, rows: list[dict]) -> None:
    headers = [
        "guest_name_normalized",
        "guest_name_raw_examples",
        "times_seen",
        "form_codes",
        "listed_by_respondents",
        "response_ids",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict], unknown_rows: list[dict]) -> None:
    counted = sum(1 for r in rows if r["counted_present"] == "yes")
    respondent_count = sum(1 for r in rows if r["responded_as_respondent"] == "yes")
    print("UKR invitee cross-check summary")
    print(f"- Invitees in mother list: {len(rows)}")
    print(f"- Invitees counted (respondent or accompanying): {counted}")
    print(f"- Invitees who responded directly: {respondent_count}")
    print(f"- Uncounted external guests (not in mother list): {len(unknown_rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-check UKR invitee mother list against reconciled guest CSV.")
    parser.add_argument("--guest-csv", default=DEFAULT_GUEST_CSV, help=f"Input guest CSV. Default: {DEFAULT_GUEST_CSV}")
    parser.add_argument("--invitees", default=DEFAULT_INVITEE_FILE, help=f"Mother list file path. Default: {DEFAULT_INVITEE_FILE}")
    parser.add_argument("--aliases", default=DEFAULT_ALIAS_FILE, help=f"Optional invitee alias CSV. Default: {DEFAULT_ALIAS_FILE}")
    parser.add_argument("--form-code", choices=["all", "en", "it", "uk"], default="all", help="Responses to check. Default: all.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help=f"Output report CSV. Default: {DEFAULT_OUTPUT_CSV}")
    parser.add_argument("--uncounted-output", default=DEFAULT_UNCOUNTED_CSV, help=f"Output CSV for guests not in mother list. Default: {DEFAULT_UNCOUNTED_CSV}")
    args = parser.parse_args()

    invitees = load_invitees(args.invitees, args.aliases)
    guest_rows = read_guest_rows(args.guest_csv)
    report_rows, unknown_rows = analyze(invitees, guest_rows, args.form_code)
    write_report(args.output, report_rows)
    write_uncounted(args.uncounted_output, unknown_rows)
    print_summary(report_rows, unknown_rows)
    print(f"Saved invitee status report to: {args.output}")
    print(f"Saved uncounted guest report to: {args.uncounted_output}")


if __name__ == "__main__":
    main()
