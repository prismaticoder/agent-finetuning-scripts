#!/usr/bin/env python3
"""
coder.py — CLI harness for your finetuned coding assistant.

Usage:
  python coder.py "How does the auth middleware handle expired tokens?"
  python coder.py --repo /path/to/repo "What does the UserService class do?"
"""

import sys
import os
import subprocess
import json
import argparse
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "my-coder"
MAX_CONTEXT_CHARS = 6000  # leave room for the model's response

def search_codebase(repo_path, query):
    """Use ripgrep to find the most relevant lines for the query."""
    stopwords = {"what", "does", "how", "the", "this", "that", "with", "from", "into"}
    terms = [w for w in query.lower().split() if len(w) > 4 and w not in stopwords]

    if not terms:
        return ""

    snippets = []
    for term in terms[:3]:  # top 3 terms to avoid noise
        try:
            result = subprocess.run(
                ["rg", "--ignore-case", "--context", "5", "--max-count", "2",
                 "--glob", "!*.{json,lock,min.js,pb.go}", term, repo_path],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout:
                snippets.append(result.stdout[:2000])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return "\n---\n".join(snippets)[:MAX_CONTEXT_CHARS]

def ask(query, repo_path):
    context = search_codebase(repo_path, query)

    if context:
        prompt = (
            f"The following code snippets are from the codebase:\n\n"
            f"```\n{context}\n```\n\n"
            f"Question: {query}"
        )
    else:
        prompt = query

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": True
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            for line in response:
                chunk = json.loads(line.decode())
                print(chunk.get("response", ""), end="", flush=True)
                if chunk.get("done"):
                    print()
                    break
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask your codebase a question.")
    parser.add_argument("query", nargs="+", help="Your question")
    parser.add_argument("--repo", default=os.getcwd(), help="Path to repo (default: cwd)")
    args = parser.parse_args()
    ask(" ".join(args.query), args.repo)
