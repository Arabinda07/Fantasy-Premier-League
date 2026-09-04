"""Rolling form calculator for the FPL prediction model.

Computes per-player and per-team rolling form metrics from CSVs already on
disk (data/<season>/gws/merged_gw.csv, data/<season>/players_raw.csv).

This is a pure function of the files on disk plus the parameters — it does
not persist a historical table. It only answers "what are the rates right
now", not a full historical time series.
"""
import math
import os
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd


# The columns from merged_gw.csv that we sum over a form window and then
# express as per-90 rates.
PLAYER_RATE_COLS = [
    'expected_goals',        # xG
    'expected_assists',      # xA
    'expected_goals_conceded',  # xGC
    'defensive_contribution',   # DC
    'bonus',
    'bps',
]

# Default exponential half-life for retrospective form aggregation (M-03)
DEFAULT_HALF_LIFE: float = 8.0

# Default inter-season summer break gap in equivalent gameweeks (~90 days off-season)
DEFAULT_SUMMER_BREAK_GAP: int = 4


def calculate_gw_lag(
    match_season: str,
    match_gw: int,
    current_season: str,
    current_gw: int,
    summer_gap: int = DEFAULT_SUMMER_BREAK_GAP,
) -> int:
    """Calculate the elapsed gameweek distance between a historical match and evaluation point.

    Args:
        match_season: season of the historical match (e.g. '2024-25').
        match_gw: gameweek number of the historical match (1 to 38).
        current_season: season at evaluation time (e.g. '2025-26').
        current_gw: gameweek number at evaluation time (1 to 38).
        summer_gap: effective gameweeks elapsed during inter-season summer break (default 4).

    Returns:
        Non-negative integer gameweek lag.
    """
    try:
        curr_start = int(str(current_season).split('-')[0])
        match_start = int(str(match_season).split('-')[0])
    except (ValueError, AttributeError, IndexError):
        return max(0, int(current_gw) - int(match_gw))

    season_diff = curr_start - match_start
    if season_diff == 0:
        return max(0, int(current_gw) - int(match_gw))
    elif season_diff > 0:
        # Include summer break gap to account for 3 months of off-season attrition/transfers
        return max(0, int(current_gw) + (38 - int(match_gw)) + (season_diff - 1) * 38 + int(summer_gap))
    else:
        return 0


def compute_ewma_weight(lag_gws: int, half_life: Optional[float] = DEFAULT_HALF_LIFE) -> float:
    """Compute exponential decay weight 2^(-lag / half_life).

    Args:
        lag_gws: non-negative gameweek lag.
        half_life: half-life in gameweeks (default 8.0). If None or <= 0, returns 1.0.

    Returns:
        Float weight in (0.0, 1.0].
    """
    if half_life is None or half_life <= 0:
        return 1.0
    return math.pow(2.0, -float(lag_gws) / float(half_life))


def _load_merged_gw(season, data_root='data'):
    """Load merged_gw.csv for a given season.

    Args:
        season: e.g. '2025-26'.
        data_root: root data directory.

    Returns:
        pd.DataFrame, or an empty DataFrame if the file doesn't exist.
    """
    path = os.path.join(data_root, season, 'gws', 'merged_gw.csv')
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def _load_merged_gw_with_code(season, data_root='data'):
    """Load merged_gw.csv and join to players_raw.csv to add 'code' column.

    'element' IDs are NOT stable across seasons — element=3 in 2024-25
    may be a completely different player than element=3 in 2025-26.
    The 'code' column from players_raw.csv IS stable across seasons,
    so this must be joined BEFORE concatenating data across seasons.

    Args:
        season: e.g. '2025-26'.
        data_root: root data directory.

    Returns:
        pd.DataFrame with merged_gw data plus a 'code' column, or an
        empty DataFrame if the file doesn't exist.
    """
    gw_df = _load_merged_gw(season, data_root)
    if gw_df.empty:
        return pd.DataFrame()

    pr_path = os.path.join(data_root, season, 'players_raw.csv')
    if not os.path.exists(pr_path):
        return gw_df  # no code available, fallback

    pr = pd.read_csv(pr_path, usecols=['id', 'code'])
    gw_df = gw_df.merge(pr, left_on='element', right_on='id', how='left')
    return gw_df


