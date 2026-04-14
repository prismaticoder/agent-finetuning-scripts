#!/usr/bin/env python3
"""
clean_dataset.py
Merge JSONL files, dedup, and filter low-quality pairs.

Usage: python clean_dataset.py pairs_pr.jsonl pairs_docblock.jsonl --out dataset.jsonl
"""

import json
import sys

MIN_PROMPT_LEN = 50
MIN_COMPLETION_LEN = 80

def clean(input_files, out_path):
    seen = set()
    clean_pairs = []

    for fpath in input_files:
        with open(fpath) as f:
            for line in f:
                try:
                    pair = json.loads(line)
                except json.JSONDecodeError:
                    continue
                messages = pair.get("messages", [])
                if len(messages) < 2:
                    continue
                prompt = messages[0].get("content", "").strip()
                completion = messages[1].get("content", "").strip()

                if len(prompt) < MIN_PROMPT_LEN or len(completion) < MIN_COMPLETION_LEN:
                    continue

                key = (prompt[:80], completion[:80])
                if key in seen:
                    continue
                seen.add(key)
                clean_pairs.append({"messages": messages})

    print(f"Final dataset: {len(clean_pairs)} pairs")
    with open(out_path, "w") as f:
        for pair in clean_pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--out", default="dataset.jsonl")
    args = parser.parse_args()
    clean(args.inputs, args.out)
