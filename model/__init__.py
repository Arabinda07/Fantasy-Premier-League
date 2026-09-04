"""model/ — FPL points-prediction rebuild package.

Phases:
- Phase 1: Data Pipeline (rolling_form, build_dataset)
- Phase 2: Point-Prediction Engine (prediction_engine)
- Phase 3: Fixture & Form Adjustment Engine (fixture_engine)
- Phase 4: Squad Optimization Solver (solver)
- Phase 5: Excel Export Engine (excel_exporter)
- Live Data Pipeline Automation (pipeline_automation)
"""

from model.prediction_engine import (
    predict_player_points,
    predict_all_players,
    apply_empirical_bayes_shrinkage,
    poisson_pmf,
    poisson_cdf,
    poisson_clean_sheet_prob,
    poisson_two_plus_gc_prob,
    poisson_exact_gc_penalty,
    poisson_dc_hit_prob,
    estimate_playing_probabilities,
    GOAL_POINTS,
    ASSIST_POINTS,
    CLEAN_SHEET_POINTS,
    POSITIONAL_PRIORS,
)

from model.fixture_engine import (
    blend_form_rates,
    compute_team_league_averages,
    compute_fixture_multipliers,
    load_fixtures_for_gw,
    predict_player_fixture,
    predict_gameweek_fixtures,
    DEFAULT_ALPHA,
    HOME_ATTACK_FACTOR,
    HOME_DEFENSE_FACTOR,
    AWAY_ATTACK_FACTOR,
    AWAY_DEFENSE_FACTOR,
)

from model.solver import (
    solve_initial_squad,
    solve_weekly_transfers,
    solve_multi_horizon_transfers,
    order_bench,
    format_squad_output,
    PlayerPick,
    SquadSolution,
    TransferSolution,
    GameweekPlan,
    MultiHorizonSolution,
)

from model.excel_exporter import (
    export_excel_report,
)

from model.chip_optimizer import (
    detect_double_and_blank_gameweeks,
    evaluate_chip_schedule,
    SeasonalChipPlan,
    ChipRecommendation,
)

from model.live_manager import (
    manage_gameweek,
    apply_live_injury_dampening,
)

from model.pipeline_automation import (
    run_live_pipeline,
    detect_active_gameweek,
    record_price_snapshot,
    PipelineResult,
    StageResult,
)

from model.match_simulator import (
    dixon_coles_tau,
    compute_dixon_coles_matrix,
    analyze_bivariate_scoreline_matrix,
    compute_true_bps_and_bonus,
    simulate_match_monte_carlo,
    simulate_gameweek_fixtures,
    MatchProbabilityMetrics,
    PlayerSimulationDistribution,
)

from model.live_sync import (
    sync_manager_profile,
    fetch_fpl_entry_summary,
    fetch_fpl_entry_picks,
    fetch_fpl_entry_transfers,
    fetch_fpl_league_standings,
    load_element_to_code_map,
    load_code_to_element_map,
    LiveSyncProfile,
)

from model.minutes_model import (
    compute_player_minutes_hazard,
    predict_gameweek_minutes_distribution,
    calculate_pre60_hook_probability,
    MinutesDistributionProfile,
)

from model.bps_tournament import (
    compute_player_bps_propensity,
    solve_plackett_luce_tournament,
    calibrate_fixture_bonus_points,
    DEFAULT_BPS_TEMPERATURE,
    DEFAULT_TIE_INFLATION,
)
