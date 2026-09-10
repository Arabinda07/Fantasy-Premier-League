import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import marimo as mo
    return json, mo


@app.cell
def _(mo):
    mo.md(
        """
        # 🏟️ Premier League Historical Vault — Interactive Simulation Lab
        **Client-Side Python & SQL Sandbox (WebAssembly / Pyodide)**

        This laboratory runs entirely in your browser using WebAssembly. No remote Python server or backend API is required.
        Adjust scoring models, simulate counterfactual captaincy rules, or run SQL queries across 10 seasons of Premier League data.
        """
    )
    return


@app.cell
def _(json):
    # Embedded compact historical dataset for instantaneous client-side execution
    import urllib.request

    try:
        req = urllib.request.urlopen("/src/data/historical_vault.json")
        vault_data = json.loads(req.read().decode("utf-8"))
    except Exception:
        # Fallback inline minimal dataset if accessed outside Vite root
        vault_data = {
            "seasons": [
                {"season": "2024-25", "total_goals": 1081, "top_scorer_name": "M.Salah", "top_scorer_goals": 29, "top_points_name": "M.Salah", "top_points": 344},
                {"season": "2023-24", "total_goals": 1196, "top_scorer_name": "Haaland", "top_scorer_goals": 27, "top_points_name": "Palmer", "top_points": 244},
                {"season": "2022-23", "total_goals": 1038, "top_scorer_name": "Haaland", "top_scorer_goals": 36, "top_points_name": "Haaland", "top_points": 272},
                {"season": "2021-22", "total_goals": 1037, "top_scorer_name": "Son", "top_scorer_goals": 23, "top_points_name": "Salah", "top_points": 265},
                {"season": "2020-21", "total_goals": 986, "top_scorer_name": "Kane", "top_scorer_goals": 23, "top_points_name": "Fernandes", "top_points": 244},
                {"season": "2019-20", "total_goals": 1001, "top_scorer_name": "Vardy", "top_scorer_goals": 23, "top_points_name": "De Bruyne", "top_points": 251},
                {"season": "2018-19", "total_goals": 1038, "top_scorer_name": "Aubameyang", "top_scorer_goals": 22, "top_points_name": "Salah", "top_points": 259},
                {"season": "2017-18", "total_goals": 988, "top_scorer_name": "Salah", "top_scorer_goals": 32, "top_points_name": "Salah", "top_points": 303},
                {"season": "2016-17", "total_goals": 1029, "top_scorer_name": "Kane", "top_scorer_goals": 29, "top_points_name": "Sánchez", "top_points": 264}
            ]
        }
    return req, vault_data


@app.cell
def _(mo, vault_data):
    seasons_list = [s["season"] for s in vault_data.get("seasons", [])]
    season_picker = mo.ui.dropdown(
        options=seasons_list,
        value=seasons_list[0] if seasons_list else "2024-25",
        label="Campaign Season"
    )
    captain_mult = mo.ui.slider(
        start=1,
        stop=4,
        step=1,
        value=2,
        label="Captaincy Multiplier"
    )
    goal_pts = mo.ui.slider(
        start=4,
        stop=8,
        step=1,
        value=5,
        label="MID Goal Points"
    )

    mo.md(
        f"""
        ### ⚙️ Tactical Parameters
        {mo.as_html(mo.hstack([season_picker, captain_mult, goal_pts], justify='start', gap=2))}
        """
    )
    return captain_mult, goal_pts, season_picker, seasons_list


@app.cell
def _(captain_mult, mo, season_picker, vault_data):
    s_meta = next((s for s in vault_data.get("seasons", []) if s["season"] == season_picker.value), None)

    if s_meta:
        top_pts = s_meta["top_points"]
        simulated_pts = top_pts + (s_meta["top_points"] // 4) * (captain_mult.value - 2)
        summary_md = f"""
        ### 📊 Simulation Output: `{season_picker.value}`
        - **Golden Boot Winner**: **{s_meta['top_scorer_name']}** ({s_meta['top_scorer_goals']} goals)
        - **Official MVP**: **{s_meta['top_points_name']}** ({top_pts} pts)
        - **Simulated MVP Output ({captain_mult.value}x Captaincy)**: **~{simulated_pts} pts**
        - **League Total Goals**: {s_meta['total_goals']:,} goals
        """
    else:
        summary_md = "Select a valid season above."

    mo.md(summary_md)
    return s_meta, simulated_pts, summary_md, top_pts


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ### 🔍 In-Browser SQL Explorer (SQLite)
        Run queries across historical Premier League records directly in WebAssembly:
        """
    )
    return


@app.cell
def _(mo, vault_data):
    import sqlite3

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE seasons (season TEXT, total_goals INT, top_scorer TEXT, goals INT, mvp TEXT, points INT);")

    for s in vault_data.get("seasons", []):
        cursor.execute(
            "INSERT INTO seasons VALUES (?, ?, ?, ?, ?, ?)",
            (s["season"], s["total_goals"], s.get("top_scorer_name", ""), s.get("top_scorer_goals", 0), s.get("top_points_name", ""), s.get("top_points", 0))
        )
    conn.commit()

    query_input = mo.ui.text_area(
        value="SELECT season, mvp, points, top_scorer, goals FROM seasons ORDER BY points DESC LIMIT 5;",
        label="Arbitrary SQL Query",
        rows=3
    )
    query_input
    return conn, cursor, query_input, sqlite3


@app.cell
def _(conn, mo, query_input):
    try:
        cur = conn.cursor()
        cur.execute(query_input.value)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description] if cur.description else []
        table_html = mo.ui.table([dict(zip(cols, r)) for r in rows])
    except Exception as err:
        table_html = mo.md(f"⚠️ **SQL Error**: `{err}`")

    table_html
    return cols, cur, rows, table_html


if __name__ == "__main__":
    app.run()
