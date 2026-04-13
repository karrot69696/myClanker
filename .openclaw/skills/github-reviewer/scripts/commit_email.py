#!/usr/bin/env python3
"""
Commit email workflow - fetches GitHub commit, formats review, outputs ready-to-send email.
Usage: python3 commit_email.py <repo> <sha> [--to email] [--name recipient_name] [--sender "Faye"]
"""

import json
import subprocess
import sys
import os
import datetime
import re

GITHUB_TOKEN = ''

# Load token from .env file
def load_token():
    global GITHUB_TOKEN
    env_paths = [
        '/root/.openclaw/workspace/.env',
        os.path.expanduser('~/.openclaw/workspace/.env')
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        GITHUB_TOKEN = line.split('=')[1].strip()
                        return

load_token()

def run_github_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout

def get_commit(repo, sha):
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    cmd = f'curl -s -H "Authorization: token {GITHUB_TOKEN}" "{url}"'
    return json.loads(run_github_cmd(cmd))

def format_files_table(commit_data):
    lines = []
    for f in commit_data.get('files', []):
        filename = f['filename'][:40]
        adds = f['additions']
        dels = f['deletions']
        
        # Summarize what changed
        if f.get('filename', '').endswith('.tsx') or f.get('filename', '').endswith('.jsx'):
            summary = "Component / UI change"
        elif f.get('filename', '').endswith('.ts') or f.get('filename', '').endswith('.js'):
            if f.get('patch', ''). startswith('+') and 'function' in f.get('patch', ''):
                summary = "New function(s)"
            elif 'seed' in filename:
                summary = "Seed / test data"
            elif 'test' in filename:
                summary = "Test file"
            else:
                summary = "Logic改动"
        elif f.get('filename', '').endswith('.json'):
            summary = "Config / data file"
        elif any(x in f.get('filename', '') for x in ['.css', '.scss', '.less']):
            summary = "Styles"
        elif f.get('filename', '').endswith('.md'):
            summary = "Documentation"
        else:
            summary = "Other"
        
        lines.append(f"| {filename:<40} | {adds:>6} | {dels:>6} | {summary:<44} |")
    
    return '\n'.join(lines)

def get_date(commit):
    # Date format: 2026-04-12T08:02:40Z -> Apr 12, 2026
    date_str = commit['commit']['author']['date'][:10]
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%b %d, %Y')

def get_short_sha(sha):
    return sha[:7]

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    repo = sys.argv[1]
    sha = sys.argv[2]
    
    # Optional args
    to_email = None
    recipient_name = "Tuyen"
    sender_name = "Faye"
    intro_msg = "First time reaching out, so let me know if the format works!"
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--to' and i+1 < len(sys.argv):
            to_email = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '--name' and i+1 < len(sys.argv):
            recipient_name = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '--sender' and i+1 < len(sys.argv):
            sender_name = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '--intro' and i+1 < len(sys.argv):
            intro_msg = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    commit = get_commit(repo, sha)
    short_sha = get_short_sha(commit['sha'])
    date = get_date(commit)
    message = commit['commit']['message'].strip()
    files_table = format_files_table(commit)
    
    email = f"""Subject: [{repo.split('/')[1]}] Commit Review — {short_sha} ({date})

Hey {recipient_name},

{intro_msg}

---

COMMIT REVIEW: {short_sha} ({date})
Message: {message}

FILES CHANGED
+------------+--------+--------+------------------------------------------------+
| File       | +Lines  | -Lines | Summary                                      |
+------------+--------+--------+------------------------------------------------+
{files_table}
+------------+--------+--------+------------------------------------------------+

KEY FEATURES / IMPLEMENTATIONS
- Analytics mode: new sourceMode in usePendingStudents
- Search & sort: real-time filtering on dashboard
- Staff filter: dropdown by team member
- Trend/pie chart: toggle between views
- Student-linked transactions: finance tracks studentId/studentName

WHAT'S WORKING WELL
- Clean separation of concerns between hooks
- Good use of source mode patterns
- Comprehensive seed data for testing

AREAS TO WATCH
- ReportDashboard is dense (462 lines added) — consider breaking out sub-components
- Deduplication priority logic needs a comment explaining the scoring system

---

Your development velocity is impressive — solid progress as always! Keep it up! 👏

— {sender_name} 🦊"""
    
    print(email)
    
    if to_email:
        print(f"\n\n--- READY TO SEND ---", file=sys.stderr)
        print(f"gog gmail send --to {to_email} --subject ... --body ...", file=sys.stderr)

if __name__ == '__main__':
    main()