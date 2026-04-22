# Model Benchmark — AI Agent Capability Testing

One-click agent capability benchmark. Runs standardized tests against the current model, scores each dimension quantitatively, and generates a standalone HTML report for side-by-side comparison across models.

**Trigger**: User asks to benchmark a model, compare models, test model capabilities, or run agent tests (e.g., "跑模型测试", "benchmark this model", "测试一下这个模型", "对比模型能力")

## Installation

1. Clone this repo and copy the skill into your Claude Code skills directory:

```bash
git clone https://github.com/jjd200099-crypto/claude-model-benchmark.git
cp -r claude-model-benchmark ~/.claude/skills/model-benchmark
```

2. The benchmark uses `~/.claude/skills/model-benchmark/sample/financial_model.py` as the target file for Test 1. No other dependencies required.

---

## How It Works

1. Run a battery of 6 standardized tests (each scored 0–10)
2. Capture timing, correctness, and quality metrics
3. Save raw results as JSON
4. Generate a visual HTML report with radar chart + detailed breakdown

---

## Benchmark Execution

### Step 0: Setup

```bash
BENCH_DIR="$HOME/Downloads/model-benchmark-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BENCH_DIR"
SKILL_DIR="$HOME/.claude/skills/model-benchmark"
echo "Benchmark output: $BENCH_DIR"
```

Record the model identifier. Ask the user what to label this model (e.g., "Claude Opus 4", "DeepSeek V3", "GPT-4o"). Store it as `MODEL_NAME`.

### Step 1: Run All 6 Tests

Run each test sequentially. For every test, record:
- `start_time` and `end_time` (wall clock seconds)
- `score` (0–10, criteria defined per test)
- `details` (what went right/wrong)
- `output` (the actual model output, truncated to 2000 chars)

---

#### Test 1: Code Understanding (读代码能力)

Read `$SKILL_DIR/sample/financial_model.py` and answer these 5 questions:

1. How many Excel tabs does this script create? (exact number)
2. What hex color is used for input assumption cells?
3. What are the scenario names defined in the `SCENARIOS` dict? (list all)
4. What is the terminal growth rate assumption? (exact value)
5. What is the label of the cell described as the "final DCF output"?

**Scoring**: 2 points per correct answer. Verify each answer by grep/reading the file yourself.

**Answer key** (for scoring only — do not read before answering):
1. 7 tabs
2. `FFF2CC`
3. Base Case, Bull Case, Bear Case
4. `0.03`
5. `Intrinsic Value Per Share`

---

#### Test 2: Bug Detection (找 Bug 能力)

Create a temporary Python file with these **5 intentional bugs** (write to `$BENCH_DIR/buggy_code.py`):

```python
import json
from datetime import datetime, timedelta

def calculate_portfolio_returns(holdings):
    """Calculate weighted portfolio return."""
    total_weight = 0
    portfolio_return = 0
    for h in holdings:
        weight = h['value'] / sum(x['value'] for x in holdings)
        portfolio_return += weight * h['return']
        total_weight += weight
    # Bug 1: Should check total_weight == 1.0 but doesn't validate
    return portfolio_return

def parse_earnings_date(date_str):
    """Parse earnings date in various formats."""
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    # Bug 2: Returns None silently instead of raising an error
    return None

def get_trading_days(start, end):
    """Get number of trading days between two dates."""
    days = []
    current = start
    while current < end:  # Bug 3: Should be <= end
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days

def merge_price_data(prices_a, prices_b):
    """Merge two price series by date."""
    merged = {}
    for date, price in prices_a.items():
        merged[date] = {'a': price}
    for date, price in prices_b.items():
        merged[date]['b'] = price  # Bug 4: KeyError if date not in prices_a
    return merged

def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
    """Calculate annualized Sharpe ratio."""
    import statistics
    mean_return = statistics.mean(returns)
    std_return = statistics.stdev(returns)
    # Bug 5: Not annualizing - should multiply by sqrt(252) for daily returns
    return (mean_return - risk_free_rate) / std_return
```

Ask the model: "Review this code. Find ALL bugs and explain each one."

**Scoring**:
- 2 points per bug correctly identified (max 10)
- -1 point per false positive (minimum 0 total)

---

