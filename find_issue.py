import requests
import json


token = os.environ.get("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}"}


def get_repos(url):
    all_repos = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            all_repos.append(repo['full_name'])
    return all_repos

def check_issue(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/2"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            issue = response.json()
            print(f"[{repo_full_name}] Issue #2: {issue.get('title')}")
            if "Refine Result Link" in issue.get('title', ''):
                print(f"!!! FOUND IT: {repo_full_name} !!!")
                return True
        else:
            # print(f"[{repo_full_name}] No Issue #2 or Error: {response.status_code}")
            pass
    except Exception as e:
        print(f"[{repo_full_name}] Error: {e}")
    return False

print("Fetching repos...")
repos = get_repos("https://api.github.com/users/BCC-RJT/repos?per_page=100")
print(f"Scanning {len(repos)} repositories for Issue #2...")

for repo in repos:
    if check_issue(repo):
        break
