"""Tests for understat._extract_js_json — the shared JSON-extraction helper.

Uses a canned string fixture shaped like Understat's actual inline script-tag
format, so no network access is needed.
"""
import json
import codecs

import pytest
from bs4 import BeautifulSoup

# Import the private helper — it's explicitly listed as a test target in the
# Phase 1 spec because it encapsulates non-trivial parsing logic.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from understat import _extract_js_json


def _make_script_tags(js_body):
    """Wrap a JavaScript string in <script> tags and parse with BeautifulSoup."""
    html = '<html><body><script>' + js_body + '</script></body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('script')


def _encode_as_understat(obj):
    """Encode a Python object the way Understat embeds it: hex-escaped JSON
    inside a JSON.parse('...') call.

    This mirrors the real encoding: json.dumps → encode to bytes → hex-escape
    each byte.
    """
    json_str = json.dumps(obj)
    # Hex-encode every byte, matching Understat's \\xHH format
    hex_encoded = ''.join('\\x{:02X}'.format(b) for b in json_str.encode('utf-8'))
    return hex_encoded


class TestExtractJsJson:
    """Tests for _extract_js_json."""

    def test_simple_dict(self):
        """Extract a simple dict from a teamsData variable."""
        payload = {"teamA": {"title": "Arsenal", "id": 1}}
        encoded = _encode_as_understat(payload)
        js = "var teamsData = JSON.parse('" + encoded + "');"
        scripts = _make_script_tags(js)
        result = _extract_js_json(scripts, 'teamsData')
        assert result == payload

    def test_simple_list(self):
        """Extract a list (like playersData) from a script tag."""
        payload = [{"player_name": "Salah", "id": "1234"}]
        encoded = _encode_as_understat(payload)
        js = "var playersData = JSON.parse('" + encoded + "');"
        scripts = _make_script_tags(js)
        result = _extract_js_json(scripts, 'playersData')
        assert result == payload

    def test_multiple_variables(self):
        """When multiple variables exist, only the requested one is returned."""
        teams = {"t1": {"title": "Chelsea"}}
        players = [{"player_name": "Palmer"}]
        js = (
            "var teamsData = JSON.parse('" + _encode_as_understat(teams) + "');\n"
            "var playersData = JSON.parse('" + _encode_as_understat(players) + "');"
        )
        scripts = _make_script_tags(js)
        assert _extract_js_json(scripts, 'teamsData') == teams
        assert _extract_js_json(scripts, 'playersData') == players

    def test_missing_variable_returns_empty_dict(self):
        """If the requested variable doesn't exist, return {}."""
        js = "var teamsData = JSON.parse('" + _encode_as_understat({"a": 1}) + "');"
        scripts = _make_script_tags(js)
        result = _extract_js_json(scripts, 'nonExistentVar')
        assert result == {}

    def test_empty_scripts(self):
        """Empty script list returns {}."""
        result = _extract_js_json([], 'teamsData')
        assert result == {}

    def test_unicode_content(self):
        """Player names with accented/non-ASCII characters decode correctly."""
        payload = [{"player_name": "Martín Ødegaard", "id": "999"}]
        encoded = _encode_as_understat(payload)
        js = "var playersData = JSON.parse('" + encoded + "');"
        scripts = _make_script_tags(js)
        result = _extract_js_json(scripts, 'playersData')
        assert result[0]["player_name"] == "Martín Ødegaard"
