import os
import requests
import json


token = os.environ.get("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}"}


def list_repos(url):
    print(f"--- Fetching {url} ---")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        repos = response.json()
        print(f"Found {len(repos)} repositories.")
        for repo in repos:
            print(f"{repo['name']} - {repo['clone_url']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

list_repos("https://api.github.com/users/BCC-RJT/repos?per_page=100")
list_repos("https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator,organization_member")
