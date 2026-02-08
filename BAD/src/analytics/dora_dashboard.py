import os
import re
import sys
from datetime import datetime, timedelta, timezone
from statistics import mean
import statistics

try:
    from dotenv import load_dotenv
    from github import Github, GithubException, Auth
except ImportError as e:
    print(f"Error: Missing dependency. {e}")
    print("Please run: pip install PyGithub python-dotenv")
    sys.exit(1)

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO") or os.getenv("REPO_NAME")
    
    if not token:
        print("Error: GITHUB_TOKEN not found in .env")
        sys.exit(1)
        
    if not repo_name:
        print("Error: GITHUB_REPO or REPO_NAME not found in .env")
        sys.exit(1)
        
    return token, repo_name

def get_linked_issue_time(pr, repo):
    """
    Try to find a linked issue in the PR body (e.g., 'Closes #123').
    Returns the created_at time of the linked issue if found, otherwise None.
    """
    if not pr.body:
        return None
        
    # Regex to find 'Closes #123', 'Fixes #123', etc.
    # GitHub keywords: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved
    match = re.search(r'(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)', pr.body, re.IGNORECASE)
    
    if match:
        issue_number = int(match.group(1))
        try:
            issue = repo.get_issue(issue_number)
            return issue.created_at
        except GithubException:
            # Issue might not exist or be accessible
            return None
            
    return None

def calculate_metrics(token, repo_name):
    """Fetch data and calculate DORA metrics."""
    auth = Auth.Token(token)
    g = Github(auth=auth)
    try:
        repo = g.get_repo(repo_name)
    except GithubException as e:
        print(f"Error accessing repository '{repo_name}': {e}")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    
    print(f"Fetching data for {repo_name} since {thirty_days_ago.date()}...")

    # 1. Deployment Frequency: Merged PRs in last 30 days
    # We search for PRs that are merged and closed >= 30 days ago
    # GitHub search qualifiers: type:pr is:merged closed:>=YYYY-MM-DD
    query_date = thirty_days_ago.strftime("%Y-%m-%d")
    pr_query = f"repo:{repo_name} type:pr is:merged closed:>={query_date}"
    
    try:
        merged_prs = list(g.search_issues(query=pr_query))
    except GithubException as e:
        print(f"Error searching PRs: {e}")
        sys.exit(1)

    # Filter out any that might have slipped through (search is inclusive) or are docs only if possible
    # For now, we take all merged PRs as "deployments"
    deployment_count = len(merged_prs)
    
    # 2. Lead Time for Changes
    lead_times = []
    
    for pr_issue in merged_prs:
        # search_issues returns Issue objects, need to get PR details for some fields if needed, 
        # but Issue object for a PR has pull_request url. 
        # However, to get 'merged_at', we need the PR object.
        pr = pr_issue.as_pull_request()
        
        if pr.merged_at < thirty_days_ago:
            continue
            
        # Try to find linked issue
        start_time = get_linked_issue_time(pr, repo)
        
        # Fallback to PR creation time
        if not start_time:
            start_time = pr.created_at
            
        lead_time = pr.merged_at - start_time
        lead_times.append(lead_time.total_seconds())

    avg_lead_time_seconds = mean(lead_times) if lead_times else 0
    
    # 3. Change Failure Rate
    # Count issues/PRs created in last 30 days with "bug" or "hotfix" in title or label
    # This is a heuristic.
    bug_query = f"repo:{repo_name} created:>={query_date} (label:bug OR label:hotfix OR \"bug\" in:title OR \"hotfix\" in:title)"
    try:
        bug_issues = list(g.search_issues(query=bug_query))
    except GithubException as e:
        print(f"Error searching bugs: {e}")
        sys.exit(1)
        
    failure_count = len(bug_issues)
    
    # Calculate Failure Rate
    # If 0 deployments, rate is 0 if no bugs, else maybe 100%? Let's say 0.
    if deployment_count > 0:
        failure_rate = (failure_count / deployment_count) * 100
    else:
        failure_rate = 0.0

    return {
        "deployment_count": deployment_count,
        "avg_lead_time_seconds": avg_lead_time_seconds,
        "failure_count": failure_count,
        "failure_rate": failure_rate
    }

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return hours, minutes

def get_verdict(deployment_count, lead_time_seconds, failure_rate):
    # Arbitrary thresholds for "BAD" context
    # Elite: Daily deployments, < 1 day lead time, < 15% failure
    # High: Weekly deployments, < 1 week lead time, < 30% failure
    # ...
    
    if deployment_count == 0:
        return "Low"

    score = 0
    
    # deploy frequency
    if deployment_count >= 30: score += 3 # Daily
    elif deployment_count >= 4: score += 2 # Weekly
    elif deployment_count >= 1: score += 1
    
    # lead time
    day_seconds = 86400
    if lead_time_seconds < day_seconds: score += 3
    elif lead_time_seconds < day_seconds * 7: score += 2
    elif lead_time_seconds < day_seconds * 30: score += 1
    # If longer than 30 days (which shouldn't happen with our query but technically possible if calculation is weird), 0 points
    
    # failure rate
    if failure_rate < 15: score += 3
    elif failure_rate < 30: score += 2
    elif failure_rate < 50: score += 1
    
    if score >= 8: return "Elite"
    if score >= 6: return "High"
    if score >= 4: return "Medium"
    return "Low"

def main():
    print("Initializing DORA Dashboard...")
    token, repo_name = load_config()
    
    metrics = calculate_metrics(token, repo_name)
    
    hours, minutes = format_duration(metrics["avg_lead_time_seconds"])
    verdict = get_verdict(metrics["deployment_count"], metrics["avg_lead_time_seconds"], metrics["failure_rate"])
    
    print("\n" + "="*41)
    print("🐻 B.A.D. DORA REPORT (Last 30 Days)")
    print("="*41)
    print(f"🚀 Velocity:        {metrics['deployment_count']} Shipped Updates (approx {metrics['deployment_count']/4:.1f}/week)")
    print(f"⏱️ Mean Lead Time:  {hours} hours, {minutes} minutes")
    print(f"🔥 Stability:       {metrics['failure_rate']:.1f}% Failure Rate")
    print("="*41)
    print(f"VERDICT: {verdict} Performer")

if __name__ == "__main__":
    main()
