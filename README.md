# claude-model-benchmark

A Claude Code skill that runs a standardized 6-test benchmark against any AI model and generates a visual HTML report — score, radar chart, timing, and per-test breakdown.

**Use it to compare models side by side**: run once per model, open both `report.html` files.

---

## What It Tests

| # | Test | Dimension | Max Score |
|---|------|-----------|-----------|
| 1 | Read a real Python file, answer 5 factual questions | Code Understanding | 10 |
| 2 | Find 5 intentional bugs in financial code | Bug Detection | 10 |
| 3 | Multi-step tool use: count files, find longest, extract imports, write JSON | Tool Use | 10 |
| 4 | Write a two-stage DCF function with type hints; actually run it | Code Generation | 10 |
| 5 | Generate a markdown table with computed columns (PEG-based ratings) | Structured Output | 10 |
| 6 | Design a SEC EDGAR monitoring system: components, stack, failure modes | Planning & Reasoning | 10 |

**Total: 60 points.**  Grade: ≥90% = A+, ≥80% = A, ≥70% = B+, ≥60% = B, ≥50% = C, <50% = D.

---

## Installation

```bash
# 1. Clone
git clone https://github.com/jjd200099-crypto/claude-model-benchmark.git

# 2. Copy into Claude Code skills directory
cp -r claude-model-benchmark ~/.claude/skills/model-benchmark
```

That's it. No external dependencies required for the benchmark itself.  
(`openpyxl` is imported in the sample file but not executed during tests.)

---

## Usage

In any Claude Code session, type:

```
/model-benchmark
```

Claude will:
1. Ask you to label the model (e.g., "Claude Sonnet 4.6", "GPT-4o")
2. Run all 6 tests sequentially
3. Score each test objectively (grep + code execution for verification)
4. Write `results.json` + `report.html` to `~/Downloads/model-benchmark-results/<timestamp>/`
5. Open the report automatically

---

## Output

Each run produces:

```
~/Downloads/model-benchmark-results/20260422_143000/
├── results.json          # raw scores + timing
├── report.html           # standalone visual report (no server needed)
├── generate_report.py    # report renderer (re-run after editing template)
└── buggy_code.py         # temp file used in Test 2
```

Open `report.html` in any browser. To compare two models, open both files side by side.

---

## Design Principles

- **Objective scoring**: most points are tied to verifiable facts (grep results, code that runs, numbers that match)
- **No rubric cheating**: the model answers first, scoring rubric is only consulted after
- **Reproducible**: prompts are hardcoded — same prompts every run, every model
- **Zero-dependency report**: HTML uses inline CSS + pure SVG radar chart, no CDN

---

## Repo Structure

```
claude-model-benchmark/
├── skill.md              # the Claude Code skill definition
├── sample/
│   └── financial_model.py    # target file for Test 1 (Code Understanding)
└── README.md
```

---

## Contributing

PRs welcome. The most valuable contributions:
- Additional test cases (keep the same rubric structure)
- Translations of test prompts for non-English model evaluation
- A script to aggregate multiple `results.json` files into a comparison table

---

## License

MIT
