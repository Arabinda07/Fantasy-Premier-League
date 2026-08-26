"""Unit tests for Data Pipeline Schema Validator (model/schema_validator.py)."""
import pandas as pd
import pytest

from model.schema_validator import (
    validate_dataframe_schema,
    SchemaValidationError,
    REQUIRED_SCHEMAS,
)


class TestSchemaValidator:
    """Test schema validation contracts across all FPL pipeline artifact types."""

    def test_valid_players_raw_schema(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'code': [1001, 1002],
            'web_name': ['Raya', 'Gabriel'],
            'team': [1, 1],
            'element_type': [1, 2],
            'now_cost': [55, 60],
            'status': ['a', 'a'],
        })
        is_valid, errors = validate_dataframe_schema(df, 'players_raw')
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_column_raises_error(self):
        df = pd.DataFrame({
            'id': [1],
            'web_name': ['Raya'],
            'team': [1],
            # missing 'code', 'element_type', 'now_cost', 'status'
        })
        is_valid, errors = validate_dataframe_schema(df, 'players_raw')
        assert is_valid is False
        assert len(errors) > 0
        assert "missing required columns" in errors[0]

        with pytest.raises(SchemaValidationError):
            validate_dataframe_schema(df, 'players_raw', raise_error=True)

    def test_empty_dataframe_fails(self):
        df = pd.DataFrame(columns=['id', 'code', 'web_name', 'team', 'element_type', 'now_cost', 'status'])
        is_valid, errors = validate_dataframe_schema(df, 'players_raw')
        assert is_valid is False
        assert "empty (0 rows)" in errors[0]

    def test_valid_predictions_schema(self):
        cols = REQUIRED_SCHEMAS['predictions']
        row_data = {c: [1.0] for c in cols}
        row_data['player_code'] = [154561]
        row_data['web_name'] = ['Raya']
        row_data['team'] = ['Arsenal']
        row_data['position'] = ['GK']
        row_data['now_cost'] = [55]

        df = pd.DataFrame(row_data)
        is_valid, errors = validate_dataframe_schema(df, 'predictions')
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_fixture_predictions_schema(self):
        cols = REQUIRED_SCHEMAS['fixture_predictions']
        row_data = {c: [1.0] for c in cols}
        row_data['player_code'] = [154561]
        row_data['web_name'] = ['Raya']
        row_data['team'] = ['Arsenal']
        row_data['position'] = ['GK']
        row_data['now_cost'] = [55]
        row_data['fixture_opponent'] = ['Aston Villa']
        row_data['fixture_venue'] = ['A']
        row_data['fixture_fdr'] = [3]

        df = pd.DataFrame(row_data)
        is_valid, errors = validate_dataframe_schema(df, 'fixture_predictions')
        assert is_valid is True
        assert len(errors) == 0
