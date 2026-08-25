import requests
import json
from bs4 import BeautifulSoup
import re
import codecs
import pandas as pd
import os
import csv


def _season_to_understat_year(season):
    """Convert this repo's season string (e.g. '2026-27') to Understat's URL year.

    Understat uses the season's start year in its URLs, e.g.
    https://understat.com/league/EPL/2026 for the 2026-27 season.
    """
    return season.split('-')[0]


def _extract_js_json(scripts, var_name):
    """Extract a JSON object from Understat's inline script tags.

    Understat embeds data as JavaScript variables like:
        var teamsData = JSON.parse('\\x7B...hex-encoded JSON...\\x7D');

    This helper finds the variable named `var_name` (e.g. 'teamsData'),
    pulls out the hex-encoded JSON payload, decodes it, and returns the
    parsed Python dict/list.

    Args:
        scripts: list of BeautifulSoup <script> tag elements.
        var_name: the JavaScript variable name to extract (without 'var '),
                  e.g. 'teamsData', 'playersData', 'matchesData'.

    Returns:
        The parsed JSON object (dict or list), or an empty dict if the
        variable is not found in any script tag.
    """
    target = 'var ' + var_name
    for script in scripts:
        for c in script.contents:
            # Split by lines first so multiple assignments in one script tag
            # are handled correctly, then split each line on the first '='
            # only (some JSON payloads contain '=' inside the encoded data).
            for line in c.split('\n'):
                split_data = line.split('=', 1)
                if len(split_data) < 2:
                    continue
                data = split_data[0].strip()
                if data == target:
                    content = re.findall(r'JSON\.parse\(\'(.*)\'\)', split_data[1])
                    decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                    return json.loads(decoded_content)
    return {}


def get_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    html = response.text
    parsed_html = BeautifulSoup(html, 'html.parser')
    scripts = parsed_html.findAll('script')
    filtered_scripts = []
    for script in scripts:
        if len(script.contents) > 0:
            filtered_scripts += [script]
    return scripts


def get_epl_data(season='2026-27'):
    """Fetch team and player data from Understat for the given season.

    Args:
        season: season string in this repo's format, e.g. '2026-27'.
                Defaults to the current season.

    Returns:
        Tuple of (teamData dict, playerData list).
    """
    year = _season_to_understat_year(season)
    scripts = get_data("https://understat.com/league/EPL/" + year)
    teamData = _extract_js_json(scripts, 'teamsData')
    playerData = _extract_js_json(scripts, 'playersData')
    return teamData, playerData


def get_player_data(id):
    scripts = get_data("https://understat.com/player/" + str(id))
    matchesData = _extract_js_json(scripts, 'matchesData')
    shotsData = _extract_js_json(scripts, 'shotsData')
    groupsData = _extract_js_json(scripts, 'groupsData')
    return matchesData, shotsData, groupsData


def parse_epl_data(outfile_base, season='2026-27'):
    """Scrape Understat EPL data and write per-team and per-player CSVs.

    Args:
        outfile_base: directory to write output CSVs into.
        season: season string, e.g. '2026-27'.
    """
    os.makedirs(outfile_base, exist_ok=True)
    teamData, playerData = get_epl_data(season)
    new_team_data = []
    for t,v in teamData.items():
        new_team_data += [v]
    for data in new_team_data:
        team_frame = pd.DataFrame.from_records(data["history"])
        team = data["title"].replace(' ', '_')
        team_frame.to_csv(os.path.join(outfile_base, 'understat_' + team + '.csv'), index=False)
    player_frame = pd.DataFrame.from_records(playerData)
    player_frame.to_csv(os.path.join(outfile_base, 'understat_player.csv'), index=False)
    for d in playerData:
        matches, shots, groups = get_player_data(int(d['id']))
        indi_player_frame = pd.DataFrame.from_records(matches)
        player_name = d['player_name']
        player_name = player_name.replace(' ', '_')
        indi_player_frame.to_csv(os.path.join(outfile_base, player_name + '_' + d['id'] + '.csv'), index=False)


class PlayerID:
    def __init__(self, us_id, fpl_id, us_name, fpl_name):
        self.us_id = str(us_id)
        self.fpl_id = str(fpl_id)
        self.us_name = us_name
        self.fpl_name = fpl_name
        

def match_ids(understat_dir, data_dir):
    """Match Understat player IDs to FPL player IDs and write id_dict.csv.

    Uses csv.writer for proper CSV escaping (handles player names with commas).
    """
    with open(os.path.join(understat_dir, 'understat_player.csv')) as understat_file:
        understat_inf = csv.DictReader(understat_file)
        ustat_players = {}
        for row in understat_inf:
            ustat_players[row['player_name']] = row['id']

    with open(os.path.join(data_dir, 'player_idlist.csv')) as fpl_file:
        fpl_players = {}
        fpl_inf = csv.DictReader(fpl_file)
        for row in fpl_inf:
            fpl_players[row['first_name'] + ' ' + row['second_name']] = row['id']
    players = []
    found = {}
    for k, v in ustat_players.items():
        if k in fpl_players:
            player = PlayerID(v, fpl_players[k], k, k)
            players += [player]
            found[k] = True
        else:
            player = PlayerID(v, -1, k, "")
            players += [player]

    for k, v in fpl_players.items():
        if k not in found:
            player = PlayerID(-1, v, "", k)
            players += [player]

    with open(os.path.join(data_dir, 'id_dict.csv'), 'w', newline='') as outf:
        writer = csv.writer(outf)
        writer.writerow(['Understat_ID', 'FPL_ID', 'Understat_Name', 'FPL_Name'])
        for p in players:
            writer.writerow([p.us_id, p.fpl_id, p.us_name, p.fpl_name])


def main():
    season = '2026-27'
    understat_dir = os.path.join('data', season, 'understat')
    data_dir = os.path.join('data', season)
    parse_epl_data(understat_dir, season)
    match_ids(understat_dir, data_dir)

if __name__ == '__main__':
    main()