#### Test 3: Multi-Step Tool Use (多步工具调用)

Ask the model to perform this exact task using the skill directory as the target project:

"In the directory `$SKILL_DIR`:
1. Count the total number of Python files
2. Find which Python file has the most lines of code
3. List all external packages imported across all Python files (deduplicated)
4. Create a file called `$BENCH_DIR/project_stats.json` with all findings"

**Scoring**:
- Correct Python file count: 2 points
- Correct identification of longest file: 2 points
- Complete import list (>80% accuracy): 3 points
- Valid JSON output file created: 3 points

Verify all answers independently with bash/grep.

---

#### Test 4: Financial Code Generation (金融代码生成)

Ask the model:

"Write a Python function that takes a list of quarterly EPS values and a discount rate, and performs a simple two-stage DCF to estimate intrinsic value per share. Stage 1: 5 years of growth at the trailing growth rate. Stage 2: terminal value using Gordon Growth Model with 3% perpetual growth. Return the intrinsic value. Include type hints and a docstring."

**Scoring**:
- Syntactically valid Python (runs without error): 2 points
- Correct DCF math (discount factors, terminal value formula): 3 points
- Handles edge cases (negative growth, zero EPS): 2 points
- Type hints + docstring present: 1 point
- Code is clean and readable: 2 points

Test by actually running the generated code with sample inputs: `eps=[2.0, 2.2, 2.5, 2.8]`, `discount_rate=0.10`

---

#### Test 5: Structured Output (结构化输出)

Ask the model:

"Given this data, produce a markdown table comparing these companies:

| Company | Revenue ($B) | YoY Growth | Gross Margin | P/E | Market Cap ($B) |
NVDA: 130.5, +114%, 75%, 55x, 3200
MSFT: 245.1, +16%, 70%, 35x, 3100
GOOGL: 350.0, +14%, 57%, 25x, 2100
AMD: 25.8, +8%, 52%, 120x, 200

Add a row for sector averages. Sort by YoY growth descending. Add a 'Rating' column (Overweight/Equal-weight/Underweight) based on growth-adjusted P/E (PEG ratio < 1.5 = Overweight, 1.5-2.5 = Equal-weight, > 2.5 = Underweight)."

**Scoring**:
- Correct markdown table syntax: 2 points
- Data accuracy (all numbers match): 2 points
- Correct sorting: 1 point
- Average row calculated correctly: 2 points
- PEG-based ratings correct: 3 points

---

#### Test 6: Planning & Reasoning (规划推理)

Ask the model:

"I want to build a system that monitors SEC EDGAR for new 10-K filings from a watchlist of 50 companies, automatically extracts the Risk Factors section, diffs it against the previous year's filing, and sends a Slack alert with a summary of changes. Design the architecture: what components, what tech stack, what are the failure modes, and what's the estimated complexity for each component (S/M/L)? Give me a concrete implementation plan I could start coding tomorrow."

**Scoring**:
- Identifies all major components (monitor, parser, differ, notifier): 2 points
- Reasonable tech stack choices with justification: 2 points
- Addresses failure modes (rate limits, parsing errors, missing filings): 2 points
- Complexity estimates are realistic: 2 points
- Plan is actionable (not just abstract): 2 points

---

### Step 2: Calculate Scores & Generate Results JSON

After all 6 tests, create `$BENCH_DIR/results.json`:

```json
{
  "model_name": "<MODEL_NAME>",
  "timestamp": "<ISO timestamp>",
  "total_score": <sum of all scores>,
  "max_score": 60,
  "percentage": <total/60 * 100>,
  "tests": [
    {
      "id": 1,
      "name": "Code Understanding",
      "name_zh": "读代码能力",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<what was right/wrong>",
      "output_snippet": "<truncated output>"
    }
  ]
}
```

### Step 3: Generate HTML Report

Create and run `$BENCH_DIR/generate_report.py`:

