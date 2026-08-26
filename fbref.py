import requests
from bs4 import BeautifulSoup
from bs4 import Comment
import time
import csv
import os
import pandas as pd


# ---------------------------------------------------------------------------
# Legacy classes — kept for backward compatibility but no longer used by the
# new fetch_*/summarize_* interface below.
# ---------------------------------------------------------------------------

class MatchData:
    def __init__(self) -> None:
        self.comp = ""
        self.date = ""
        self.round = ""
        self.data = {}


class PlayerData:
    def __init__(self) -> None:
        self.data = []
        self.base_url = ""
        self.matches_links = []
        self.matches = []
        self.match_stat_set = set()


# ---------------------------------------------------------------------------
# Low-level HTTP helpers
# ---------------------------------------------------------------------------

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}


def _get_with_retry(url, session=None, max_retries=3, backoff=2):
    """Fetch a URL with retry-on-non-200.

    Args:
        url: the URL to fetch.
        session: optional requests.Session (for shared retry policy / test injection).
        max_retries: number of retries before giving up.
        backoff: seconds to sleep between retries.

    Returns:
        The response text (HTML string).
    """
    getter = session if session else requests
    attempts = 0
    while True:
        print("Getting data for: " + url)
        try:
            response = getter.get(url, headers=DEFAULT_HEADERS, timeout=10)
            if response.status_code == 200:
                return response.text
            if response.status_code == 403:
                raise Exception(f"FBref returned 403 Forbidden (Cloudflare bot protection active on {url})")
        except Exception as req_err:
            if "403 Forbidden" in str(req_err):
                raise
            print(f"Request attempt failed ({req_err}), retrying...")

        attempts += 1
        if attempts >= max_retries:
            raise Exception("Failed after " + str(max_retries) + " retries for " + url)
        time.sleep(backoff)


def _parse_comment_tables(html):
    """Extract <table> elements hidden inside HTML comments.

    FBref hides its stat tables inside HTML comments. This helper finds all
    comment nodes that contain a <table>, parses them, and returns the table
    elements.

    Args:
        html: raw HTML string.

    Returns:
        List of BeautifulSoup <table> elements.
    """
    parsed = BeautifulSoup(html, 'html.parser')
    comments = parsed.find_all(string=lambda text: isinstance(text, Comment))
    tables = []
    for c in comments:
        if '<table' in c:
            table_html = BeautifulSoup(c, 'html.parser')
            tables += table_html.find_all('table')
    return tables


def _parse_visible_tables(html):
    """Extract visible (non-commented) <table> elements from HTML."""
    parsed = BeautifulSoup(html, 'html.parser')
    return parsed.find_all('table')


# ---------------------------------------------------------------------------
# Legacy interface — preserved unchanged for any existing callers.
# ---------------------------------------------------------------------------

def get_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    html = response.text
    parsed_html =  BeautifulSoup(html, 'html.parser')
    comments = parsed_html.find_all(string=lambda text: isinstance(text, Comment))
    tables = []
    for c in comments:
        if '<table' in c:
            table_html = BeautifulSoup(c, 'html.parser')
            tables = table_html.find_all('table')
    return tables

def get_table_data(url):
    status_code = 0
    while status_code != 200:
        print("Getting data for: " + url)
        response = requests.get(url)
        status_code = response.status_code
        if status_code != 200:
            time.sleep(5)
    html = response.text
    parsed_html = BeautifulSoup(html, 'html.parser')
    tables = parsed_html.find_all('table')
    return tables[0]

