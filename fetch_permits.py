"""
Austin Building Permits Tracker - Fetcher

Pulls issued construction permits from the City of Austin's open data portal
(data.austintexas.gov) via the Socrata SODA API.

Dataset: Issued Construction Permits (3syk-w9eu)
Source:  https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu

Usage:
    python fetch_permits.py                # fetch all permits since INITIAL_START_DATE
    python fetch_permits.py --since 2026-01-01  # fetch permits issued since a specific date
    python fetch_permits.py --update       # incremental update (only new/changed since last run)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

import config


def build_headers():
    headers = {"Accept": "application/json"}
    if config.APP_TOKEN:
        headers["X-App-Token"] = config.APP_TOKEN
    return headers


def fetch_page(since_date, offset=0, limit=config.PAGE_SIZE):
    """Fetch one page of permits from the SODA API."""
    select = ",".join(config.FIELDS)
    params = {
        "$select": select,
        "$where": f"issue_date >= '{since_date}'",
        "$order": "issue_date DESC",
        "$limit": limit,
        "$offset": offset,
    }
    resp = requests.get(config.API_BASE, headers=build_headers(), params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_all(since_date):
    """Page through the API and return all permits since the given date."""
    all_permits = []
    offset = 0
    while True:
        print(f"  Fetching offset {offset}...")
        page = fetch_page(since_date, offset=offset)
        if not page:
            break
        all_permits.extend(page)
        if len(page) < config.PAGE_SIZE:
            break
        offset += len(page)
        time.sleep(0.5)  # be polite to the API
    return all_permits


def load_existing():
    """Load previously saved permits from disk."""
    if os.path.exists(config.PERMITS_FILE):
        with open(config.PERMITS_FILE, "r") as f:
            return json.load(f)
    return {"meta": {}, "permits": {}}


def save_permits(data):
    """Save permits data to disk."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.PERMITS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved {len(data['permits'])} permits to {config.PERMITS_FILE}")


def detect_changes(old_permits, new_permits_list):
    """Compare old and new permits, return (merged_dict, changes_list)."""
    changes = []
    merged = dict(old_permits)

    for permit in new_permits_list:
        pnum = permit.get("permit_number", "")
        if not pnum:
            continue

        if pnum not in merged:
            changes.append({
                "type": "new",
                "permit_number": pnum,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "address": permit.get("original_address1", ""),
                    "permit_type": permit.get("permit_type_desc", ""),
                    "status": permit.get("status_current", ""),
                    "valuation": permit.get("total_job_valuation", ""),
                },
            })
        else:
            old = merged[pnum]
            changed_fields = {}
            for key in permit:
                old_val = old.get(key, "")
                new_val = permit.get(key, "")
                if str(old_val) != str(new_val) and new_val:
                    changed_fields[key] = {"old": old_val, "new": new_val}
            if changed_fields:
                changes.append({
                    "type": "updated",
                    "permit_number": pnum,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "changed_fields": changed_fields,
                })

        merged[pnum] = permit

    return merged, changes


def save_changelog(changes):
    """Append changes to the changelog file."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    existing = []
    if os.path.exists(config.CHANGELOG_FILE):
        with open(config.CHANGELOG_FILE, "r") as f:
            existing = json.load(f)
    existing.extend(changes)
    with open(config.CHANGELOG_FILE, "w") as f:
        json.dump(existing, f, indent=2, default=str)
    print(f"Logged {len(changes)} changes to {config.CHANGELOG_FILE}")


def save_weekly_snapshot(data):
    """Save a dated weekly snapshot."""
    os.makedirs(config.WEEKLY_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(config.WEEKLY_DIR, f"permits_{today}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Weekly snapshot saved to {path}")


def run(since_date=None, update_mode=False):
    existing_data = load_existing()
    old_permits = existing_data.get("permits", {})

    if update_mode and existing_data.get("meta", {}).get("last_fetched"):
        # Go back 7 days from last fetch to catch any late-appearing records
        last = datetime.fromisoformat(existing_data["meta"]["last_fetched"])
        since_date = (last - timedelta(days=7)).strftime("%Y-%m-%d")
        print(f"Update mode: fetching permits since {since_date}")
    elif not since_date:
        since_date = config.INITIAL_START_DATE

    print(f"Fetching Austin building permits issued since {since_date}...")
    new_permits = fetch_all(since_date)
    print(f"Fetched {len(new_permits)} permits from API")

    if not new_permits:
        print("No permits returned. Check your date range or network.")
        return

    merged, changes = detect_changes(old_permits, new_permits)

    new_count = sum(1 for c in changes if c["type"] == "new")
    updated_count = sum(1 for c in changes if c["type"] == "updated")
    print(f"Changes: {new_count} new, {updated_count} updated")

    data = {
        "meta": {
            "source": "City of Austin Open Data - Issued Construction Permits",
            "dataset_id": "3syk-w9eu",
            "api_url": config.API_BASE,
            "last_fetched": datetime.now(timezone.utc).isoformat(),
            "since_date": since_date,
            "total_permits": len(merged),
        },
        "permits": merged,
    }

    save_permits(data)

    if changes:
        save_changelog(changes)

    save_weekly_snapshot(data)

    print_summary(merged)


def print_summary(permits):
    """Print a quick summary of the permits data."""
    print("\n--- Summary ---")
    print(f"Total permits tracked: {len(permits)}")

    by_type = {}
    by_status = {}
    total_val = 0.0
    for p in permits.values():
        t = p.get("permit_type_desc", "Unknown")
        s = p.get("status_current", "Unknown")
        by_type[t] = by_type.get(t, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        try:
            total_val += float(p.get("total_job_valuation", 0) or 0)
        except (ValueError, TypeError):
            pass

    print("\nBy permit type:")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    print("\nBy status:")
    for s, count in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {s}: {count}")

    print(f"\nTotal job valuation: ${total_val:,.0f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Austin building permits")
    parser.add_argument("--since", help="Fetch permits issued since this date (YYYY-MM-DD)")
    parser.add_argument("--update", action="store_true", help="Incremental update from last fetch")
    args = parser.parse_args()

    run(since_date=args.since, update_mode=args.update)
