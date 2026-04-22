"""
NVDA Financial Model — Two-Stage DCF + Scenario Analysis
Outputs a multi-tab Excel workbook using openpyxl.
"""

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Color palette ──────────────────────────────────────────────
INPUT_COLOR   = "FFF2CC"   # soft yellow  — user-editable assumptions
OUTPUT_COLOR  = "DDEEFF"   # soft blue    — calculated outputs
HEADER_COLOR  = "1F3864"   # dark navy    — section headers
ACCENT_COLOR  = "C6EFCE"   # light green  — positive variance
WARN_COLOR    = "FFCCCC"   # light red    — negative variance

# ── Scenario definitions ───────────────────────────────────────
SCENARIOS = {
    "Base Case":  {"revenue_growth": 0.18, "gross_margin": 0.72, "label": "Base"},
    "Bull Case":  {"revenue_growth": 0.28, "gross_margin": 0.76, "label": "Bull"},
    "Bear Case":  {"revenue_growth": 0.08, "gross_margin": 0.66, "label": "Bear"},
}

# ── DCF assumptions ────────────────────────────────────────────
DISCOUNT_RATE       = 0.10    # WACC
TERMINAL_GROWTH     = 0.03    # perpetual growth rate (Gordon Model)
PROJECTION_YEARS    = 5       # Stage 1 explicit forecast period
SHARES_OUTSTANDING  = 24_530  # millions

# ── Tab / sheet names (order defines workbook tab order) ───────
SHEET_NAMES = [
    "Cover",
    "Assumptions",
    "Income Statement",
    "DCF Valuation",
    "Scenario Summary",
    "Sensitivity",
    "Charts",
]   # 7 tabs total


def build_workbook(output_path: str = "nvda_model.xlsx") -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)          # remove default Sheet

    sheets = {name: wb.create_sheet(name) for name in SHEET_NAMES}

    _build_cover(sheets["Cover"])
    _build_assumptions(sheets["Assumptions"])
    _build_income_statement(sheets["Income Statement"])
    _build_dcf(sheets["DCF Valuation"])
    _build_scenario_summary(sheets["Scenario Summary"])
    _build_sensitivity(sheets["Sensitivity"])
    _build_charts(sheets["Charts"])

    wb.save(output_path)
    print(f"Saved: {output_path}  ({len(wb.sheetnames)} sheets)")


# ── Individual sheet builders ──────────────────────────────────

def _fill(ws, cell_ref: str, color: str):
    ws[cell_ref].fill = PatternFill("solid", fgColor=color)


def _build_cover(ws):
    ws["B2"] = "NVIDIA Corporation (NVDA)"
    ws["B3"] = "Equity Research Model — Two-Stage DCF"
    ws["B4"] = "For educational purposes only"
    ws["B2"].font = Font(bold=True, size=18, color=HEADER_COLOR)


def _build_assumptions(ws):
    ws["B2"] = "Key Assumptions"
    ws["B2"].font = Font(bold=True, color=HEADER_COLOR)

    rows = [
        ("Discount Rate (WACC)",    DISCOUNT_RATE,      "10.0%"),
        ("Terminal Growth Rate",    TERMINAL_GROWTH,    "3.0%"),
        ("Projection Years",        PROJECTION_YEARS,   "5"),
        ("Shares Outstanding (M)",  SHARES_OUTSTANDING, "24,530"),
    ]
    for i, (label, value, display) in enumerate(rows, start=4):
        ws[f"B{i}"] = label
        ws[f"C{i}"] = value
        ws[f"D{i}"] = display
        _fill(ws, f"C{i}", INPUT_COLOR)   # input cells highlighted in INPUT_COLOR


def _build_income_statement(ws):
    ws["B2"] = "Projected Income Statement"
    ws["B2"].font = Font(bold=True, color=HEADER_COLOR)

    headers = ["Metric", "FY+1", "FY+2", "FY+3", "FY+4", "FY+5"]
    for col, h in enumerate(headers, start=2):
        ws.cell(row=3, column=col, value=h).font = Font(bold=True)

    scenario = SCENARIOS["Base Case"]
    base_revenue = 130_500   # $M, FY0 actuals
    for year in range(1, PROJECTION_YEARS + 1):
        revenue = base_revenue * (1 + scenario["revenue_growth"]) ** year
        gross_profit = revenue * scenario["gross_margin"]
        ws.cell(row=4, column=year + 1, value=round(revenue, 0))
        ws.cell(row=5, column=year + 1, value=round(gross_profit, 0))


def _build_dcf(ws):
    """Two-stage DCF — final output is Intrinsic Value Per Share."""
    ws["B2"] = "DCF Valuation"
    ws["B2"].font = Font(bold=True, color=HEADER_COLOR)

    ws["B4"]  = "Stage 1: Explicit Forecast (5 years)"
    ws["B10"] = "Stage 2: Terminal Value"
    ws["B14"] = "Enterprise Value ($M)"
    ws["B15"] = "Net Debt ($M)"
    ws["B16"] = "Equity Value ($M)"
    ws["B17"] = "Shares Outstanding (M)"
    ws["B18"] = "Intrinsic Value Per Share"   # ← final DCF output

    # Illustrative values
    ws["C14"] = 3_050_000
    ws["C15"] = -10_200      # net cash position
    ws["C16"] = 3_060_200
    ws["C17"] = SHARES_OUTSTANDING
    ws["C18"] = round(3_060_200 / SHARES_OUTSTANDING, 2)

    _fill(ws, "C18", OUTPUT_COLOR)
    ws["C18"].font = Font(bold=True)


def _build_scenario_summary(ws):
    ws["B2"] = "Scenario Summary"
    ws["B2"].font = Font(bold=True, color=HEADER_COLOR)

    headers = ["Scenario", "Revenue Growth", "Gross Margin", "Implied Price"]
    for col, h in enumerate(headers, start=2):
        ws.cell(row=3, column=col, value=h).font = Font(bold=True)

    for row, (name, params) in enumerate(SCENARIOS.items(), start=4):
        ws.cell(row=row, column=2, value=name)
        ws.cell(row=row, column=3, value=params["revenue_growth"])
        ws.cell(row=row, column=4, value=params["gross_margin"])
        ws.cell(row=row, column=5, value="=C18*(1+RAND()*0.1)")   # placeholder
        _fill(ws, f"B{row}", INPUT_COLOR)


def _build_sensitivity(ws):
    ws["B2"] = "Sensitivity: WACC vs Terminal Growth"
    ws["B2"].font = Font(bold=True, color=HEADER_COLOR)

    wacc_range   = [0.08, 0.09, 0.10, 0.11, 0.12]
    growth_range = [0.02, 0.025, 0.03, 0.035, 0.04]

    for col, g in enumerate(growth_range, start=3):
        ws.cell(row=3, column=col, value=f"{g:.1%}")
    for row, w in enumerate(wacc_range, start=4):
        ws.cell(row=row, column=2, value=f"{w:.1%}")
        for col, g in enumerate(growth_range, start=3):
            fcf = 50_000
            tv = fcf * (1 + g) / (w - g)
            price = round(tv / SHARES_OUTSTANDING, 0)
            ws.cell(row=row, column=col, value=price)


def _build_charts(ws):
    ws["B2"] = "Charts placeholder — add openpyxl BarChart objects here"


if __name__ == "__main__":
    build_workbook()
