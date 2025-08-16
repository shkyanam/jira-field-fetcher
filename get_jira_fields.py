import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
url = f"{JIRA_DOMAIN}/rest/api/3/field"

response = requests.get(url, auth=auth)

if response.status_code != 200:
    print(f"Error {response.status_code}: {response.text}")
    exit(1)

fields = response.json()

# Print in the required format
for f in fields:
    print(f"ID: {f['id']}, Name: {f['name']}")
