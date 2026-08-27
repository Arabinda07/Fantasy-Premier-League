# FPL Dugout — Voice, Tone & Copy Style Guide

## 1. Brand Identity & Persona

### 1.1 App Identity
- **Full Brand Name**: **FPL Dugout** *(Smart Squad & Matchday Planner)*
- **Short Badge / Mobile Name**: **Dugout**

### 1.2 Who We Are (The Persona)
We speak like the **sharpest, most enthusiastic football fan in your college/office WhatsApp group and local EPL fan club**.
- **Tactical, not academic**: We explain smart data (xG, clean sheet odds, fixture swings) without sounding like a statistics textbook.
- **Direct & Manager-to-Manager**: We give actionable advice that helps fans climb ranks, win mini-leagues, and avoid silly mistakes (e.g. taking unnecessary -4 hits or forgetting to check price rises).
- **Zero Corporate Fluff**: We never talk about "assets", "portfolios", "capital allocation", or "risk mitigation". We talk about *players*, *squads*, *budget*, and *protecting your lead*.

---

## 2. Core Tone Pillars

| Pillar | How It Sounds | What It Replaces | Example |
| :--- | :--- | :--- | :--- |
| **1. Direct & Punchy** | Short, active sentences with natural flow. | Passive, verbose corporate explanations. | *"Save this for major Blank Gameweeks to field a full XI without taking hits."* |
| **2. Football Native** | Speaks the authentic language of Indian FPL managers. | Financial trader jargon (*"assets"*, *"downside risk"*). | *"Danger Player — Owned by 4 of your top 5 rivals"* |
| **3. Crystal-Clear Math** | Math is translated into everyday football outcomes. | Statistical formula names (*"Poisson"*, *"Bayesian Shrinkage"*). | *"League Averages by Position"* instead of *"Empirical Bayesian Shrinkage Prior"* |
| **4. Encouraging & Tactical** | Empowers the manager to make the final call. | Robotic prescriptive commands. | *"Test any transfer head-to-head to see projected point gains and budget impact."* |

---

## 3. The 3-Tier Vocabulary Filter

### Tier 1: Keep (Sacred FPL Fan Vocabulary)
*Do NOT replace or over-explain these core community terms:*
- **Punt** / **Differential** / **Template** / **Essential**
- **Haul** (double-digit points) / **Blank** (2 or fewer points)
- **Free Transfer (FT)** / **Banked FT** (saving transfers) / **Point Hit (-4 pts)**
- **Clean Sheet (CS)** / **Bonus Points (BPS)** / **Expected Goals (xG)** / **Expected Assists (xA)**
- **Chips**: **Triple Captain (3xC)**, **Bench Boost (BB)**, **Free Hit (FH)**, **Wildcard (WC)**
- **Gameweek (GW)** / **Double Gameweek (DGW)** / **Blank Gameweek (BGW)**

---

### Tier 2: Translate (Statistical / Academic $\to$ Fan-Friendly English)
*Always replace the left column with the right column:*

| Statistical / Formal Term | Fan-Friendly Indian English Replacement | Component Surface |
| :--- | :--- | :--- |
| `Expected Value (EV) / Dynamic xP` | `Projected Points / Exp Pts / Expected Points` | All Surfaces |
| `Linear Programming Horizon` | `5-Gameweek Transfer Planner & Bank Strategy` | Transfer Planner |
| `Bivariate Dixon-Coles Poisson Model` | `Match Preview · Scoreline Chances & Clean Sheet Odds` | Fixture Matchup Drawer |
| `Column 0 sum (Away 0 goals)` | `Chance of shutting out opponent` | Matchup Drawer |
| `Empirical Bayesian Shrinkage` | `Blending Recent Form with Long-Term Career Record` | Points Forecaster |
| `Mean Absolute Error (MAE)` | `Average Points Margin (±X pts per starter)` | Forecaster Accuracy |
| `Rank Correlation (Spearman ρ)` | `Player Rank Consistency (Accurately identifies top picks)` | Forecaster Accuracy |
| `Outlier Diagnostic / Root Cause` | `Gameweek Surprises & Anomalies / Why: [Match reason]` | Forecaster Outliers |
| `Player DNA Breakdown` | `Scouting Report, Stats & Points Breakdown` | Player Modal / Drawer |
| `Net Head-to-Head Haul Advantage` | `Your Points Advantage (+X pts projected lead)` | Mini-Leagues |
| `FDR Avg` | `Avg Difficulty` | Fixture Heatmap |

