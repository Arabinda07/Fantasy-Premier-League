import csv
import os

from getters import get_data, get_fixtures_data, get_individual_player_data
from parsers import (
    parse_players,
    parse_fixtures,
    parse_team_data,
    parse_player_history,
    parse_player_gw_history,
)
from collector import collect_gw, merge_gw
from positions import POSITION_NAMES


def compute_value_per_m(cost_raw, pts_raw):
    """Points per million spent (now_cost is in tenths of a million).

    Returns '' if cost or points are missing, non-numeric, or cost is zero.
    """
    try:
        cost_m = float(cost_raw) / 10.0 if cost_raw not in (None, '') else None
        total_points = float(pts_raw) if pts_raw not in (None, '') else None
    except (TypeError, ValueError):
        return ''

    if cost_m and cost_m > 0 and total_points is not None:
        return round(total_points / cost_m, 1)
    return ''


def clean_players(filename, base_filename):
    """ Creates a file with only important data columns for each player

    Args:
        filename (str): Name of the file that contains the full data for each player
    """
    headers = ['first_name', 'second_name', 'goals_scored', 'assists', 'total_points', 'minutes', 'goals_conceded', 'creativity', 'influence', 'threat', 'bonus', 'bps', 'ict_index', 'clean_sheets', 'red_cards', 'yellow_cards', 'selected_by_percent', 'now_cost', 'element_type', 'value_per_m']
    fin = open(filename, 'r+', encoding='utf-8')
    outname = base_filename + 'cleaned_players.csv'
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    fout = open(outname, 'w+', encoding='utf-8', newline='')
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, headers, extrasaction='ignore')
    writer.writeheader()
    for line in reader:
        if line['element_type'] in POSITION_NAMES:
            line['element_type'] = POSITION_NAMES[line['element_type']]
        else:
            print("Unknown element type")
        line['value_per_m'] = compute_value_per_m(line.get('now_cost', ''), line.get('total_points', ''))
        writer.writerow(line)


def id_players(players_filename, base_filename):
    """ Creates a file that contains the name to id mappings for each player

    Args:
        players_filename (str): Name of the file that contains the full data for each player
    """
    headers = ['first_name', 'second_name', 'id']
    fin = open(players_filename, 'r+', encoding='utf-8')
    outname = base_filename + 'player_idlist.csv'
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    fout = open(outname, 'w+', encoding='utf-8', newline='')
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, headers, extrasaction='ignore')
    writer.writeheader()
    for line in reader:
        writer.writerow(line)


def get_player_ids(base_filename):
    """ Gets the list of all player ids and player names
    """
    filename = base_filename + 'player_idlist.csv'
    fin = open(filename, 'r+', encoding='utf-8')
    reader = csv.DictReader(fin)
    player_ids = {}
    for line in reader:
        k = int(line['id'])
        v = line['first_name'] + '_' + line['second_name']
        player_ids[k] = v
    return player_ids


def parse_data():
    """ Parse and store all the data
    """
    season = '2026-27'
    base_filename = 'data/' + season + '/'
    print("Getting data")
    data = get_data()
    print("Parsing summary data")
    parse_players(data["elements"], base_filename)
    xPoints = []
    for e in data["elements"]:
        xPoint = {}
        xPoint['id'] = e['id']
        xPoint['xP'] = e['ep_this']
        xPoints += [xPoint]
    gw_num = 0
    events = data["events"]
    for event in events:
        if event["is_current"] == True:
            gw_num = event["id"]
    print("Cleaning summary data")
    clean_players(base_filename + 'players_raw.csv', base_filename)
    print("Getting fixtures data")
    fixtures(base_filename)
    print("Getting teams data")
    parse_team_data(data["teams"], base_filename)
    print("Extracting player ids")
    id_players(base_filename + 'players_raw.csv', base_filename)
    player_ids = get_player_ids(base_filename)
    num_players = len(data["elements"])
    player_base_filename = base_filename + 'players/'
    gw_base_filename = base_filename + 'gws/'
    print("Extracting player specific data")
    for i,name in player_ids.items():
        player_data = get_individual_player_data(i)
        parse_player_history(player_data["history_past"], player_base_filename, name, i)
        parse_player_gw_history(player_data["history"], player_base_filename, name, i)
    if gw_num > 0:
        print("Writing expected points")
        with open(os.path.join(gw_base_filename, 'xP' + str(gw_num) + '.csv'), 'w+') as outf:
            w = csv.DictWriter(outf, ['id', 'xP'])
            w.writeheader()
            for xp in xPoints:
                w.writerow(xp)
        print("Collecting gw scores")
        collect_gw(gw_num, player_base_filename, gw_base_filename, base_filename)
        print("Merging gw scores")
        merge_gw(gw_num, gw_base_filename)

def fixtures(base_filename):
    data = get_fixtures_data()
    parse_fixtures(data, base_filename)

def main():
    parse_data()

if __name__ == "__main__":
    main()
