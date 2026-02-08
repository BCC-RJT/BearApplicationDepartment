
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("REPO_NAME")

if not token or not repo_name:
    print("Error: GITHUB_TOKEN or REPO_NAME missing in .env")
    exit(1)

g = Github(token)
repo = g.get_repo(repo_name)

keywords = ["VM", "Virtual Machine", "IP Address", "External IP", "Connect", "SSH"]

print(f"Searching {repo_name} for keywords: {keywords}")

issues = repo.get_issues(state="all") # Search open and closed
found = False

for issue in issues:
    content = f"{issue.title} {issue.body}"
    # Check comments too? Maybe too slow. Let's check issue body first.
    
    hits = [k for k in keywords if k.lower() in content.lower()]
    if hits:
        print(f"\nIssue #{issue.number}: {issue.title}")
        print(f"  Keywords: {hits}")
        # Print snippet?
        lines = issue.body.split('\n')
        for line in lines:
            if any(k.lower() in line.lower() for k in keywords):
                print(f"  Snippet: {line.strip()}")
        found = True
        
        # Check comments if body isn't enough?
        comments = issue.get_comments()
        for comment in comments:
            if any(k.lower() in comment.body.lower() for k in keywords):
                 print(f"  Comment by {comment.user.login}:")
                 for line in comment.body.split('\n'):
                     if any(k.lower() in line.lower() for k in keywords):
                         print(f"    Snippet: {line.strip()}")

if not found:
    print("No relevant issues found.")
