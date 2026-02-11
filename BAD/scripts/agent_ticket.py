import os
import sys
import argparse
from github import Github
from dotenv import load_dotenv

# Load environment
# Try to find .env in project root or current dir
INITIAL_DIR = os.getcwd()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    load_dotenv() # Fallback

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')

def create_ticket(title, body, labels):
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or REPO_NAME not set.")
        return

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        issue = repo.create_issue(title=title, body=body, labels=labels)
        print(f"✅ Ticket Created Successfully!")
        print(f"Issue: #{issue.number}")
        print(f"Title: {title}")
        print(f"URL: {issue.html_url}")
        
    except Exception as e:
        print(f"❌ Error creating ticket: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Ticket Creator")
    parser.add_argument('title', help='Ticket Title')
    parser.add_argument('body', help='Ticket Body/Description')
    parser.add_argument('--labels', nargs='+', default=['agent-reported'], help='Labels (default: agent-reported)')
    
    args = parser.parse_args()
    
    create_ticket(args.title, args.body, args.labels)
