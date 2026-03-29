# City of Austin Building Permits Tracker - Configuration

# Socrata SODA API for Issued Construction Permits
# Dataset: "Issued Construction Permits" on data.austintexas.gov
# Dataset ID: 3syk-w9eu
API_BASE = "https://data.austintexas.gov/resource/3syk-w9eu.json"

# Optional: register at https://data.austintexas.gov/profile/edit/developer_settings
# Without a token you get ~1,000 requests/hour; with one you get much higher limits.
APP_TOKEN = ""  # Set your Socrata app token here if you have one

# Permit types to track
# BP = Building, EP = Electrical, MP = Mechanical, PP = Plumbing, DS = Driveway/Sidewalks
PERMIT_TYPES = ["BP", "EP", "MP", "PP", "DS"]

# How far back to look on initial fetch (ISO date)
INITIAL_START_DATE = "2025-01-01"

# Page size per API request (max 50,000)
PAGE_SIZE = 5000

# Output files
DATA_DIR = "data"
PERMITS_FILE = "data/permits.json"
WEEKLY_DIR = "data/weekly"
CHANGELOG_FILE = "data/changelog.json"

# Fields to keep (reduces file size)
FIELDS = [
    "permit_number",
    "permittype",
    "permit_type_desc",
    "permit_class_mapped",
    "work_class",
    "status_current",
    "description",
    "original_address1",
    "original_city",
    "original_zip",
    "council_district",
    "applieddate",
    "issue_date",
    "statusdate",
    "expiresdate",
    "completed_date",
    "total_job_valuation",
    "total_new_add_sqft",
    "total_existing_bldg_sqft",
    "remodel_repair_sqft",
    "number_of_floors",
    "housing_units",
    "contractor_company_name",
    "contractor_full_name",
    "applicant_full_name",
    "applicant_org",
    "latitude",
    "longitude",
    "link",
    "project_id",
    "masterpermitnum",
]
