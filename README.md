# Austin Building Permits Tracker

Automatically fetches, stores, and tracks weekly changes to building permits issued by the **City of Austin** via the [Austin Open Data Portal](https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu).

## What It Does

- **Full fetch** — pulls all issued construction permits from Austin's Socrata SODA API going back to Jan 2025
- **Weekly diff** — every Monday, compares the latest data against the previous snapshot and saves only what's new or changed
- **Changelog** — maintains a running `data/changelog.json` with a summary of each weekly run (new permits, status changes, count)
- **GitHub Actions** — fully automated, no server required; results committed back to this repo

## Data Source

| Field | Value |
|---|---|
| Portal | [data.austintexas.gov](https://data.austintexas.gov) |
| Dataset | Issued Construction Permits |
| Dataset ID | `3syk-w9eu` |
| API | Socrata SODA (JSON) |
| Update frequency | Weekly (Mondays 8 AM UTC) |

## Permit Types Tracked

| Code | Type |
|---|---|
| `BP` | Building |
| `EP` | Electrical |
| `MP` | Mechanical |
| `PP` | Plumbing |
| `DS` | Driveway / Sidewalks |

## Data Fields Captured

Each permit record includes: permit number, type, status, address, council district, applied/issued/expiry dates, job valuation, square footage, housing units, contractor, applicant, and lat/long coordinates.

## Project Structure

```
austin-permits-tracker/
├── fetch_permits.py          # Full permit fetch → data/permits.json
├── weekly_tracker.py         # Weekly diff → data/weekly/YYYY-MM-DD.json
├── config.py                 # API endpoint, fields, date range settings
├── requirements.txt          # requests, sodapy
├── data/
│   ├── permits.json          # Full current snapshot
│   ├── changelog.json        # Weekly run history & summaries
│   └── weekly/               # Per-week diff files
└── .github/workflows/
    └── weekly_tracker.yml    # GitHub Actions cron job
```

## Setup & Local Usage

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Add a Socrata app token
Register at [data.austintexas.gov](https://data.austintexas.gov/profile/edit/developer_settings) for a free app token to get higher API rate limits, then set it in `config.py`:
```python
APP_TOKEN = "your_token_here"
```

### 3. Run a full fetch
```bash
python fetch_permits.py
```
Saves all permits to `data/permits.json`.

### 4. Run the weekly tracker
```bash
python weekly_tracker.py
```
Diffs against the last snapshot and saves changes to `data/weekly/YYYY-MM-DD.json`.

## GitHub Actions (Automated)

The workflow runs every **Monday at 8:00 AM UTC** (3:00 AM Austin time) automatically.

You can also trigger it manually:
1. Go to **Actions** → **Weekly Austin Permits Tracker**
2. Click **Run workflow**

Each run commits updated JSON files back to this repo, so the data stays current without any manual work.

## Output Files

### `data/permits.json`
Full snapshot of all tracked permits. Each record looks like:
```json
{
  "permit_number": "2025-001234 BP",
  "permittype": "BP",
  "permit_type_desc": "Building Permit",
  "status_current": "Active",
  "original_address1": "123 Congress Ave",
  "original_city": "Austin",
  "original_zip": "78701",
  "council_district": "9",
  "issue_date": "2025-03-01T00:00:00.000",
  "total_job_valuation": "450000.00",
  "total_new_add_sqft": "2400",
  "housing_units": "1",
  "contractor_company_name": "ABC Construction LLC",
  "latitude": "30.2672",
  "longitude": "-97.7431"
}
```

### `data/weekly/YYYY-MM-DD.json`
Diff for that week — only new permits and permits with status changes.

### `data/changelog.json`
Running history of every weekly run with counts and summary stats.

## License

Data sourced from the City of Austin Open Data Portal under the [Open Data Commons Public Domain Dedication and License](https://opendatacommons.org/licenses/pddl/).