def _load_id_map(season, data_root='data'):
    """Load the element-id → player-code mapping from players_raw.csv.

    Args:
        season: e.g. '2025-26'.
        data_root: root data directory.

    Returns:
        pd.DataFrame with columns ['id', 'code', 'web_name', 'element_type'].
    """
    path = os.path.join(data_root, season, 'players_raw.csv')
    cols = ['id', 'code', 'web_name', 'element_type']
    return pd.read_csv(path, usecols=cols)


def _previous_season(season):
    """Given '2025-26', return '2024-25'.

    Args:
        season: season string.

    Returns:
        Previous season string, or None if the start year would be < 2016.
    """
    parts = season.split('-')
    start = int(parts[0])
    if start <= 2016:
        return None
    prev_start = start - 1
    prev_end = start  # end year = current start year
    return str(prev_start) + '-' + str(prev_end % 100).zfill(2)


def _filter_window(df, season, gw, window_gws, data_root='data'):
    """Select rows from merged_gw data within a gameweek window.

    The window is defined as "the last `window_gws` gameweeks up to and
    including `gw` in `season`". If the window extends before GW1 of the
    given season, it reaches back into the prior season.

    Each season's data is joined to its players_raw.csv to get the cross-
    season-stable 'code' column BEFORE concatenation (since 'element' IDs
    are NOT stable across seasons).

    Args:
        df: unused (kept for signature compat). We load fresh from disk.
        season: current season string.
        gw: current gameweek number (inclusive upper bound).
        window_gws: number of gameweeks in the window. Use None for
                    "full season to date" (GW1 through gw).
        data_root: root data directory.

    Returns:
        pd.DataFrame of merged_gw rows within the window, possibly spanning
        two seasons. Has 'season' and 'code' columns added.
    """
    current = _load_merged_gw_with_code(season, data_root)
    if current.empty:
        # Try previous season only
        prev = _previous_season(season)
        if prev is None:
            return pd.DataFrame()
        prev_df = _load_merged_gw_with_code(prev, data_root)
        if prev_df.empty:
            return pd.DataFrame()
        prev_df['season'] = prev
        if window_gws is None:
            return prev_df
        return prev_df[prev_df['GW'] > (prev_df['GW'].max() - window_gws)]

    current['season'] = season

    if window_gws is None:
        # Full season to date for current season, plus full prior season
        current_window = current[current['GW'] <= gw]
        prev = _previous_season(season)
        if prev is not None:
            prev_df = _load_merged_gw_with_code(prev, data_root)
            if not prev_df.empty:
                prev_df['season'] = prev
                return pd.concat([prev_df, current_window], ignore_index=True)
        return current_window

    # Fixed-size window (e.g. last 6 GWs)
    current_in_range = current[current['GW'] <= gw]
    gws_available = sorted(current_in_range['GW'].unique())

    if len(gws_available) >= window_gws:
        # Enough gameweeks in current season
        cutoff_gws = gws_available[-window_gws:]
        return current_in_range[current_in_range['GW'].isin(cutoff_gws)]

    # Need to reach into previous season
    remaining = window_gws - len(gws_available)
    prev = _previous_season(season)
    result = current_in_range.copy()

    if prev is not None:
        prev_df = _load_merged_gw_with_code(prev, data_root)
        if not prev_df.empty:
            prev_df['season'] = prev
            prev_gws = sorted(prev_df['GW'].unique())
            if remaining <= len(prev_gws):
                cutoff = prev_gws[-remaining:]
                prev_window = prev_df[prev_df['GW'].isin(cutoff)]
            else:
                prev_window = prev_df
            result = pd.concat([prev_window, result], ignore_index=True)

    return result


