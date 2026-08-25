# Phase 5 Design Specification: FPL Excel Multi-Tab Export Engine

**Document Type:** Technical Architecture & Implementation Spec  
**Target Phase:** Phase 5 (Excel Write-Back & Report Engine)  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  

---

## 1. Executive Summary & Problem Formulation

The final phase of the Python rebuild bridges the modeling stack back to the repository owner's original spreadsheet workflow. It generates a multi-tab, formatted Excel workbook (`fpl_model_output_<season>_gw<GW>.xlsx`) using `openpyxl`.

The workbook synthesizes the outputs of all previous phases:
- **Phase 1**: Historical stats, Understat xG/xA, FBref starts/subs (`model_dataset.csv`).
- **Phase 2**: 11-component point predictions ($C_1 \dots C_{11}$), Bayesian shrinkage, Poisson expectations (`predictions.csv`).
- **Phase 3**: Fixture difficulty, venue conjugate factors, opponent strength ratios (`fixture_predictions.csv`).
- **Phase 4**: Optimal 15-man squad, starting XI, captaincy ($2\times$), bench priority, and transfers (`SquadSolution`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Phase 5 Excel Workbook (.xlsx)                  │
├────────────────────────────────────────────────────────────────────────┤
│ Sheet 1: 🏆 Summary Dashboard                                          │
│   - KPI Cards: Total Projected xP, Budget Spent, Bank, Formation       │
│   - Visual Pitch Layout: Starting XI (GK/DEF/MID/FWD) + Bench Slots    │
│   - Captain & Vice-Captain highlight                                   │
│                                                                        │
│ Sheet 2: 📋 Optimal Squad                                              │
│   - 15-player table: Role, Pos, Name, Team, Cost, xP, Opponent, FDR    │
│                                                                        │
│ Sheet 3: 🔮 GW Player Predictions                                      │
│   - Full 600+ player projections with all 11 component breakdowns      │
│   - Filterable & sortable by xP, position, team, cost, value (xP/£M)   │
│                                                                        │
│ Sheet 4: ⚔️ Fixtures & Team Ratings                                     │
│   - 20 teams attacking xG90, defending xGC90, opponent multipliers     │
│   - GW fixture matchups with FDR ratings                               │
│                                                                        │
│ Sheet 5: 📊 Form & Underlying Stats                                    │
│   - Short vs Long form rates, FBref starts/subs, Understat data        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Visual Styling & Spreadsheet Architecture

To ensure the workbook feels like a financial/sports analytics model:
1. **Color Palette**:
   - Primary Header Fill: Dark Navy `#1E293B` with White bold text.
   - Accent / Pitch Green: `#0F766E` / `#115E59` (dark emerald / teal).
   - Starter Highlight Fill: `#F0FDF4` (soft green tint).
   - Captain Badge Fill: `#FEF3C7` (warm gold / amber).
   - Zebra Row Alternation: `#F8FAFC` (soft slate tint).
   - Gridlines enabled explicitly across all sheets.
2. **Number Formatting**:
   - Currency / Cost: `£#,##0.0"M"` (e.g. `£15.5M`)
   - Expected Points (xP): `0.00`
   - Rates per 90: `0.000`
   - Percentages / Probabilities: `0.0%`
   - Integers: `#,##0`
3. **UX & Ergonomics**:
   - Frozen Panes: Freeze header rows and player name columns for navigation.
   - Auto-Fitted Column Widths: Calculated dynamically from max string length with safety padding.
   - Total & KPI Summary Rows: Styled with double bottom borders and bold sum formulas.

---

## 3. Module Architecture & File Layout

```
model/
├── __init__.py                # Exports export_excel_report
├── excel_exporter.py          # Core openpyxl multi-tab styling & workbook generator
├── test_excel_exporter.py     # Pytest unit test suite
```

### Core Functions in `model/excel_exporter.py`:
1. `export_excel_report(solution, pred_df, season, gw, output_path=None)`: Main orchestrator building and saving the workbook.
2. `_build_dashboard_sheet(wb, solution, season, gw)`: Generates KPI cards, starting XI pitch, and bench table.
3. `_build_optimal_squad_sheet(wb, solution)`: Generates the 15-player squad breakdown.
4. `_build_predictions_sheet(wb, pred_df)`: Writes full league player predictions with all 11 components.
5. `_build_fixtures_sheet(wb, pred_df, season, gw)`: Writes team attack/defense ratings and gameweek matchups.
6. `_build_form_stats_sheet(wb, pred_df)`: Writes short vs long form comparison table.
7. `_apply_sheet_styling(ws, header_fill, is_table=True)`: Utility applying borders, alignment, fonts, and column widths.

---

## 4. Verification & Testing Plan

1. **Unit Tests in `model/test_excel_exporter.py`**:
   - Verify workbook creation and 5 sheets existence (`Summary Dashboard`, `Optimal Squad`, `GW Predictions`, `Fixtures & Ratings`, `Form & Underlying Stats`).
   - Verify cell values, formulas, and numeric formatting across sheets.
   - Verify column dimensions and frozen panes settings.
   - Verify error handling on missing / empty prediction inputs.
2. **End-to-End Functional Verification**:
   - Run `python -m model.excel_exporter --season 2026-27 --gw 1` to generate `data/2026-27/fpl_model_output_2026-27_gw1.xlsx`.
   - Validate file size, readability with `openpyxl.load_workbook`, and verify sheets and rows.