def get_matches_data(player):
    tables = []
    for l in player.matches_links:
        tables += [get_table_data(l)]
    matches = []
    match_stat_set = set()
    for t in tables:
        for row in t.tbody.find_all('tr'):
            data = {}
            class_name = row.get('class')
            if class_name != None and len(class_name) > 0 and 'unused_sub' not in class_name:
                continue
            columns = row.find_all('td') + row.find_all('th')
            for c in columns:
                data_stat = c.get('data-stat')
                match_stat_set.add(data_stat)
                if data_stat in ['date', 'round', 'comp', 'opponent', 'squad']:
                    for i in range(len(c.contents)):
                        a_html = BeautifulSoup(str(c.contents[i]), 'html.parser')
                        a = a_html.find_all('a')
                        if len(a) > 0:
                            if len(a[0].contents) > 0:
                                data[data_stat] = a[0].contents[0]
                elif data_stat == 'match_report':
                    continue
                else:
                    if len(c.contents) == 0:
                        continue
                    data[data_stat] = c.contents[0]
            match = MatchData()
            match.date = data['date']
            match.round = data['round']
            match.comp = data['comp']
            match.data = data
            matches += [match]
    player.matches = matches
    player.match_stat_set = match_stat_set

def get_epl_players():
    tables = get_data("https://fbref.com/en/comps/9/stats/Premier-League-Stats")
    table = tables[0]
    players = {}
    stat_names = set()
    for row in table.tbody.find_all('tr'):
        class_name = row.get('class')
        if class_name != None and len(class_name) > 0:
            continue
        columns = row.find_all('td')
        base_url = ""
        matches_link = ""
        player_id = ""
        stats = {}
        for c in columns:
            data_stat = c.get('data-stat')
            if data_stat == 'player':
                a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                a = a_html.find_all('a')
                base_url = "https://fbref.com" + a[0].get('href')
                link = a[0].get('href')
                pieces = link.split('/')
                player_id = pieces[3]
                stats[data_stat] = a[0].contents[0]
                stat_names.add(data_stat)
            elif data_stat == 'squad':
                a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                a = a_html.find_all('a')
                stats[data_stat] = a[0].contents[0]
                stat_names.add(data_stat)
            elif data_stat == 'minutes':
                mins = c.contents[0]
                if ',' in mins:
                    mins = int(mins.replace(',', ''))
                stats[data_stat] = mins
                stat_names.add(data_stat)
            elif data_stat == "matches":
                a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                a = a_html.find_all('a')
                matches_link = "https://fbref.com" + a[0].get('href')
            elif data_stat == "nationality":
                continue
            else:
                stats[data_stat] = c.contents[0]
                stat_names.add(data_stat)
        player = PlayerData()
        if player_id in players:
            player = players[player_id]
        player.base_url = base_url
        if len(player.matches_links) == 0:
            player.matches_links += [matches_link]
        player.data += [stats]
        players[player_id] = player
    return players, stat_names


# ---------------------------------------------------------------------------
# New clean interface (Phase 1 spec, Component 1)
# ---------------------------------------------------------------------------

def _season_to_fbref_path(season):
    """Convert '2026-27' to FBref's URL fragment for that season.

    FBref uses the full hyphenated season string in its URLs, e.g.
    /en/comps/9/2026-2027/stats/2026-2027-Premier-League-Stats

    Args:
        season: season string in this repo's format, e.g. '2026-27'.

    Returns:
        The FBref season path component, e.g. '2026-2027'.
    """
    parts = season.split('-')
    start_year = parts[0]
    end_year_short = parts[1]
    # Convert '27' -> '2027' by taking the century from start_year
    end_year = start_year[:2] + end_year_short
    return start_year + '-' + end_year