def compute_player_form(season, gw, window_gws=None, half_life=DEFAULT_HALF_LIFE, data_root='data'):
    """Compute per-player rolling form metrics with exponential recency decay.

    Aggregates by 'code' (the cross-season-stable player identifier) so
    that multi-season windows correctly combine the same player's data
    even when their 'element' ID differs between seasons.

    Args:
        season: current season string, e.g. '2025-26'.
        gw: current gameweek number.
        window_gws: number of gameweeks in the window. None means "full
                    season(s) to date" (long-form).
        half_life: half-life in gameweeks for EWMA decay (default DEFAULT_HALF_LIFE = 8.0).
                   If None or <= 0, flat unweighted aggregation is used.
        data_root: root data directory.

    Returns:
        pd.DataFrame with columns:
            code, minutes, unweighted_minutes, expected_goals, expected_assists, ...,
            expected_goals_90, expected_assists_90, ...
        Keyed by 'code' (the cross-season stable player code).
        Also carries 'element' (the most recent season's element ID)
        for downstream joining.
    """
    window_df = _filter_window(None, season, gw, window_gws, data_root)
    if window_df.empty:
        return pd.DataFrame()

    # Coerce rate columns and minutes to numeric
    for col in PLAYER_RATE_COLS + ['minutes']:
        if col in window_df.columns:
            window_df[col] = pd.to_numeric(window_df[col], errors='coerce').fillna(0)

    # Compute EWMA weight per match row
    if half_life is not None and half_life > 0:
        match_seasons = window_df['season'] if 'season' in window_df.columns else [season] * len(window_df)
        match_gws = window_df['GW'] if 'GW' in window_df.columns else [gw] * len(window_df)
        window_df['gw_lag'] = [
            calculate_gw_lag(s, g, season, gw)
            for s, g in zip(match_seasons, match_gws)
        ]
        window_df['form_weight'] = [
            compute_ewma_weight(lag, half_life) for lag in window_df['gw_lag']
        ]
    else:
        window_df['form_weight'] = 1.0

    # Calculate weighted metrics per row
    window_df['w_minutes'] = window_df['minutes'] * window_df['form_weight']
    for col in PLAYER_RATE_COLS:
        if col in window_df.columns:
            window_df['w_' + col] = window_df[col] * window_df['form_weight']

    # Aggregate per player by 'code' (cross-season stable)
    # Also keep the most recent element ID for downstream joins
    agg_dict = {
        'w_minutes': 'sum',
        'minutes': 'sum',
        'element': 'last',
    }
    for col in PLAYER_RATE_COLS:
        if col in window_df.columns:
            agg_dict['w_' + col] = 'sum'
            agg_dict[col] = 'sum'

    grouped = window_df.groupby('code').agg(agg_dict).reset_index()

    # If half_life was used, minutes is weighted effective minutes,
    # and unweighted_minutes stores raw physical minutes
    if half_life is not None and half_life > 0:
        grouped['unweighted_minutes'] = grouped['minutes']
        grouped['minutes'] = grouped['w_minutes'].round(1)
        for col in PLAYER_RATE_COLS:
            if col in grouped.columns:
                grouped['unweighted_' + col] = grouped[col]
                grouped[col] = grouped['w_' + col].round(4)
    else:
        grouped['unweighted_minutes'] = grouped['minutes']

    # Compute per-90 rates: col / (minutes / 90.0)
    for col in PLAYER_RATE_COLS:
        if col in grouped.columns:
            col_90 = col + '_90'
            grouped[col_90] = grouped.apply(
                lambda r: round(r[col] / (r['minutes'] / 90.0), 4)
                if r['minutes'] > 0 else 0.0,
                axis=1
            )

    # Drop temporary w_ columns
    drop_cols = [c for c in grouped.columns if c.startswith('w_')]
    grouped = grouped.drop(columns=drop_cols, errors='ignore')

    return grouped


