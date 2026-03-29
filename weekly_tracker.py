"""
Austin Building Permits - Weekly Tracker

Runs the permit fetcher on a schedule (default: every Monday at 8 AM).
Can also be triggered manually or set up as a cron job.

Usage:
    python weekly_tracker.py              # run scheduler (stays alive)
    python weekly_tracker.py --once       # run once and exit
    python weekly_tracker.py --cron       # print crontab line for system cron setup
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import schedule
import time

import config
from fetch_permits import run as fetch_run


def weekly_job():
    """Run the weekly permit update and generate a diff report."""
    print(f"\n{'='*60}")
    print(f"Weekly Austin Permits Update - {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}\n")

    fetch_run(update_mode=True)
    generate_weekly_report()


def generate_weekly_report():
    """Generate a summary report of changes from the past week."""
    if not os.path.exists(config.CHANGELOG_FILE):
        print("No changelog found yet.")
        return

    with open(config.CHANGELOG_FILE, "r") as f:
        changelog = json.load(f)

    # Filter to last 7 days
    cutoff = datetime.now(timezone.utc).timestamp() - (7 * 86400)
    recent = []
    for entry in changelog:
        try:
            ts = datetime.fromisoformat(entry["timestamp"]).timestamp()
            if ts >= cutoff:
                recent.append(entry)
        except (KeyError, ValueError):
            continue

    if not recent:
        print("No changes in the past 7 days.")
        return

    new_permits = [e for e in recent if e["type"] == "new"]
    updated_permits = [e for e in recent if e["type"] == "updated"]

    report = {
        "report_date": datetime.now(timezone.utc).isoformat(),
        "period": "last_7_days",
        "summary": {
            "new_permits": len(new_permits),
            "updated_permits": len(updated_permits),
        },
        "new_permits": new_permits[:50],  # cap at 50 for readability
        "status_changes": [
            e for e in updated_permits
            if "status_current" in e.get("changed_fields", {})
        ],
    }

    # Compute valuation of new permits
    total_new_val = 0
    for p in new_permits:
        try:
            total_new_val += float(p.get("details", {}).get("valuation", 0) or 0)
        except (ValueError, TypeError):
            pass
    report["summary"]["total_new_valuation"] = total_new_val

    report_path = os.path.join(config.WEEKLY_DIR, f"report_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json")
    os.makedirs(config.WEEKLY_DIR, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nWeekly Report: {report_path}")
    print(f"  New permits this week: {len(new_permits)}")
    print(f"  Updated permits: {len(updated_permits)}")
    print(f"  New permit valuation: ${total_new_val:,.0f}")
    print(f"  Status changes: {len(report['status_changes'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Austin Permits Weekly Tracker")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--cron", action="store_true", help="Print crontab line for system cron")
    parser.add_argument("--day", default="monday", help="Day of week to run (default: monday)")
    parser.add_argument("--time", default="08:00", dest="run_time", help="Time to run (default: 08:00)")
    args = parser.parse_args()

    if args.cron:
        script_path = os.path.abspath(__file__)
        python_path = sys.executable
        print("# Add this line to your crontab (crontab -e):")
        print(f"0 8 * * 1 cd {os.path.dirname(script_path)} && {python_path} {script_path} --once >> cron.log 2>&1")
        sys.exit(0)

    if args.once:
        weekly_job()
        sys.exit(0)

    # Schedule recurring run
    getattr(schedule.every(), args.day).at(args.run_time).do(weekly_job)
    print(f"Scheduler started. Will run every {args.day} at {args.run_time}.")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)
