"""Schema Validator & Data Integrity Subsystem for FPL Data Pipelines.

Enforces strict structural contracts, type checks, and column presence across all
intermediate and final CSV/JSON artifacts (players_raw, merged_gw, model_dataset,
predictions, fixture_predictions) to prevent silent data corruption and schema drift.
"""
from typing import Dict, List, Optional, Set, Tuple, Union
import pandas as pd


class SchemaValidationError(Exception):
    """Raised when a DataFrame or dataset violates its required OKF schema."""
    pass


# Canonical Schema Requirements
REQUIRED_SCHEMAS: Dict[str, Set[str]] = {
    'players_raw': {
        'id', 'code', 'web_name', 'team', 'element_type', 'now_cost', 'status',
    },
    'merged_gw': {
        'name', 'element', 'round', 'total_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets',
    },
    'model_dataset': {
        'player_code', 'web_name', 'team', 'position', 'now_cost', 'status',
        'short_form_minutes', 'long_form_minutes',
    },
    'predictions': {
        'player_code', 'web_name', 'team', 'position', 'now_cost',
        'p_start', 'p_app', 'p_60_plus',
        'c1_app_1_60', 'c2_app_60_plus', 'c3_saves', 'c4_yellow_cards',
        'c5_red_cards', 'c6_bonus', 'c7_assists', 'c8_goals',
        'c9_clean_sheets', 'c10_goals_conceded', 'c11_defensive_contributions',
        'expected_points',
    },
    'fixture_predictions': {
        'player_code', 'web_name', 'team', 'position', 'now_cost',
        'fixture_opponent', 'fixture_venue', 'fixture_fdr',
        'fixture_attack_mult', 'fixture_xgc90',
        'c1_app_1_60', 'c2_app_60_plus', 'c3_saves', 'c4_yellow_cards',
        'c5_red_cards', 'c6_bonus', 'c7_assists', 'c8_goals',
        'c9_clean_sheets', 'c10_goals_conceded', 'c11_defensive_contributions',
        'expected_points',
    },
}


def validate_dataframe_schema(
    df: pd.DataFrame,
    schema_name: str,
    raise_error: bool = False,
) -> Tuple[bool, List[str]]:
    """Validate that a DataFrame contains all required columns for a given schema.

    Args:
        df: pandas DataFrame to validate.
        schema_name: one of 'players_raw', 'merged_gw', 'model_dataset', 'predictions', 'fixture_predictions'.
        raise_error: if True, raises SchemaValidationError on failure.

    Returns:
        Tuple of (is_valid, list_of_error_strings).
    """
    errors: List[str] = []

    if not isinstance(df, pd.DataFrame):
        errors.append(f"Input is not a pandas DataFrame (got {type(df)})")
        if raise_error:
            raise SchemaValidationError(errors[0])
        return False, errors

    if df.empty:
        errors.append(f"DataFrame for schema '{schema_name}' is empty (0 rows)")
        if raise_error:
            raise SchemaValidationError(errors[0])
        return False, errors

    expected_cols = REQUIRED_SCHEMAS.get(schema_name)
    if not expected_cols:
        errors.append(f"Unknown schema name '{schema_name}'. Valid schemas: {list(REQUIRED_SCHEMAS.keys())}")
        if raise_error:
            raise SchemaValidationError(errors[0])
        return False, errors

    actual_cols = set(df.columns)
    missing_cols = expected_cols - actual_cols

    if missing_cols:
        msg = f"Schema '{schema_name}' validation failed: missing required columns {sorted(list(missing_cols))}"
        errors.append(msg)
        if raise_error:
            raise SchemaValidationError(msg)

    # Basic non-null check on primary key
    if 'player_code' in df.columns:
        null_codes = df['player_code'].isnull().sum()
        if null_codes > 0:
            msg = f"Schema '{schema_name}' contains {null_codes} null player_code entries"
            errors.append(msg)
            if raise_error:
                raise SchemaValidationError(msg)

    is_valid = len(errors) == 0
    return is_valid, errors
