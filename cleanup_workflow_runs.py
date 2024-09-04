import os
import sys
import json
import requests
from datetime import datetime, timedelta

GITHUB_API_URL = "https://api.github.com"
REPO = os.getenv("REPO")
TOKEN = os.getenv("TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

LOG_FILE = "logs.json"
MAX_LOG_ENTRIES = 5

def get_runs(workflow_id, status=None, days_old=None):
    runs = []
    page = 1
    params = {"per_page": 100, "page": page}

    if status:
        params["status"] = status

    while True:
        response = requests.get(
            f"{GITHUB_API_URL}/repos/{REPO}/actions/workflows/{workflow_id}/runs",
            headers=HEADERS,
            params=params,
        )

        if response.status_code == 403:
            print("Rate limit reached, stopping cleanup.")
            sys.exit(1)

        response.raise_for_status()
        data = response.json()

        for run in data["workflow_runs"]:
            run_date = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if not days_old or run_date < datetime.now() - timedelta(days=days_old):
                runs.append(run["id"])

        if "next" not in response.links:
            break

        page += 1
        params["page"] = page

    return runs

def delete_run(run_id):
    response = requests.delete(
        f"{GITHUB_API_URL}/repos/{REPO}/actions/runs/{run_id}",
        headers=HEADERS,
    )
    response.raise_for_status()

def log_cleanup(details):
    logs = {"cleanup_logs": [], "bot_logs": []}

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            logs = json.load(file)

    if 'cleanup_logs' not in logs:
        logs['cleanup_logs'] = []

    logs['cleanup_logs'].append(details)

    if len(logs['cleanup_logs']) > MAX_LOG_ENTRIES:
        logs['cleanup_logs'] = logs['cleanup_logs'][-MAX_LOG_ENTRIES:]

    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)

def main():
    workflows = ["cleanup-workflow-runs.yml"]

    cleanup_details = {
        "timestamp": datetime.now().isoformat(),
        "details": []
    }

    for workflow in workflows:
        workflow_id = get_workflow_id(workflow)
        if not workflow_id:
            continue

        details = {
            "workflow": workflow,
            "deleted_success": 0,
            "deleted_failure": 0,
            "deleted_cancelled": 0,
        }

        success_runs = get_runs(workflow_id, status="success", days_old=5)
        for run_id in success_runs:
            delete_run(run_id)
            details["deleted_success"] += 1

        failed_runs = get_runs(workflow_id, status="failure", days_old=15)
        for run_id in failed_runs:
            delete_run(run_id)
            details["deleted_failure"] += 1

        canceled_runs = get_runs(workflow_id, status="cancelled")
        for run_id in canceled_runs:
            delete_run(run_id)
            details["deleted_cancelled"] += 1

        cleanup_details["details"].append(details)

    log_cleanup(cleanup_details)

def get_workflow_id(workflow_name):
    response = requests.get(
        f"{GITHUB_API_URL}/repos/{REPO}/actions/workflows",
        headers=HEADERS,
    )
    response.raise_for_status()
    workflows = response.json()["workflows"]

    for workflow in workflows:
        if workflow["path"].endswith(workflow_name):
            return workflow["id"]

    return None

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        sys.exit(1)
