#!/usr/bin/env python3
"""
extract_docblock_pairs.py
Extracts (docstring/docblock, function body) pairs from Python and TypeScript files.

Usage: python extract_docblock_pairs.py --src ./src --out pairs_docblock.jsonl
"""

import os
import re
import json
import argparse

# --- Python: docstring + function body ---
PYTHON_FUNC_RE = re.compile(
    r'def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]+)?:\s*\n'
    r'(\s+"""[\s\S]*?""")\s*\n'  # docstring
    r'([\s\S]*?)(?=\ndef |\nclass |\Z)',  # body
    re.MULTILINE
)

# --- TypeScript/JS: JSDoc + function ---
TS_FUNC_RE = re.compile(
    r'(/\*\*[\s\S]*?\*/)\s*\n'  # JSDoc block
    r'\s*(?:export\s+)?(?:async\s+)?function\s+\w+[^{]*\{([\s\S]*?)\n\}',
    re.MULTILINE
)

def extract_from_python(content):
    pairs = []
    for match in PYTHON_FUNC_RE.finditer(content):
        fn_name, docstring, body = match.groups()
        docstring = docstring.strip().strip('"""').strip()
        body = body.strip()
        if len(docstring) > 20 and len(body) > 20:
            pairs.append({
                "messages": [
                    {"role": "user", "content": f"Implement a Python function based on this description:\n{docstring}"},
                    {"role": "assistant", "content": body},
                ]
            })
    return pairs

def extract_from_typescript(content):
    pairs = []
    for match in TS_FUNC_RE.finditer(content):
        jsdoc, body = match.groups()
        jsdoc = re.sub(r'/\*\*|\*/|^\s*\*', '', jsdoc, flags=re.MULTILINE).strip()
        body = body.strip()
        if len(jsdoc) > 20 and len(body) > 20:
            pairs.append({
                "messages": [
                    {"role": "user", "content": f"Implement a TypeScript function based on this description:\n{jsdoc}"},
                    {"role": "assistant", "content": body},
                ]
            })
    return pairs

def extract_all(src_dir, out_path):
    all_pairs = []
    for root, _, files in os.walk(src_dir):
        # Skip common auto-generated dirs
        if any(skip in root for skip in ["node_modules", ".git", "__pycache__", "dist", "build"]):
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath).read()
            except Exception:
                continue
            if fname.endswith(".py"):
                all_pairs.extend(extract_from_python(content))
            elif fname.endswith((".ts", ".tsx", ".js")):
                all_pairs.extend(extract_from_typescript(content))

    # Deduplicate by prompt
    seen = set()
    deduped = []
    for p in all_pairs:
        key = p["prompt"][:100]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    print(f"Extracted {len(deduped)} docblock pairs.")
    with open(out_path, "w") as f:
        for pair in deduped:
            f.write(json.dumps(pair) + "\n")
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="./src")
    parser.add_argument("--out", default="pairs_docblock.jsonl")
    args = parser.parse_args()
    extract_all(args.src, args.out)
