# agent-finetuning-scripts

A collection of scripts for extracting training data from your codebase and preparing it for LLM finetuning. Built as a companion to the article **[How To Build Your Own Coding Agent](#)**.

The idea is simple: your codebase already contains high-quality examples of how you write code — in your PR descriptions, your docblocks, your commit history. These scripts help you extract that signal into structured (prompt, completion) pairs that you can use to finetune a coding model on your own stack.

---

## Scripts

### `extract_pr_pairs.py`
Extracts training pairs from merged pull requests using the GitHub CLI.

- **Input:** A GitHub repo with merged PRs that have meaningful descriptions
- **Output:** A JSONL file where each line is `{"prompt": "<PR title + description>", "completion": "<diff>"}`
- **Why it works:** A merged PR implies the code was good enough to ship. The description is the intent; the diff is the implementation. That's exactly the shape of a useful training pair.

```bash
python extract_pr_pairs.py --repo your-org/your-repo --limit 300 --out pairs_pr.jsonl
```

**Requirements:** `gh` CLI installed and authenticated (`gh auth login`)

---

### `extract_docblock_pairs.py`
Walks your codebase and extracts (docstring/JSDoc, function body) pairs from Python and TypeScript/JavaScript files.

- **Input:** A source directory
- **Output:** A JSONL file where each line is `{"prompt": "<docblock description>", "completion": "<function body>"}`
- **Why it works:** If you write good documentation, you've already described what each function does. The body is the ground truth answer.

```bash
python extract_docblock_pairs.py --src ./src --out pairs_docblock.jsonl
```

---

### `clean_dataset.py`
Merges multiple JSONL pair files, deduplicates, and filters out low-quality pairs based on minimum length thresholds.

- **Input:** One or more JSONL files produced by the extractors above
- **Output:** A single clean JSONL file ready for upload to your finetuning platform

```bash
python clean_dataset.py pairs_pr.jsonl pairs_docblock.jsonl --out dataset.jsonl
```

---

## Recommended Workflow

```bash
# 1. Extract from PR history
python extract_pr_pairs.py --repo your-org/your-repo --limit 300 --out pairs_pr.jsonl

# 2. Extract from docblocks
python extract_docblock_pairs.py --src ./src --out pairs_docblock.jsonl

# 3. Merge and clean
python clean_dataset.py pairs_pr.jsonl pairs_docblock.jsonl --out dataset.jsonl
```

Your `dataset.jsonl` is now ready to upload to [Tinker](https://thinkingmachines.ai/tinker/) (or any other finetuning platform that accepts JSONL prompt/completion pairs).

---

## A Note on Data Quality

These scripts are only as good as your codebase's maintenance habits. Finetuning amplifies whatever patterns exist in your training data — consistent naming, meaningful PR descriptions, and well-documented functions will produce a better model than noisy data ever could.

If your dataset is smaller than ~300 pairs after cleaning, focus on improving your codebase's documentation first, then re-run the extractors.

---

## Requirements

- Python 3.8+
- `gh` CLI (for `extract_pr_pairs.py`) — install via `brew install gh` or the [official docs](https://cli.github.com)
