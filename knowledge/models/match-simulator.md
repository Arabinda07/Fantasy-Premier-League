---
type: Model Component
title: Bivariate Dixon-Coles Match Simulator & Monte Carlo Engine
description: Mathematical formulation for Dixon-Coles low-scoring dependence, exact bivariate probability grids, 10,000-run Monte Carlo match simulations, player goal/assist attribution, and True BPS allocation.
resource: model/match_simulator.py
tags: [math, model, dixon-coles, monte-carlo, simulation, bps, rank-distribution]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: match-sim-src
    resource: model/match_simulator.py
    title: Match Simulator Source Code
---

# Mathematical Specification: Dixon-Coles Match Simulator & Monte Carlo Engine

The match simulator ([model/match_simulator.py](/computations/simulate-matches.md)) provides:
1. Exact discrete bivariate scoreline probability distributions.
2. Vectorized 10,000-run Monte Carlo fixture simulation with multinomial player attribution.
3. Official FPL Bonus Points System (BPS) calculation and 3, 2, 1 bonus point allocation.
4. Player-level percentile distributions (Mean, $\sigma$, Floor $p_{10}$, Median $p_{50}$, Ceiling $p_{90}$, Haul Probability $P(\text{Points} \ge 10)$).

---

## 1. Bivariate Dixon-Coles Poisson Model

Independent Poisson assumptions fail to capture the empirical correlation in low-scoring football matches. The Dixon-Coles model introduces a low-scoring adjustment factor $\tau(x, y; \rho)$ where default $\rho = -0.05$:

$$P(X=x, Y=y) = \tau(x, y; \rho) \cdot \frac{\lambda_h^x e^{-\lambda_h}}{x!} \cdot \frac{\mu_a^y e^{-\mu_a}}{y!}$$

### Low-Scoring Correction Factor $\tau(x, y; \rho)$

$$\tau(x, y; \rho) = \begin{cases}
1 - \lambda_h \mu_a \rho & \text{for } (x, y) = (0, 0) \\
1 + \lambda_h \rho & \text{for } (x, y) = (0, 1) \\
1 + \mu_a \rho & \text{for } (x, y) = (1, 0) \\
1 - \rho & \text{for } (x, y) = (1, 1) \\
1.0 & \text{for all other } (x, y)
\end{cases}$$

The resulting $(11 \times 11)$ grid (for $x, y \in \{0 \dots 10\}$) is normalized so that $\sum_{x,y} P(X=x, Y=y) \equiv 1.0$.

---

## 2. Discrete Match Outcome Probabilities

From the normalized probability matrix $\mathbf{P}$:

* **Home Win**: $P(\text{Home Win}) = \sum_{x > y} P(X=x, Y=y)$ (lower triangle)
* **Draw**: $P(\text{Draw}) = \sum_{x = y} P(X=x, Y=y)$ (diagonal)
* **Away Win**: $P(\text{Away Win}) = \sum_{x < y} P(X=x, Y=y)$ (upper triangle)
* **Home Clean Sheet**: $P(\text{Home CS}) = \sum_x P(X=x, Y=0)$ (column $y=0$)
* **Away Clean Sheet**: $P(\text{Away CS}) = \sum_y P(X=0, Y=y)$ (row $x=0$)
* **Both Teams to Score (BTTS)**: $P(\text{BTTS}) = \sum_{x \ge 1, y \ge 1} P(X=x, Y=y)$
* **Over 2.5 Goals**: $P(\text{Over 2.5}) = \sum_{x+y \ge 3} P(X=x, Y=y)$

---

## 3. Monte Carlo Simulation Engine ($N = 10,000$)

### Step 1: Scoreline Sampling
The 2D joint distribution is flattened into a 1D categorical distribution of length 121. $N=10,000$ joint scorelines $(H_s, A_s)$ are sampled using thread-safe isolated NumPy generators (`np.random.default_rng(seed)`).

### Step 2: Goal Attribution
For each simulated home goal, the scorer is selected via multinomial sampling weighted by:

$$w_{\text{goal}, i} \propto \max(0.001, \, xG90_i \cdot \text{active\_ratio}_i)$$

### Step 3: Assist Attribution
75% of simulated goals are assisted. The assister is drawn from remaining teammates ($j \ne \text{scorer}$) weighted by:

$$w_{\text{assist}, j} \propto \max(0.001, \, xA90_j \cdot \text{active\_ratio}_j)$$

---

## 4. True BPS Allocation Algorithm

In each simulation iteration, full BPS points are awarded per player:
* **Goals**: FWD/MID $+24$, DEF/GK $+12$
* **Assists**: $+9$
* **Clean Sheet ($\ge 60$ mins)**: GK/DEF $+12$
* **Minutes**: $\ge 60$ mins $\implies +6$, $1-59$ mins $\implies +3$
* **Saves (GK)**: $+2$ per save
* **Defensive Contributions**: $+1$ per DC
* **Goals Conceded ($\ge 2$ GC, $\ge 60$ mins)**: $-4$
* **Discipline**: Yellow $-3$, Red $-9$

Official FPL 3, 2, 1 bonus points are awarded to the top 3 BPS earners, handling exact tie tiers (joint-first yields two 3-point awards with 1 point to third, etc.).

---

## 5. Player Statistical Distributions

For each player across all 10,000 simulation runs:
* **Mean $xP$**: $\mathbb{E}[\text{Points}] = \frac{1}{N}\sum_{s=1}^N \text{pts}_s$
* **Volatility $\sigma$**: $\sqrt{\text{Var}(\text{Points})}$
* **Floor ($p_{10}$)**: 10th percentile outcome
* **Median ($p_{50}$)**: 50th percentile outcome
* **Ceiling ($p_{90}$)**: 90th percentile outcome
* **Haul Probability**: $P(\text{Points} \ge 10) = \frac{1}{N}\sum_{s=1}^N \mathbb{I}(\text{pts}_s \ge 10)$

[^match-sim-src]: `model/match_simulator.py`