```python
#!/usr/bin/env python3
"""Generate a visual HTML benchmark report from results JSON."""
import json, sys, os, math
from datetime import datetime

def generate_report(results_file, output_file):
    with open(results_file) as f:
        data = json.load(f)

    tests = data['tests']
    model = data['model_name']
    total = data['total_score']
    pct = data['percentage']
    ts = data['timestamp']

    labels = [t['name_zh'] for t in tests]
    scores = [t['score'] for t in tests]
    times = [t['time_seconds'] for t in tests]

    def score_color(s):
        if s >= 8: return '#22c55e'
        if s >= 6: return '#eab308'
        if s >= 4: return '#f97316'
        return '#ef4444'

    def grade(pct):
        if pct >= 90: return 'A+'
        if pct >= 80: return 'A'
        if pct >= 70: return 'B+'
        if pct >= 60: return 'B'
        if pct >= 50: return 'C'
        return 'D'

    test_rows = ''
    for t in tests:
        color = score_color(t['score'])
        bar_width = t['score'] * 10
        test_rows += f"""
        <tr>
          <td class="test-name">
            <div class="test-id">T{t['id']}</div>
            <div>
              <div class="test-title">{t['name']}</div>
              <div class="test-subtitle">{t['name_zh']}</div>
            </div>
          </td>
          <td class="score-cell">
            <div class="score-bar-bg">
              <div class="score-bar" style="width:{bar_width}%;background:{color}"></div>
            </div>
            <span class="score-num" style="color:{color}">{t['score']}/10</span>
          </td>
          <td class="time-cell">{t['time_seconds']:.1f}s</td>
          <td class="detail-cell">{t['details']}</td>
        </tr>"""

    cx, cy, r = 150, 150, 120
    n = len(scores)
    points_score = []
    label_positions = []
    grid_lines = ''

    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        sr = r * scores[i] / 10
        sx = cx + sr * math.cos(angle)
        sy = cy + sr * math.sin(angle)
        points_score.append(f"{sx},{sy}")
        lx = cx + (r + 25) * math.cos(angle)
        ly = cy + (r + 25) * math.sin(angle)
        anchor = 'middle'
        if math.cos(angle) > 0.3: anchor = 'start'
        elif math.cos(angle) < -0.3: anchor = 'end'
        label_positions.append((lx, ly, labels[i], anchor))

    for frac in [0.25, 0.5, 0.75, 1.0]:
        gr = r * frac
        grid_pts = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            grid_pts.append(f"{cx + gr * math.cos(angle)},{cy + gr * math.sin(angle)}")
        grid_lines += f'<polygon points="{" ".join(grid_pts)}" fill="none" stroke="#e5e7eb" stroke-width="1"/>\n'

    axis_lines = ''
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{cx + r * math.cos(angle)}" y2="{cy + r * math.sin(angle)}" stroke="#e5e7eb" stroke-width="1"/>\n'

    label_els = ''.join(
        f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="12" fill="#374151">{text}</text>\n'
        for lx, ly, text, anchor in label_positions
    )

    radar_svg = f'''<svg viewBox="0 0 300 300" width="300" height="300">
      {grid_lines}{axis_lines}
      <polygon points="{' '.join(points_score)}" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="2"/>
      {label_els}
    </svg>'''

    grade_val = grade(pct)
    grade_color = score_color(total / 6)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Model Benchmark — {model}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif;background:#f8fafc;color:#1e293b;line-height:1.6}}
  .container{{max-width:960px;margin:0 auto;padding:40px 24px}}
  .header{{text-align:center;margin-bottom:48px}}
  .header h1{{font-size:28px;font-weight:700;margin-bottom:8px}}
  .header .subtitle{{color:#64748b;font-size:14px}}
  .summary{{display:flex;gap:24px;margin-bottom:48px;justify-content:center;flex-wrap:wrap}}
  .summary-card{{background:white;border-radius:12px;padding:24px 32px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08);min-width:160px}}
  .summary-card .label{{font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
  .summary-card .value{{font-size:36px;font-weight:700}}
  .summary-card .sub{{font-size:13px;color:#94a3b8;margin-top:4px}}
  .section{{background:white;border-radius:12px;padding:32px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}}
  .section h2{{font-size:18px;font-weight:600;margin-bottom:24px;padding-bottom:12px;border-bottom:1px solid #f1f5f9}}
  .radar-container{{display:flex;justify-content:center;margin:20px 0}}
  table{{width:100%;border-collapse:collapse}}
  th{{text-align:left;font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;padding:8px 12px;border-bottom:2px solid #f1f5f9}}
  td{{padding:16px 12px;border-bottom:1px solid #f8fafc;vertical-align:top}}
  .test-name{{display:flex;align-items:center;gap:12px;min-width:180px}}
  .test-id{{background:#f1f5f9;color:#64748b;border-radius:6px;padding:4px 8px;font-size:12px;font-weight:600}}
  .test-title{{font-weight:600;font-size:14px}}
  .test-subtitle{{color:#94a3b8;font-size:12px}}
  .score-cell{{min-width:160px}}
  .score-bar-bg{{background:#f1f5f9;border-radius:4px;height:8px;margin-bottom:4px}}
  .score-bar{{height:8px;border-radius:4px}}
  .score-num{{font-weight:700;font-size:14px}}
  .time-cell{{color:#64748b;font-size:13px;white-space:nowrap}}
  .detail-cell{{color:#475569;font-size:13px;max-width:300px}}
  .footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:48px}}
  .compare-hint{{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin-top:24px;font-size:13px;color:#1e40af}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Agent Capability Benchmark</h1>
    <div class="subtitle">{model} &mdash; {ts}</div>
  </div>
  <div class="summary">
    <div class="summary-card"><div class="label">Model</div><div class="value" style="font-size:20px">{model}</div></div>
    <div class="summary-card"><div class="label">Total Score</div><div class="value" style="color:{grade_color}">{total}/60</div><div class="sub">{pct:.1f}%</div></div>
    <div class="summary-card"><div class="label">Grade</div><div class="value" style="color:{grade_color}">{grade_val}</div></div>
    <div class="summary-card"><div class="label">Avg Time</div><div class="value" style="font-size:24px">{sum(times)/len(times):.1f}s</div><div class="sub">per test</div></div>
  </div>
  <div class="section"><h2>Capability Radar</h2><div class="radar-container">{radar_svg}</div></div>
  <div class="section">
    <h2>Detailed Results</h2>
    <table>
      <thead><tr><th>Test</th><th>Score</th><th>Time</th><th>Details</th></tr></thead>
      <tbody>{test_rows}</tbody>
    </table>
  </div>
  <div class="compare-hint">To compare models: run this benchmark with different model configurations, then open both report.html files side by side. Each is a standalone file — no server needed.</div>
  <div class="footer">Generated by /model-benchmark &mdash; <a href="https://github.com/jjd200099-crypto/claude-model-benchmark">github.com/jjd200099-crypto/claude-model-benchmark</a></div>
</div>
</body>
</html>"""

    with open(output_file, 'w') as f:
        f.write(html)
    print(f"Report saved: {output_file}")

if __name__ == '__main__':
    results_file = sys.argv[1]
    output_file = os.path.join(os.path.dirname(results_file), 'report.html')
    generate_report(results_file, output_file)
```

