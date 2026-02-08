import os
import sys
import argparse
from github import Github
from dotenv import load_dotenv

# Load environment
# Assuming script is run from project root or BAD/ dir
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')

def get_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or REPO_NAME not set.")
        sys.exit(1)
    g = Github(GITHUB_TOKEN)
    return g.get_repo(REPO_NAME)

def list_issues(args):
    repo = get_repo()
    state = args.state if args.state else 'open'
    issues = repo.get_issues(state=state)
    
    print(f"**{state.title()} Issues:**")
    count = 0
    for issue in issues:
        print(f"- **#{issue.number}**: {issue.title} ({issue.html_url})")
        count += 1
        if count >= 10:
            print("...(showing first 10)")
            break
    if count == 0:
        print("No issues found.")

def close_issue(args):
    repo = get_repo()
    try:
        issue = repo.get_issue(int(args.id))
        if issue.state == 'closed':
            print(f"⚠️ Issue #{issue.number} is already closed.")
        else:
            issue.edit(state='closed')
            print(f"✅ Closed issue **#{issue.number}**: {issue.title}")
    except Exception as e:
        print(f"❌ Error closing issue: {e}")

def comment_issue(args):
    repo = get_repo()
    try:
        issue = repo.get_issue(int(args.id))
        issue.create_comment(args.body)
        print(f"✅ Commented on **#{issue.number}**: '{args.body}'")
    except Exception as e:
        print(f"❌ Error commenting: {e}")

def get_issue_details(args):
    repo = get_repo()
    try:
        issue = repo.get_issue(int(args.id))
        print(f"**Issue #{issue.number}: {issue.title}**")
        print(f"**State:** {issue.state}")
        print(f"**Author:** {issue.user.login}")
        print(f"\n**Body:**\n{issue.body}")
        
        comments = issue.get_comments()
        if comments.totalCount > 0:
            print(f"\n**Comments ({comments.totalCount}):**")
            for c in comments:
                print(f"- **{c.user.login}:** {c.body[:200]}...") # Truncate for brevity
    except Exception as e:
        print(f"❌ Error getting issue: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage GitHub Issues")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # List
    parser_list = subparsers.add_parser('list', help='List issues')
    parser_list.add_argument('--state', default='open', choices=['open', 'closed', 'all'])

    # Get details
    parser_get = subparsers.add_parser('get', help='Get issue details')
    parser_get.add_argument('id', help='Issue Number')

    # Close
    parser_close = subparsers.add_parser('close', help='Close an issue')
    parser_close.add_argument('id', help='Issue Number')

    # Comment
    parser_comment = subparsers.add_parser('comment', help='Comment on an issue')
    parser_comment.add_argument('id', help='Issue Number')
    parser_comment.add_argument('body', help='Comment Body')

    args = parser.parse_args()

    if args.command == 'list':
        list_issues(args)
    elif args.command == 'get':
        get_issue_details(args)
    elif args.command == 'close':
        close_issue(args)
    elif args.command == 'comment':
        comment_issue(args)

if __name__ == "__main__":
    main()
