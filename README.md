# claude-model-benchmark

A Claude Code skill that runs a standardized **10-test** benchmark against any AI model and generates a visual HTML report — score, radar chart, timing, and per-test breakdown.

**Use it to compare models side by side**: run once per model, open both `report.html` files.

---

## What It Tests

| # | Test | Dimension | Max Score |
|---|------|-----------|-----------|
| 1 | Read a real Python file, answer 5 factual questions | Code Understanding | 10 |
| 2 | Find 5 intentional bugs in financial code | Bug Detection | 10 |
| 3 | Multi-step tool use: count files, find longest, extract imports, write JSON | Tool Use | 10 |
| 4 | Write a two-stage DCF function with type hints; run against 10 test cases | Code Generation | 10 |
| 5 | Generate a markdown table with computed columns (PEG-based ratings) | Structured Output | 10 |
| 6 | Design a SEC EDGAR monitoring system: components, stack, failure modes | Planning & Reasoning | 10 |
| 7 | Retrieve 5 scattered facts from a ~50KB financial document | Long Context | 10 |
| 8 | Resist hallucination: missing file + fake Python library | Hallucination Resistance | 10 |
| 9 | Write a Python function with Chinese identifiers and docstring | Multilingual | 10 |
| 10 | Follow 10 exact constraints to create a Python file | Instruction Following | 10 |

**Total: 100 points.** Grade: >=90% = A+, >=80% = A, >=70% = B+, >=60% = B, >=50% = C, <50% = D.

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
2. Run all 10 tests sequentially
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
├── generate_report.py    # report renderer
├── buggy_code.py         # temp file used in Test 2
├── dcf_model.py          # model-generated code from Test 4
├── test_dcf.py           # test harness for Test 4
├── long_context_10k.txt  # 50KB document for Test 7
├── sharpe_cn.py          # Chinese-identifier code from Test 9
└── analysis.py           # constraint-checking code from Test 10
```

Open `report.html` in any browser. To compare two models, open both files side by side.

---

## Design Principles

- **Objective scoring**: all points are tied to verifiable facts (grep results, code that runs, numbers that match)
- **No rubric cheating**: the model answers first, scoring rubric is only consulted after
- **Reproducible**: prompts are hardcoded — same prompts every run, every model
- **Zero-dependency report**: HTML uses inline CSS + pure SVG radar chart, no CDN
- **10 dimensions**: expanded from the original 6 to cover long context, hallucination resistance, multilingual, and instruction following

---

## Repo Structure

```
claude-model-benchmark/
├── skill.md                  # the Claude Code skill definition (v2, 10 tests)
├── sample/
│   └── financial_model.py    # target file for Test 1 (Code Understanding)
└── README.md
```

---

## Changelog

### v2 (April 2026)
- Expanded from 6 to 10 tests (60 -> 100 points)
- Added: Long Context Processing (Test 7), Hallucination Resistance (Test 8), Multilingual Capability (Test 9), Instruction Following Precision (Test 10)
- All rubrics made fully objective and verifiable
- Added token efficiency metadata tracking

### v1 (April 2026)
- Initial release with 6 tests / 60 points

---

## Contributing

PRs welcome. The most valuable contributions:
- Additional test cases (keep the same rubric structure)
- Translations of test prompts for non-English model evaluation
- A script to aggregate multiple `results.json` files into a comparison table

---

## License

MIT
