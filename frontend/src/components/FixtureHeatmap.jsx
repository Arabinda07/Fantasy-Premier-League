import React, { useState, useMemo } from 'react';
import { GridNine, Lightning } from '@phosphor-icons/react';

export default function FixtureHeatmap({ fixtures, teams }) {
  const [gwWindow, setGwWindow] = useState(6);

  // Build matrix: team_name -> [GW1, GW2, ... GW38]
  const matrix = useMemo(() => {
    if (!fixtures || !teams) return [];

    const teamList = teams.map(t => ({
      id: t.id,
      name: t.name,
      short_name: t.short_name
    }));

    const result = teamList.map(team => {
      const teamFixtures = [];
      for (let gw = 1; gw <= 38; gw++) {
        const match = fixtures.find(
          f => f.event === gw && (f.team_h === team.id || f.team_a === team.id)
        );

        if (match) {
          const isHome = match.team_h === team.id;
          const oppShort = isHome ? match.away_short : match.home_short;
          const diff = isHome ? match.team_h_difficulty : match.team_a_difficulty;
          teamFixtures.push({
            gw,
            isHome,
            oppShort,
            diff: diff || 3,
            label: `${oppShort} (${isHome ? 'H' : 'A'})`
          });
        } else {
          teamFixtures.push({
            gw,
            isHome: false,
            oppShort: 'BLANK',
            diff: 0,
            label: 'Blank'
          });
        }
      }

      const currentGw = 2;
      const nextN = teamFixtures.slice(currentGw - 1, currentGw - 1 + gwWindow);
      const avgDiff = nextN.reduce((acc, f) => acc + (f.diff || 3), 0) / (nextN.length || 1);

      return {
        ...team,
        fixtures: teamFixtures,
        avgDiff
      };
    });

    // Sort by easiest upcoming run
    return result.sort((a, b) => a.avgDiff - b.avgDiff);
  }, [fixtures, teams, gwWindow]);

  const fdrClass = (diff) => {
    if (diff === 1) return 'fdr-1';
    if (diff === 2) return 'fdr-2';
    if (diff === 3) return 'fdr-3';
    if (diff === 4) return 'fdr-4';
    if (diff >= 5) return 'fdr-5';
    return '';
  };

  return (
    <div className="view-fluid">
      {/* Ticker Header & Controls Bar */}
      <div className="ticker-controls-bar">
        <div className="ticker-title-group">
          <h3 className="ticker-title">
            <GridNine size={18} weight="bold" />
            <span>Fixture Schedule & Difficulty Ticker</span>
          </h3>
          <div className="ticker-subtitle">
            Teams ranked from easiest to toughest fixture run over the next {gwWindow} gameweeks (GW2–GW{1 + gwWindow}).
          </div>
        </div>

        <div className="ticker-window-controls" role="group" aria-label="Select fixture run lookahead">
          <span className="ticker-window-label font-mono">LOOKAHEAD:</span>
          <div className="segmented-chip-rail">
            {[3, 5, 8, 12].map(w => (
              <button
                key={w}
                type="button"
                onClick={() => setGwWindow(w)}
                aria-label={`Lookahead window: ${w} gameweeks`}
                aria-pressed={gwWindow === w}
                className={`segmented-chip-btn ${gwWindow === w ? 'active' : ''}`}
              >
                <span>{w} GWs</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="data-table-container">
        <div className="table-scroll-wrapper">
          <table className="heatmap-table" aria-label="Premier League 38 Gameweek Fixture Difficulty Table">
            <thead>
              <tr>
                <th className="sticky-col team-col">Team</th>
                <th className="avg-col font-mono">FDR Avg</th>
                {Array.from({ length: 38 }, (_, i) => i + 1).map(gw => (
                  <th key={gw} className={`gw-col font-mono ${gw === 2 ? 'current-gw-header' : ''}`}>
                    GW{gw}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((team, idx) => (
                <tr key={team.id || team.name}>
                  <td className="sticky-col team-cell">
                    <span className="rank-num font-mono">{idx + 1}</span>
                    <span className="team-name">{team.name}</span>
                  </td>
                  <td className="avg-cell font-mono">
                    <span className="avg-badge" style={{ color: team.avgDiff <= 2.6 ? 'var(--accent-emerald)' : team.avgDiff >= 3.6 ? 'var(--accent-crimson)' : 'var(--text-primary)' }}>
                      {team.avgDiff.toFixed(2)}
                    </span>
                  </td>
                  {team.fixtures.map(f => (
                    <td key={f.gw} className={`fdr-cell ${fdrClass(f.diff)} ${f.gw === 2 ? 'current-gw-col' : ''}`}>
                      <div className="fdr-cell-content">
                        <span className="opp-name font-mono">{f.oppShort}</span>
                        <span className="venue-tag font-mono">{f.isHome ? 'H' : 'A'}</span>
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