def fetch_season_overview(season, session=None):
    """Fetch the season overview table from FBref for all Premier League players.

    Replaces the scrape half of get_epl_players(). Returns a DataFrame with
    one row per player and columns for each stat, plus 'fbref_id' and
    'matches_url' columns.

    Args:
        season: season string, e.g. '2026-27'.
        session: optional requests.Session for retry policy / test injection.

    Returns:
        pd.DataFrame with one row per player-squad combination.
    """
    fbref_season = _season_to_fbref_path(season)
    url = ("https://fbref.com/en/comps/9/" + fbref_season
           + "/stats/" + fbref_season + "-Premier-League-Stats")

    html = _get_with_retry(url, session=session)
    tables = _parse_comment_tables(html)
    if not tables:
        raise Exception("No comment-hidden tables found at " + url)
    table = tables[0]

    rows_data = []
    for row in table.tbody.find_all('tr'):
        class_name = row.get('class')
        if class_name is not None and len(class_name) > 0:
            continue
        columns = row.find_all('td')
        stats = {}
        fbref_id = ""
        matches_url = ""
        for c in columns:
            data_stat = c.get('data-stat')
            if data_stat == 'player':
                a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                a = a_html.find_all('a')
                link = a[0].get('href')
                fbref_id = link.split('/')[3]
                stats['player'] = a[0].contents[0]
            elif data_stat == 'squad':
                a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                a = a_html.find_all('a')
                stats['squad'] = a[0].contents[0]
            elif data_stat == 'minutes':
                mins = c.contents[0] if len(c.contents) > 0 else '0'
                if isinstance(mins, str) and ',' in mins:
                    mins = int(mins.replace(',', ''))
                stats['minutes'] = mins
            elif data_stat in ('matches', 'nationality'):
                if data_stat == 'matches' and len(c.contents) > 0:
                    a_html = BeautifulSoup(str(c.contents[0]), 'html.parser')
                    a = a_html.find_all('a')
                    if a:
                        matches_url = "https://fbref.com" + a[0].get('href')
                continue
            else:
                if len(c.contents) > 0:
                    stats[data_stat] = c.contents[0]
        stats['fbref_id'] = fbref_id
        stats['matches_url'] = matches_url
        rows_data.append(stats)

    return pd.DataFrame(rows_data)


def fetch_player_match_log(player_id, season, session=None):
    """Fetch a single player's match log from FBref.

    The HTML-comment unwrapping and data-stat column dispatch are entirely
    behind this call — a caller doesn't need to know either quirk exists.

    Rows are kept if they have no class (normal match entry) or if their
    class is 'unused_sub'. All other classed rows (e.g. dnp, injury) are
    dropped.

    Args:
        player_id: FBref player ID string (e.g. '1f44ac21').
        season: season string, e.g. '2026-27'.
        session: optional requests.Session.

    Returns:
        pd.DataFrame with one row per match, columns from the data-stat
        attributes of the table.
    """
    fbref_season = _season_to_fbref_path(season)
    url = ("https://fbref.com/en/players/" + player_id
           + "/matchlogs/" + fbref_season + "/summary/"
           + player_id + "-Match-Logs")

    html = _get_with_retry(url, session=session)
    # Match log tables are in the visible DOM, not hidden in comments
    tables = _parse_visible_tables(html)
    if not tables:
        return pd.DataFrame()

    table = tables[0]
    if not table.tbody:
        return pd.DataFrame()

    matches = []
    for row in table.tbody.find_all('tr'):
        data = {}
        class_name = row.get('class')
        # Keep: no class (normal entry) or 'unused_sub'
        if class_name is not None and len(class_name) > 0 and 'unused_sub' not in class_name:
            continue
        # Track whether this row is an unused_sub
        is_unused_sub = (class_name is not None and 'unused_sub' in class_name)
        data['is_unused_sub'] = is_unused_sub

        columns = row.find_all('td') + row.find_all('th')
        for c in columns:
            data_stat = c.get('data-stat')
            if data_stat is None:
                continue
            if data_stat in ['date', 'round', 'comp', 'opponent', 'squad']:
                # Extract text from nested <a> tags
                for content in c.contents:
                    a_html = BeautifulSoup(str(content), 'html.parser')
                    a = a_html.find_all('a')
                    if a and a[0].contents:
                        data[data_stat] = str(a[0].contents[0])
                        break
            elif data_stat == 'match_report':
                continue
            else:
                if len(c.contents) > 0:
                    data[data_stat] = str(c.contents[0])
        if data:
            matches.append(data)

    return pd.DataFrame(matches)


