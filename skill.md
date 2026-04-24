# Model Benchmark — AI Agent Capability Testing

One-click agent capability benchmark. Runs 10 standardized tests against the current model, scores each dimension quantitatively (fully objective rubrics), and generates a standalone HTML report for side-by-side comparison across models.

Trigger: User asks to benchmark a model, compare models, test model capabilities, run agent tests (e.g., "跑模型测试", "benchmark this model", "测试一下这个模型", "对比模型能力")

## How It Works

1. Run a battery of 10 standardized tests (each scored 0-10)
2. Capture timing, correctness, and token efficiency metadata
3. Save raw results as JSON
4. Generate a visual HTML report with radar chart + detailed breakdown

## Benchmark Execution

### Step 0: Setup

```bash
# Create output directory with timestamp
BENCH_DIR="$HOME/Downloads/model-benchmark-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BENCH_DIR"
echo "Benchmark output: $BENCH_DIR"
```

Record the model identifier. Ask the user what to label this model (e.g., "Claude Opus", "DeepSeek V3", "GPT-4o"). Store it as `MODEL_NAME`.

### Step 1: Run All 10 Tests

Run each test sequentially. For every test, record:
- `start_time` and `end_time` (wall clock seconds)
- `score` (0-10, criteria defined per test)
- `details` (what went right/wrong)
- `output` (the actual model output, truncated to 2000 chars)

---

#### Test 1: Code Understanding (读代码能力)

Read `~/.claude/skills/model-benchmark/sample/financial_model.py` and answer these 5 questions:

1. How many Excel tabs (sheets) does this script create? (exact number)
2. What is the hex color code used for input/assumption cells?
3. What are the scenario names used? (list all three)
4. What is the terminal growth rate assumption? (find the exact value)
5. What financial metric does the DCF sheet calculate as its final output?

**Scoring**: 2 points per correct answer. Verify each answer by grep/reading the file yourself.

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

Ask the model to perform this exact task:

"In the current working directory (the project you're in):
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

#### Test 4: Code Generation (代码生成) — Objective

Ask the model:

"Write a Python function `two_stage_dcf(eps_list: list[float], discount_rate: float) -> dict` that:
- Takes a list of quarterly EPS values and a discount rate
- Performs a two-stage DCF: Stage 1 = 5 years of growth at trailing growth rate; Stage 2 = terminal value via Gordon Growth Model with 3% perpetual growth
- Returns a dict with keys: `intrinsic_value`, `stage1_npv`, `terminal_npv`, `trailing_growth_rate`
- Includes type hints and a docstring"

Save the generated code to `$BENCH_DIR/dcf_model.py`. Then create and run this test harness:

```python
# $BENCH_DIR/test_dcf.py
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from dcf_model import two_stage_dcf

test_cases = [
    # (eps_list, discount_rate, expected_range)
    # Test 1: Normal case — eps=[2.0, 2.2, 2.5, 2.8], rate=0.10
    ([2.0, 2.2, 2.5, 2.8], 0.10, (180, 250)),
    # Test 2: Flat EPS — no growth
    ([3.0, 3.0, 3.0, 3.0], 0.08, (100, 200)),
    # Test 3: Negative growth
    ([5.0, 4.5, 4.0, 3.5], 0.12, (50, 120)),
    # Test 4: Single quarter (edge case — should handle gracefully or raise clear error)
    ([1.5], 0.10, None),
    # Test 5: Zero EPS
    ([0.0, 0.0, 0.0, 0.0], 0.10, (0, 10)),
    # Test 6: High discount rate
    ([2.0, 2.2, 2.5, 2.8], 0.25, (30, 80)),
    # Test 7: Very low discount rate
    ([2.0, 2.2, 2.5, 2.8], 0.04, (500, 1500)),
    # Test 8: Negative EPS
    ([-1.0, -0.5, -0.2, 0.1], 0.10, (-50, 30)),
    # Test 9: Returns dict with correct keys
    None,  # special: just check keys
    # Test 10: Type hints present
    None,  # special: just check annotations
]

results = []
for i, tc in enumerate(test_cases):
    if tc is None:
        continue
    eps, rate, expected = tc
    try:
        result = two_stage_dcf(eps, rate)
        passed = False
        if expected is not None:
            passed = expected[0] <= result['intrinsic_value'] <= expected[1]
        if not passed and expected is not None:
            results.append((i+1, False, f"Expected {expected[0]}-{expected[1]}, got {result['intrinsic_value']:.2f}"))
        else:
            results.append((i+1, True, f"Value: {result['intrinsic_value']:.2f}"))
    except Exception as e:
        if expected is None:
            results.append((i+1, True, f"Graceful error: {e}"))
        else:
            results.append((i+1, False, f"Exception: {e}"))

# Test 9: Check return keys
try:
    r = two_stage_dcf([2.0, 2.2, 2.5, 2.8], 0.10)
    required_keys = {'intrinsic_value', 'stage1_npv', 'terminal_npv', 'trailing_growth_rate'}
    keys_ok = required_keys.issubset(r.keys())
    results.append((9, keys_ok, f"Keys: {list(r.keys())}"))
except Exception as e:
    results.append((9, False, f"Exception: {e}"))

# Test 10: Check type hints + docstring
import inspect
sig = inspect.signature(two_stage_dcf)
has_hints = all(p.annotation != inspect.Parameter.empty for p in sig.parameters.values())
has_return = sig.return_annotation != inspect.Signature.empty
has_docstring = two_stage_dcf.__doc__ is not None
all_ok = has_hints and has_return and has_docstring
results.append((10, all_ok, f"Type hints: {has_hints}, Return: {has_return}, Docstring: {has_docstring}"))

passed = sum(1 for _, p, _ in results if p)
print(f"PASSED: {passed}/10")
print(json.dumps(results, indent=2))
```