def compute_team_form(season, gw, window_gws=None, half_life=DEFAULT_HALF_LIFE, data_root='data'):
    """Compute per-team rolling form (xG and xGC per 90) with exponential recency decay.

    Uses merged_gw.csv team-level aggregation:
    - Match-level xG: sum of expected_goals across all players on that team in that match.
    - Match-level xGC: max expected_goals_conceded across players on that team in that match
      (since FPL prorates xGC by minutes played, the 90-min defender has full-match value).
    - Match-level weight: 2^(-lag / half_life).

    Args:
        season: current season string.
        gw: current gameweek number.
        window_gws: window size or None for full season(s).
        half_life: half-life in gameweeks for EWMA decay (default DEFAULT_HALF_LIFE = 8.0).
                   If None or <= 0, flat unweighted aggregation is used.
        data_root: root data directory.

    Returns:
        pd.DataFrame with columns: team, matches, team_minutes, team_xg, team_xgc,
        team_xg90, team_xgc90.
    """
    window_df = _filter_window(None, season, gw, window_gws, data_root)
    if window_df.empty:
        return pd.DataFrame()

    for col in ['expected_goals', 'expected_goals_conceded', 'minutes']:
        if col in window_df.columns:
            window_df[col] = pd.to_numeric(window_df[col], errors='coerce').fillna(0)

    gw_col = 'GW'
    match_key = ['team', gw_col, 'season'] if 'season' in window_df.columns else ['team', gw_col]

    # Match-level xG and xGC
    match_xg = window_df.groupby(match_key)['expected_goals'].sum().reset_index()
    match_xgc = window_df.groupby(match_key)['expected_goals_conceded'].max().reset_index()
    matches_df = match_xg.merge(match_xgc, on=match_key, how='inner')

    # Compute match weight
    if half_life is not None and half_life > 0:
        match_seasons = matches_df['season'] if 'season' in matches_df.columns else [season] * len(matches_df)
        match_gws = matches_df['GW'] if 'GW' in matches_df.columns else [gw] * len(matches_df)
        matches_df['gw_lag'] = [
            calculate_gw_lag(s, g, season, gw)
            for s, g in zip(match_seasons, match_gws)
        ]
        matches_df['form_weight'] = [
            compute_ewma_weight(lag, half_life) for lag in matches_df['gw_lag']
        ]
    else:
        matches_df['form_weight'] = 1.0

    matches_df['w_xg'] = matches_df['expected_goals'] * matches_df['form_weight']
    matches_df['w_xgc'] = matches_df['expected_goals_conceded'] * matches_df['form_weight']

    team_summary = matches_df.groupby('team').agg({
        'form_weight': 'sum',
        'expected_goals': 'sum',
        'expected_goals_conceded': 'sum',
        'w_xg': 'sum',
        'w_xgc': 'sum',
    }).reset_index()

    # Match count
    raw_counts = matches_df.groupby('team')[gw_col].count().reset_index().rename(columns={gw_col: 'matches'})
    team_summary = team_summary.merge(raw_counts, on='team', how='left')

    if half_life is not None and half_life > 0:
        team_summary['team_xg'] = team_summary['w_xg'].round(4)
        team_summary['team_xgc'] = team_summary['w_xgc'].round(4)
        team_summary['team_minutes'] = (team_summary['form_weight'] * 90.0).round(1)
        team_summary['team_xg90'] = team_summary.apply(
            lambda r: round(r['team_xg'] / (r['team_minutes'] / 90.0), 4)
            if r['team_minutes'] > 0 else 0.0,
            axis=1
        )
        team_summary['team_xgc90'] = team_summary.apply(
            lambda r: round(r['team_xgc'] / (r['team_minutes'] / 90.0), 4)
            if r['team_minutes'] > 0 else 0.0,
            axis=1
        )
    else:
        team_summary['team_xg'] = team_summary['expected_goals'].round(4)
        team_summary['team_xgc'] = team_summary['expected_goals_conceded'].round(4)
        team_summary['team_minutes'] = team_summary['matches'] * 90
        team_summary['team_xg90'] = team_summary.apply(
            lambda r: round(r['team_xg'] / (r['team_minutes'] / 90.0), 4)
            if r['team_minutes'] > 0 else 0.0,
            axis=1
        )
        team_summary['team_xgc90'] = team_summary.apply(
            lambda r: round(r['team_xgc'] / (r['team_minutes'] / 90.0), 4)
            if r['team_minutes'] > 0 else 0.0,
            axis=1
        )

    return team_summary[['team', 'matches', 'team_minutes', 'team_xg', 'team_xgc',
                         'team_xg90', 'team_xgc90']]