def summarize_season(match_log_df):
    """Aggregate a player's match log into a season summary.

    Computes counts of starts, substitute appearances, and unused-sub
    appearances for the season.

    The three-way split uses:
    - 'is_unused_sub' flag (from fetch_player_match_log) for unused subs.
    - 'game_started' column if available, else falls back to minutes > 0
      for distinguishing starts from sub appearances.

    Args:
        match_log_df: DataFrame from fetch_player_match_log.

    Returns:
        pd.Series with keys: squads_made, starts, subs, unused_subs, minutes.
    """
    if match_log_df.empty:
        return pd.Series({
            'squads_made': 0,
            'starts': 0,
            'subs': 0,
            'unused_subs': 0,
            'minutes': 0,
        })

    df = match_log_df.copy()

    # Count unused subs
    unused_subs = int(df['is_unused_sub'].sum()) if 'is_unused_sub' in df.columns else 0

    # Players who were not unused subs — they actually featured (or at least
    # were in the matchday squad and played)
    featured = df[~df.get('is_unused_sub', False)].copy() if 'is_unused_sub' in df.columns else df.copy()

    # Parse minutes to numeric
    if 'minutes' in featured.columns:
        featured['minutes_num'] = pd.to_numeric(featured['minutes'], errors='coerce').fillna(0).astype(int)
    else:
        featured['minutes_num'] = 0

    # Determine starts vs subs
    if 'game_started' in featured.columns:
        featured['_started'] = featured['game_started'].astype(str).str.strip().isin(['True', 'true', '1', 'Yes'])
    else:
        # Fallback: if 'minutes' > 0 and the player wasn't an unused sub,
        # we need another heuristic. FBref typically has a 'game_started'
        # column. Without it, we infer: all featured rows with minutes >= 45
        # are likely starts (rough heuristic — to be verified by hand).
        featured['_started'] = featured['minutes_num'] >= 45

    starts = int(featured['_started'].sum())
    subs = len(featured) - starts
    total_minutes = int(featured['minutes_num'].sum())

    squads_made = starts + subs + unused_subs

    return pd.Series({
        'squads_made': squads_made,
        'starts': starts,
        'subs': subs,
        'unused_subs': unused_subs,
        'minutes': total_minutes,
    })


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------

def main():
    """Run the full FBref scrape for the current season.

    Usage: python fbref.py [season]
    Defaults to '2026-27' if no argument given.
    """
    import sys
    season = sys.argv[1] if len(sys.argv) > 1 else '2026-27'
    out_dir = os.path.join('data', season, 'fbref')
    os.makedirs(out_dir, exist_ok=True)

    print("Fetching FBref season overview for " + season + "...")
    overview_df = fetch_season_overview(season)

    # Write overview CSV with sorted columns
    overview_path = os.path.join(out_dir, 'fbref_overview.csv')
    overview_df.to_csv(overview_path, index=False,
                       columns=sorted(overview_df.columns))
    print("Wrote overview to " + overview_path)

    # Per-player match logs + season summary
    summaries = []
    for _, row in overview_df.iterrows():
        pid = row.get('fbref_id', '')
        if not pid:
            continue
        player_name = str(row.get('player', pid))
        print("Fetching match log for " + player_name + " (" + pid + ")...")
        match_log = fetch_player_match_log(pid, season)

        # Write per-player match CSV with sorted columns
        if not match_log.empty:
            player_csv = os.path.join(out_dir, pid + '.csv')
            match_log.to_csv(player_csv, index=False,
                             columns=sorted(match_log.columns))

        summary = summarize_season(match_log)
        summary['fbref_id'] = pid
        summary['player'] = player_name
        summary['squad'] = str(row.get('squad', ''))
        summaries.append(summary)

    # Write combined season summary
    if summaries:
        summary_df = pd.DataFrame(summaries)
        summary_path = os.path.join(out_dir, 'season_summary.csv')
        summary_df.to_csv(summary_path, index=False,
                          columns=sorted(summary_df.columns))
        print("Wrote season summary to " + summary_path)

    print("FBref scrape complete for " + season)


if __name__ == '__main__':
    main()