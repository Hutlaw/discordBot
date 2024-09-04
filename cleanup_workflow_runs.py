import requests
import os
import sys
from datetime import datetime, timedelta

GITHUB_API_URL = "https://api.github.com"
REPO = os.getenv("REPO")
TOKEN = os.getenv("TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def get_runs(workflow_id, status, days_old):
    cutoff_date = datetime.now() - timedelta(days=days_old)
    cutoff_iso = cutoff_date.isoformat() + "Z"
    runs = []
    page = 1

    while True:
        response = requests.get(
            f"{GITHUB_API_URL}/repos/{REPO}/actions/workflows/{workflow_id}/runs",
            headers=HEADERS,
            params={"status": status, "per_page": 100, "page": page},
        )

        if response.status_code == 403:
            print("Rate limit reached, stopping cleanup.")
            sys.exit(1)

        response.raise_for_status()
        data = response.json()

        for run in data["workflow_runs"]:
            if run["created_at"] < cutoff_iso:
                runs.append(run["id"])

        if "next" not in response.links:
            break

        page += 1

    return runs

def delete_run(run_id):
    response = requests.delete(
        f"{GITHUB_API_URL}/repos/{REPO}/actions/runs/{run_id}",
        headers=HEADERS,
    )
    response.raise_for_status()

def main():
    workflows = ["run-bot.yml", "wait-for-command.yml"]

    for workflow in workflows:
        print(f"Processing workflow: {workflow}")
        workflow_id = get_workflow_id(workflow)
        if not workflow_id:
            print(f"Workflow {workflow} not found.")
            continue

        success_runs = get_runs(workflow_id, "success", 5)
        for run_id in success_runs:
            print(f"Deleting successful run: {run_id}")
            delete_run(run_id)

        failed_runs = get_runs(workflow_id, "failure", 15)
        for run_id in failed_runs:
            print(f"Deleting failed run: {run_id}")
            delete_run(run_id)

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
        print(f"Error: {e}")
        sys.exit(1)
