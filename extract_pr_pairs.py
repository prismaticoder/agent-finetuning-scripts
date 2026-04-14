#!/usr/bin/env python3
"""
extract_pr_pairs.py
Extracts (PR description, diff) training pairs from merged PRs.
Requires: gh CLI authenticated, run from repo root.

Usage: python extract_pr_pairs.py --repo owner/repo --limit 200 --out pairs_pr.jsonl
"""

import subprocess
import json
import argparse
import sys

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def extract_pairs(repo, limit, out_path):
    print(f"Fetching {limit} merged PRs from {repo}...")
    prs_json = run(
        f"gh pr list --repo {repo} --state merged --limit {limit} "
        f"--json number,title,body"
    )
    if not prs_json:
        sys.exit("Could not fetch PRs. Is `gh` authenticated?")

    prs = json.loads(prs_json)
    pairs = []

    for pr in prs:
        number = pr["number"]
        title = pr["title"]
        body = pr.get("body", "").strip()

        # Get the diff for this PR
        diff = run(f"gh pr diff {number} --repo {repo}")
        if not diff or len(diff) < 100:
            continue  # skip empty or trivial diffs

        # Skip auto-generated files (lockfiles, generated code)
        if any(skip in diff for skip in ["package-lock.json", "yarn.lock", ".pb.go", "_generated"]):
            continue

        prompt = f"PR Title: {title}\n\n{body}".strip()
        completion = diff[:4000]  # cap diff length to avoid context blowout

        if len(prompt) < 50:
            continue  # skip PRs with no description

        pairs.append({
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion},
            ]
        })
        print(f"  ✓ PR #{number}: {title[:60]}")

    print(f"\nExtracted {len(pairs)} pairs.")
    with open(out_path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--out", default="pairs_pr.jsonl")
    args = parser.parse_args()
    extract_pairs(args.repo, args.limit, args.out)