---

### Tier 3: Ban (Forbidden Corporate & Lab Jargon)
*Never use these words in UI text, tooltips, or validation messages:*

| ❌ Banned Word / Phrase | ✅ Approved Alternative |
| :--- | :--- |
| `Assets / Asset Allocation` | `Players / Squad / Picks` |
| `Capital / Funds Depletion` | `Bank Balance / Budget / Extra Cost` |
| `Downside Protection / Risk Profile` | `Protecting Your Lead / Safe Template Picks` |
| `Execution Error / System Exception` | `Formation Alert / Transfer Error` |
| `Deploy on a prolific attacker` | `Best played on heavy hitters like Haaland or Salah` |
| `Navigate fixture congestion` | `Rotate players during busy double gameweeks` |
| `Sub-optimal roster composition` | `Invalid squad formation (e.g. need at least 3 defenders)` |

---

## 4. Standard UI Copy Blueprints

### 4.1 Navigation Tabs
```
Lineup          -> My Lineup (Active squad pitch, captaincy, chips & bench)
Planner         -> Transfer Planner (5-week transfer roadmap & H2H scout)
Rivals          -> Mini-Leagues (Standings, rival tracking & differentials)
Fixtures        -> Fixture Ticker (38-week difficulty schedule & match odds)
Prices          -> Price Trends (Daily midnight rises/falls & chip guide)
Forecaster      -> Points Forecaster (Projection formula & accuracy scorecard)
```

### 4.2 Tactical Chips & Strategy Badges
- **Triple Captain**: *"Best used on heavy hitters like Haaland or Salah during a Double Gameweek with two easy fixtures."*
- **Bench Boost**: *"Best played during the biggest Double Gameweek when all 15 players in your squad have two games."*
- **Free Hit**: *"Save this for major Blank Gameweeks to field a full starting XI without burning transfers."*
- **Wildcard**: *"Use during fixture swings to reshape your squad and bring in players from top clubs."*
- **Badges**:
  - `⚡ DIFF`: *"Differential pick — owned by under 20% of managers in your league"*
  - `🛡️ TEMPLATE`: *"Popular pick — high ownership to protect your mini-league rank"*
  - `🚀 BB`: *"Bench Boost Active · Scoring points this gameweek"*

### 4.3 Validation Messages & Alerts
- **Formation Errors**:
  - *"You need at least 3 Defenders in your starting XI. Please adjust your formation before confirming."*
  - *"You need at least 1 Goalkeeper, 3 Defenders, 2 Midfielders, and 1 Forward in your starting XI."*
- **Budget Errors**:
  - *"Not enough funds: Saka costs £10.1m, but you only have £9.8m in your bank."*
- **Club Limit Errors**:
  - *"Maximum 3 players allowed from Arsenal (you already have Saka, Gabriel, and Saliba)."*

---

## 5. Development Checklist for New Features

Before merging any new component, modal, or tooltip, verify:
1. [ ] **No Raw Math Terms**: Are formulas translated into football language (*"Clean sheet chance"*, *"Goal threat"* rather than *"Poisson PMF"* or *"Bayesian prior"*?)
2. [ ] **No Corporate Speak**: Are you referring to *"players"* and *"squad"* rather than *"assets"* and *"portfolio"*?
3. [ ] **Tone Check**: Does this sound like a knowledgeable friend in a football chat group?
4. [ ] **Tokens Used**: Are shared strings imported from `frontend/src/constants/copyTokens.js`?