def build_player_form_dataset(season, gw, short_form_window=6,
                               half_life_long=DEFAULT_HALF_LIFE,
                               half_life_short=None,
                               data_root='data'):
    """Build the complete player form dataset with both long-form (EWMA decayed)
    and short-form metrics, keyed by player code.

    Args:
        season: current season, e.g. '2025-26'.
        gw: current gameweek number.
        short_form_window: number of gameweeks for short-form (default 6).
        half_life_long: half-life in GWs for long-form EWMA decay (default 8.0).
        half_life_short: half-life in GWs for short-form EWMA decay (default None = flat).
        data_root: root data directory.

    Returns:
        pd.DataFrame with one row per player, columns:
            player_code, web_name, team, position,
            long_form_minutes, long_form_xg90, long_form_xa90, ...,
            short_form_minutes, short_form_xg90, short_form_xa90, ...
    """
    # Load the ID map for the target season
    id_map = _load_id_map(season, data_root)

    # Long-form: full season(s) to date with EWMA decay
    long_form = compute_player_form(season, gw, window_gws=None,
                                     half_life=half_life_long,
                                     data_root=data_root)

    # Short-form: last N gameweeks
    short_form = compute_player_form(season, gw, window_gws=short_form_window,
                                      half_life=half_life_short,
                                      data_root=data_root)

    # Join id_map to get player code
    if long_form.empty and short_form.empty:
        return pd.DataFrame()

    # Merge on 'code' (the cross-season stable player code)
    result = id_map.copy()
    if not long_form.empty:
        lf_cols = {col: 'long_form_' + col for col in long_form.columns
                   if col not in ('code', 'element')}
        long_renamed = long_form.drop(columns=['element'], errors='ignore').rename(columns=lf_cols)
        result = result.merge(long_renamed, on='code', how='left')

    # Merge short-form
    if not short_form.empty:
        sf_cols = {col: 'short_form_' + col for col in short_form.columns
                   if col not in ('code', 'element')}
        short_renamed = short_form.drop(columns=['element'], errors='ignore').rename(columns=sf_cols)
        result = result.merge(short_renamed, on='code', how='left')

    # Rename for output clarity
    rename_map = {
        'code': 'player_code',
        'element_type': 'position',
    }
    result = result.rename(columns=rename_map)

    # Map position codes to names
    pos_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    if 'position' in result.columns:
        result['position'] = result['position'].map(pos_map).fillna('UNK')

    return result


def build_team_form_dataset(season, gw, short_form_window=6,
                             half_life_long=DEFAULT_HALF_LIFE,
                             half_life_short=None,
                             data_root='data'):
    """Build team-level form with long-form (EWMA decayed) and short-form xG/xGC rates.

    Args:
        season: current season.
        gw: current gameweek.
        short_form_window: short-form window size.
        half_life_long: half-life in GWs for long-form EWMA decay (default 8.0).
        half_life_short: half-life in GWs for short-form EWMA decay (default None = flat).
        data_root: root data directory.

    Returns:
        pd.DataFrame with columns: team, team_long_form_xg90,
        team_long_form_xgc90, team_short_form_xg90, team_short_form_xgc90.
    """
    long_team = compute_team_form(season, gw, window_gws=None,
                                   half_life=half_life_long,
                                   data_root=data_root)
    short_team = compute_team_form(season, gw, window_gws=short_form_window,
                                    half_life=half_life_short,
                                    data_root=data_root)

    if long_team.empty and short_team.empty:
        return pd.DataFrame()

    result = pd.DataFrame()
    if not long_team.empty:
        result = long_team[['team', 'team_xg90', 'team_xgc90']].rename(
            columns={'team_xg90': 'team_long_form_xg90',
                     'team_xgc90': 'team_long_form_xgc90'})

    if not short_team.empty:
        short_cols = short_team[['team', 'team_xg90', 'team_xgc90']].rename(
            columns={'team_xg90': 'team_short_form_xg90',
                     'team_xgc90': 'team_short_form_xgc90'})
        if result.empty:
            result = short_cols
        else:
            result = result.merge(short_cols, on='team', how='outer')

    return result
