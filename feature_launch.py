import requests
from datetime import datetime, timedelta, timezone
import os
import json
import csv
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# =============================
# CONFIGURATION
# =============================
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")
LAUNCH_DATE_FIELD = "customfield_10040"  # Replace with your correct custom field ID
DAYS_LOOKAHEAD = 90
OUTPUT_CSV = "feature_launch_insights.csv"

# =============================
# AUTHENTICATION
# =============================
auth = (JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Accept": "application/json"}

# =============================
# BUILD JQL QUERY
# =============================
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
future_date = (datetime.now(timezone.utc) + timedelta(days=DAYS_LOOKAHEAD)).strftime("%Y-%m-%d")

jql = f'project = {PROJECT_KEY} AND {LAUNCH_DATE_FIELD} >= "{today}" AND {LAUNCH_DATE_FIELD} <= "{future_date}" ORDER BY {LAUNCH_DATE_FIELD} ASC'

# =============================
# FETCH ISSUES FROM JIRA
# =============================
url = f"{JIRA_DOMAIN}/rest/api/2/search"
params = {"jql": jql, "fields": f"summary,status,{LAUNCH_DATE_FIELD},project", "maxResults": 100}

response = requests.get(url, headers=headers, auth=auth)

if response.status_code != 200:
    print(f"❌ API request failed with status {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

# =============================
# PROCESS & CLASSIFY
# =============================
insights = []
for issue in data.get("issues", []):
    key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "-")
    status = fields.get("status", {}).get("name", "-")
    project_name = fields.get("project", {}).get("name", "-")

    launch_date_raw = fields.get(LAUNCH_DATE_FIELD)
    launch_date = None
    if launch_date_raw:
        launch_date = datetime.strptime(launch_date_raw.split("T")[0], "%Y-%m-%d")

    risk_flag = "ON TRACK"
    if launch_date:
        today_utc = datetime.now(timezone.utc).date()
        launch_date_only = launch_date.date()
        if launch_date_only < today_utc:
            risk_flag = "❌ DELAYED"
        elif (launch_date_only - today_utc).days <= 7 and status.lower() not in ["ready", "released"]:
            risk_flag = "⚠ AT RISK"

    insights.append([
        project_name,
        key,
        summary,
        launch_date.strftime("%Y-%m-%d") if launch_date else "-",
        status,
        risk_flag
    ])

# =============================
# SAVE TO CSV
# =============================
headers = ["Project", "Key", "Summary", "Launch Date", "Status", "Risk"]

with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(insights)

print(f"✅ Feature launch insights saved to {OUTPUT_CSV}")
