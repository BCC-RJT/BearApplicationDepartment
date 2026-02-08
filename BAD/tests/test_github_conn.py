
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')

print(f"Token present: {bool(GITHUB_TOKEN)}")
print(f"Repo Name: {REPO_NAME}")

if not GITHUB_TOKEN:
    print("No token!")
    exit(1)

try:
    g = Github(GITHUB_TOKEN, timeout=10)
    user = g.get_user()
    print(f"Authenticated as: {user.login}")
    
    if REPO_NAME:
        repo = g.get_repo(REPO_NAME)
        print(f"Repo found: {repo.full_name}")
        print(f"Open issues count: {repo.open_issues_count}")
    
except Exception as e:
    print(f"Error: {e}")
