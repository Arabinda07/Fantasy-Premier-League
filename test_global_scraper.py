from global_scraper import compute_value_per_m


def test_normal_case():
    assert compute_value_per_m(cost_raw='100', pts_raw='150') == 15.0


def test_zero_cost_returns_blank():
    assert compute_value_per_m(cost_raw='0', pts_raw='150') == ''


def test_missing_values_return_blank():
    assert compute_value_per_m(cost_raw='', pts_raw='150') == ''
    assert compute_value_per_m(cost_raw='100', pts_raw='') == ''
    assert compute_value_per_m(cost_raw=None, pts_raw=None) == ''


def test_non_numeric_input_returns_blank():
    assert compute_value_per_m(cost_raw='not-a-number', pts_raw='150') == ''
    assert compute_value_per_m(cost_raw='100', pts_raw='not-a-number') == ''
