# Mathematical Models & Analytical Specifications

This section defines the mathematical formulations, probabilistic models, statistical distributions, and optimization algorithms powering the analytics platform.

## Documents

* [Point-Prediction Engine](/models/point-prediction-engine.md) - Exact formulation for the 11 scoring components ($C_1 \dots C_{11}$), Poisson clean sheet and discrete goals conceded distributions, and Empirical Bayes shrinkage ($M_0 = 500.0\text{ mins}$).
* [Fixture & Form Adjustment Engine](/models/fixture-and-form-engine.md) - Mathematical model for 6-GW sample-size form blending, conjugate venue factors ($1.08 / 0.9259$), and promoted team baseline priors.
* [Squad Optimization Solver](/models/squad-optimization-solver.md) - Multi-gameweek lookahead Mixed-Integer Linear Programming (MILP) solver with 50% profit selling price mechanics and CVaR risk tuning.
* [Minutes & Playing Probability Model](/models/minutes-model.md) - Starter proration, active ratio modeling, and substitution cameo calculations.
* [Match Simulator & Rank Distribution](/models/match-simulator.md) - Monte Carlo matchday simulation for ceiling/floor outcomes and rank distributions.
* [Effective Ownership & Game Theory Engine](/models/ownership-engine.md) - Top-10k ownership modeling and rank protection mechanics.
* [Price Change Forecaster](/models/price-predictor.md) - Net transfer momentum forecasting for price rises and falls.
* [Set-Piece Specialist Hierarchies](/models/set-pieces.md) - Penalties, direct free-kicks, and corner taker priority modeling.
* [Live Auto-Substitutions & Captaincy Rollover](/models/auto-sub-and-captaincy.md) - Official FPL formation-safe bench substitution engine and vice-captain promotion rules.