**Scoring**: 1 point per passing test case (max 10). Run the harness and count passes.

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

#### Test 6: Planning & Reasoning (规划推理) — Objective

Ask the model:

"I want to build a system that monitors SEC EDGAR for new 10-K filings from a watchlist of 50 companies, automatically extracts the Risk Factors section, diffs it against the previous year's filing, and sends a Slack alert with a summary of changes. Design the architecture: what components, what tech stack, what are the failure modes, and what's the estimated complexity for each component (S/M/L)? Give me a concrete implementation plan I could start coding tomorrow."

**Scoring** (1 point each, verified by reading the model's response against this checklist):

1. Identifies a filing monitor/scraper component
2. Identifies a document parser/extractor component
3. Identifies a diff/comparison engine component
4. Identifies a notification/alert component
5. Names at least one specific technology per component (e.g., "Python + SEC EDGAR API", not just "some scraper")
6. Mentions SEC EDGAR rate limiting as a failure mode
7. Mentions HTML/PDF parsing inconsistency as a failure mode
8. Mentions missing or amended filings as a failure mode
9. Assigns complexity estimates (S/M/L) to each component
10. Provides a concrete execution sequence (step 1, 2, 3...) beyond abstract description

---

#### Test 7: Long Context Processing (长上下文处理)

Generate a ~50KB test file:

```bash
python3 -c "
import random, string
# Generate a dense financial document with embedded answers
sections = []
# Section 1: Company Overview (~8KB)
overview = 'COMPANY OVERVIEW\n' + '='*60 + '\n'
overview += 'Galaxy Semiconductor Inc. (Ticker: GXY)\n'
overview += 'Founded: 2018 | HQ: Austin, TX | Employees: 4,200\n'
overview += 'The company specializes in advanced packaging for AI accelerators.\n'
overview += 'Q3 2025 revenue reached \$2.847 billion, up from \$1.923 billion in Q3 2024.\n'
overview += 'International sales accounted for 67.3% of total revenue.\n'
overview += ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 200)  # padding
sections.append(overview)

# Section 2: Risk Factors (~12KB)
risks = 'RISK FACTORS\n' + '='*60 + '\n'
risks += '1. Supply Chain Concentration: 78% of substrate supply comes from 2 vendors in Taiwan.\n'
risks += '2. Customer Concentration: Top 3 customers account for 71.5% of revenue.\n'
risks += '3. The fab in Leixlip, Ireland operates at 92.4% utilization.\n'
risks += '4. Patent litigation with NovaLogic Inc. seeks \$340M in damages.\n'
risks += ('Market risks include foreign exchange, interest rate, and commodity price fluctuations. ' * 200)
sections.append(risks)

# Section 3: Financial Data (~10KB)
fin = 'FINANCIAL DATA\n' + '='*60 + '\n'
fin += 'FY2025 Revenue: \$11.2B | Gross Profit: \$7.84B | Net Income: \$3.36B\n'
fin += 'R&D Spending: \$2.464B (22% of revenue)\n'
fin += 'Free Cash Flow: \$1.904B | CapEx: \$2.8B\n'
fin += 'Total Debt: \$4.48B | Cash & Equivalents: \$5.6B\n'
fin += 'Shares Outstanding: 1.12B | Current Stock Price: \$84.50\n'
fin += 'Board members: Sarah Chen (Chair), Michael Okonkwo, Priya Patel, James Liu, Anna Kowalski\n'
fin += ('Detailed quarterly breakdowns and segment reporting would follow. ' * 300)
sections.append(fin)

# Section 4: MD&A (~10KB)
mda = \"MANAGEMENT DISCUSSION & ANALYSIS\n\" + '='*60 + '\n'
mda += 'Gross margin improved 320bps YoY driven by favorable product mix.\n'
mda += 'The company repurchased 24 million shares in FY2025 at an average price of \$72.30.\n'
mda += 'Restructuring charges of \$156M were recorded in Q2 related to the closure of the Penang facility.\n'
mda += 'The effective tax rate was 16.8%, down from 21.2% in FY2024.\n'
mda += 'Management guides FY2026 revenue to \$13.5-\$14.2B.\n'
mda += ('Forward-looking statements and detailed segment analysis follow. ' * 300)
sections.append(mda)

# Section 5: Notes (~10KB)
notes = 'NOTES TO FINANCIAL STATEMENTS\n' + '='*60 + '\n'
notes += 'Note 7: The company holds 3,400 BTC on its balance sheet at an average cost basis of \$41,200.\n'
notes += 'Note 12: Operating leases total \$890M with a weighted-average remaining term of 7.3 years.\n'
notes += 'Note 15: Related party transaction — \$42M paid to ChipDesign Ltd, where board member James Liu serves as advisor.\n'
notes += ('Detailed accounting policies and supplemental data follow. ' * 300)
sections.append(notes)

# Shuffle and write
random.shuffle(sections)
with open('$BENCH_DIR/long_context_10k.txt', 'w') as f:
    for s in sections:
        f.write(s)
        f.write('\n\n')

# Verify size
import os
size = os.path.getsize('$BENCH_DIR/long_context_10k.txt')
print(f'Generated file: {size} bytes ({size/1024:.1f} KB)')
"
```

Ask the model these 5 questions (the answers are scattered across different sections):

1. What was Galaxy Semiconductor's Q3 2025 revenue (exact figure)?
2. What percentage of substrate supply comes from Taiwan vendors?
3. How many shares did the company repurchase in FY2025 and at what average price?
4. What was the effective tax rate in FY2025 vs FY2024?
5. How many BTC does the company hold and at what average cost basis?

**Scoring**: 2 points per correct answer. Verify by grepping the generated file.

---

#### Test 8: Hallucination Resistance (幻觉抵抗)

**Part A (5 pts)**: Ask the model:
"Read the file `$BENCH_DIR/nonexistent_config.json` and tell me the value of the `api_endpoint` field."

The file does NOT exist. Score:
- 5 points if the model correctly reports the file doesn't exist (or attempts to read it and reports the error)
- 0 points if the model fabricates file content or an api_endpoint value

**Part B (5 pts)**: Ask the model:
"Use the `get_industry_beta` function from the Python library `finmesh` to fetch the beta for NVDA. Show me the code."

`finmesh` is not a real library. Score:
- 5 points if the model notes that `finmesh` is not a known/standard library, or attempts to pip install and reports failure
- 0 points if the model fabricates an API for `finmesh.get_industry_beta()` or pretends it exists

---

#### Test 9: Multilingual Capability (多语言能力)

Ask the model:

"请用 Python 写一个 function called `计算夏普比率` that:
1. Takes two parameters: `daily_returns` (List[float]) and `无风险利率` (float, default 0.03)
2. 计算年化收益率 (annualized return = mean * 252)
3. Compute the annualized Sharpe ratio: (annualized_return - 无风险利率) / (std * sqrt(252))
4. Return 一个 dict: `{'年化收益率': float, 'sharpe_ratio': float, 'annualized_volatility': float}`
5. 写中文 docstring
6. 加 type hints

Save the code to `$BENCH_DIR/sharpe_cn.py`, then verify it runs correctly."

**Scoring** (objective, verify each):
- Function name is `计算夏普比率` (Chinese): 2 points
- Parameter `无风险利率` correctly used: 2 points
- Math correct (run with `[0.001, -0.002, 0.003, 0.001, 0.0]` and verify against manual calc): 2 points
- Chinese docstring present: 2 points
- Returns dict with Chinese keys `年化收益率`, `sharpe_ratio`, `annualized_volatility`: 2 points

---

#### Test 10: Instruction Following Precision (指令遵循精度)

Ask the model:

"Create a file `$BENCH_DIR/analysis.py` with these EXACT specifications:

1. Must import pandas, numpy, and datetime (all three)
2. Define a class called `FinancialAnalyzer` (exact casing)
3. `__init__` must accept exactly 3 parameters: `ticker` (str), `start_date` (str, format YYYY-MM-DD), `end_date` (str, format YYYY-MM-DD)
4. Include a method `calculate_moving_average(self, window: int = 20)` that returns pd.Series
5. Include a property `trading_days` that returns an int
6. Add a `__repr__` that returns `f"Analyzer({self.ticker})"`
7. Include a static method `validate_ticker(ticker: str) -> bool` that returns True for 1-5 uppercase letters
8. Add module-level constant `CURRENT_YEAR = 2026`
9. File must start with a shebang `#!/usr/bin/env python3`
10. File must end with exactly one trailing newline

Save and verify each constraint independently."

**Scoring**: 1 point per satisfied constraint (max 10). Verify each by reading the file and checking.

---

### Token Efficiency Metadata (not scored)

After all 10 tests, capture token efficiency metadata. Since the benchmark is self-testing, these are approximate:

```bash
# Estimate output tokens (rough: 4 chars ≈ 1 token)
for f in "$BENCH_DIR"/*.py "$BENCH_DIR"/*.json "$BENCH_DIR"/*.txt 2>/dev/null; do
  [ -f "$f" ] && wc -c < "$f"
done | awk '{sum+=$1} END {printf "Estimated output chars: %d (~%d tokens)\n", sum, sum/4}'
```

Record in results.json metadata:
- `total_wall_clock_seconds`: sum of all test times
- `estimated_output_tokens`: total output chars / 4
- `tokens_per_second_estimate`: estimated_output_tokens / total_wall_clock_seconds
- Note: these are estimates, not precise token counts. For accurate token metrics, use the API's actual token counts.

---

### Step 2: Calculate Scores & Generate Results JSON

After all 10 tests, create `$BENCH_DIR/results.json`:

```json
{
  "model_name": "<MODEL_NAME>",
  "timestamp": "<ISO timestamp>",
  "total_score": <sum of all scores>,
  "max_score": 100,
  "percentage": <total/100 * 100>,
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
    },
    {
      "id": 2,
      "name": "Bug Detection",
      "name_zh": "找Bug能力",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<bugs found/missed>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 3,
      "name": "Multi-Step Tool Use",
      "name_zh": "多步工具调用",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<verification notes>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 4,
      "name": "Code Generation",
      "name_zh": "代码生成",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<test cases passed/failed>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 5,
      "name": "Structured Output",
      "name_zh": "结构化输出",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<verification notes>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 6,
      "name": "Planning & Reasoning",
      "name_zh": "规划推理",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<checklist items hit/missed>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 7,
      "name": "Long Context Processing",
      "name_zh": "长上下文处理",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<correct answers / 5>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 8,
      "name": "Hallucination Resistance",
      "name_zh": "幻觉抵抗",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<part A result, part B result>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 9,
      "name": "Multilingual Capability",
      "name_zh": "多语言能力",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<verification notes>",
      "output_snippet": "<truncated output>"
    },
    {
      "id": 10,
      "name": "Instruction Following",
      "name_zh": "指令遵循精度",
      "score": <0-10>,
      "max_score": 10,
      "time_seconds": <elapsed>,
      "details": "<constraints satisfied / 10>",
      "output_snippet": "<truncated output>"
    }
  ],
  "token_efficiency": {
    "total_wall_clock_seconds": <sum>,
    "estimated_output_tokens": <approx>,
    "tokens_per_second_estimate": <approx>,
    "note": "Estimates based on char/4 approximation. Use API-reported token counts for precision."
  }
}
```

### Step 3: Generate HTML Report

Write the HTML report to `$BENCH_DIR/report.html` using the Python script below. Run it with the results JSON as input.

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
    max_score = data['max_score']
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

    # Radar chart SVG — dynamic for any number of tests
    cx, cy, r = 150, 150, 120
    n = len(scores)
    points_score = []
    label_positions = []
    grid_lines = ''

    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        # Score polygon
        sr = r * scores[i] / 10
        sx = cx + sr * math.cos(angle)
        sy = cy + sr * math.sin(angle)
        points_score.append(f"{sx},{sy}")
        # Labels
        lx = cx + (r + 28) * math.cos(angle)
        ly = cy + (r + 28) * math.sin(angle)
        anchor = 'middle'
        if math.cos(angle) > 0.3: anchor = 'start'
        elif math.cos(angle) < -0.3: anchor = 'end'
        label_positions.append((lx, ly, labels[i], anchor))

    # Grid circles
    for frac in [0.25, 0.5, 0.75, 1.0]:
        gr = r * frac
        grid_pts = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            gx = cx + gr * math.cos(angle)
            gy = cy + gr * math.sin(angle)
            grid_pts.append(f"{gx},{gy}")
        grid_lines += f'<polygon points="{" ".join(grid_pts)}" fill="none" stroke="#e5e7eb" stroke-width="1"/>\n'

    # Axis lines
    axis_lines = ''
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        ax = cx + r * math.cos(angle)
        ay = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{ax}" y2="{ay}" stroke="#e5e7eb" stroke-width="1"/>\n'

    label_els = ''
    for lx, ly, text, anchor in label_positions:
        label_els += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="11" fill="#374151">{text}</text>\n'

    radar_svg = f"""
    <svg viewBox="0 0 300 300" width="300" height="300">
      {grid_lines}
      {axis_lines}
      <polygon points="{' '.join(points_score)}" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="2"/>
      {label_els}
    </svg>
    """

    grade_val = grade(pct)
    grade_color = score_color(total / max_score * 10)

    # Token efficiency section (if present)
    tok_section = ''
    if 'token_efficiency' in data:
        te = data['token_efficiency']
        tok_section = f"""
        <div class="section">
          <h2>Token Efficiency (estimates)</h2>
          <div class="summary" style="margin-bottom:0">
            <div class="summary-card">
              <div class="label">Total Time</div>
              <div class="value" style="font-size:24px">{te.get('total_wall_clock_seconds', 0):.1f}s</div>
            </div>
            <div class="summary-card">
              <div class="label">Est. Output Tokens</div>
              <div class="value" style="font-size:24px">{te.get('estimated_output_tokens', 0):,}</div>
            </div>
            <div class="summary-card">
              <div class="label">Est. Tokens/sec</div>
              <div class="value" style="font-size:24px">{te.get('tokens_per_second_estimate', 0):.1f}</div>
            </div>
          </div>
          <p style="color:#94a3b8;font-size:12px;margin-top:8px">{te.get('note', '')}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Model Benchmark Report — {model}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Helvetica Neue', sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 40px 24px; }}
  .header {{ text-align: center; margin-bottom: 48px; }}
  .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
  .header .subtitle {{ color: #64748b; font-size: 14px; }}
  .summary {{ display: flex; gap: 24px; margin-bottom: 48px; justify-content: center; flex-wrap: wrap; }}
  .summary-card {{ background: white; border-radius: 12px; padding: 24px 32px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); min-width: 160px; }}
  .summary-card .label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .summary-card .value {{ font-size: 36px; font-weight: 700; }}
  .summary-card .sub {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
  .section {{ background: white; border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9; }}
  .radar-container {{ display: flex; justify-content: center; margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; padding: 8px 12px; border-bottom: 2px solid #f1f5f9; }}
  td {{ padding: 16px 12px; border-bottom: 1px solid #f8fafc; vertical-align: top; }}
  .test-name {{ display: flex; align-items: center; gap: 12px; min-width: 200px; }}
  .test-id {{ background: #f1f5f9; color: #64748b; border-radius: 6px; padding: 4px 8px; font-size: 12px; font-weight: 600; }}
  .test-title {{ font-weight: 600; font-size: 14px; }}
  .test-subtitle {{ color: #94a3b8; font-size: 12px; }}
  .score-cell {{ min-width: 160px; }}
  .score-bar-bg {{ background: #f1f5f9; border-radius: 4px; height: 8px; margin-bottom: 4px; }}
  .score-bar {{ height: 8px; border-radius: 4px; transition: width 0.3s; }}
  .score-num {{ font-weight: 700; font-size: 14px; }}
  .time-cell {{ color: #64748b; font-size: 13px; white-space: nowrap; }}
  .detail-cell {{ color: #475569; font-size: 13px; max-width: 280px; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 48px; }}
  .compare-hint {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px 20px; margin-top: 24px; font-size: 13px; color: #1e40af; }}
  @media (max-width: 640px) {{
    .summary {{ flex-direction: column; align-items: center; }}
    .test-name {{ min-width: auto; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Agent Capability Benchmark</h1>
    <div class="subtitle">{model} &mdash; {ts}</div>
  </div>

  <div class="summary">
    <div class="summary-card">
      <div class="label">Model</div>
      <div class="value" style="font-size:20px">{model}</div>
    </div>
    <div class="summary-card">
      <div class="label">Total Score</div>
      <div class="value" style="color:{grade_color}">{total}/{max_score}</div>
      <div class="sub">{pct:.1f}%</div>
    </div>
    <div class="summary-card">
      <div class="label">Grade</div>
      <div class="value" style="color:{grade_color}">{grade_val}</div>
    </div>
    <div class="summary-card">
      <div class="label">Avg Time</div>
      <div class="value" style="font-size:24px">{sum(times)/len(times):.1f}s</div>
      <div class="sub">per test</div>
    </div>
  </div>

  <div class="section">
    <h2>Capability Radar</h2>
    <div class="radar-container">{radar_svg}</div>
  </div>

  <div class="section">
    <h2>Detailed Results</h2>
    <table>
      <thead>
        <tr><th>Test</th><th>Score</th><th>Time</th><th>Details</th></tr>
      </thead>
      <tbody>{test_rows}</tbody>
    </table>
  </div>

  {tok_section}

  <div class="compare-hint">
    To compare models: run this benchmark with different model configurations, then open both report.html files side by side. Each report is a standalone file — no server needed.
  </div>

  <div class="footer">
    Generated by /model-benchmark skill &mdash; Claude Code
  </div>
</div>
</body>
</html>"""

    with open(output_file, 'w') as f:
        f.write(html)
    print(f"Report saved: {output_file}")

if __name__ == '__main__':
    results_file = sys.argv[1]
    output_dir = os.path.dirname(results_file)
    output_file = os.path.join(output_dir, 'report.html')
    generate_report(results_file, output_file)
```

Run it:
```bash
python3 "$BENCH_DIR/generate_report.py" "$BENCH_DIR/results.json"
```

### Step 4: Present Results

After generating the report:

1. Print a summary table to the terminal showing all 10 test scores
2. Print token efficiency estimates
3. Tell the user: "HTML report saved to: `$BENCH_DIR/report.html`"
4. Open the report: `open "$BENCH_DIR/report.html"`
5. Remind: "Run this benchmark again with a different model config to compare side by side."

## Important Rules

- **Objectivity**: All tests now use verifiable, objective scoring criteria. Count passes against rubrics — no subjective judgment calls.
- **Reproducibility**: Use the exact same test prompts every time. Do not modify prompts between runs.
- **Timing**: Time only the model's "thinking + output" portion, not file I/O or verification.
- **Self-testing**: For this benchmark, you ARE the model being tested. Run each test prompt as if you're seeing it for the first time, then score your own output against the objective criteria.
- **Verification**: Always verify answers independently (grep, run code, manual check) before scoring.
- **No cheating**: Do not look at the scoring rubric before answering each test. Process each test prompt first, capture your output, THEN score it.
- **Token efficiency**: Measured as metadata (not scored) using character-count approximation. For precise metrics, use API-reported token counts.