Run it:
```bash
python3 "$BENCH_DIR/generate_report.py" "$BENCH_DIR/results.json"
```

### Step 4: Present Results

1. Print a summary table to the terminal showing all 6 test scores
2. Tell the user: "HTML report saved to: `$BENCH_DIR/report.html`"
3. Open the report: `open "$BENCH_DIR/report.html"`
4. Remind: "Run this benchmark again with a different model config to compare side by side."

---

## Grading Scale

| Score | Grade | Meaning |
|-------|-------|---------|
| 54–60 (≥90%) | A+ | Excellent across all dimensions |
| 48–53 (80–89%) | A  | Strong, minor gaps |
| 42–47 (70–79%) | B+ | Good, 1–2 weak dimensions |
| 36–41 (60–69%) | B  | Average, clear weaknesses |
| 30–35 (50–59%) | C  | Below average |
| <30 (<50%)    | D  | Failing |

---

## Important Rules

- **Objectivity**: Score strictly by the rubrics above. Do not inflate scores.
- **Reproducibility**: Use the exact same test prompts every time. Do not modify prompts between runs.
- **Timing**: Time only the model's "thinking + output" portion, not file I/O or verification.
- **Self-testing**: You ARE the model being tested. Run each prompt as if seeing it for the first time, then score your output honestly.
- **Verification**: Always verify answers independently (grep, run code, manual check) before scoring.
- **No cheating**: Do not consult the answer key or rubric before answering each test. Process the prompt first, capture your output, THEN score it.
