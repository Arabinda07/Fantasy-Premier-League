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
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GridNine size={18} weight="bold" />
            Fixture Schedule & Difficulty Ticker
          </h3>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Teams sorted from easiest to toughest fixture run over the next {gwWindow} gameweeks (GW2–GW{1 + gwWindow}).
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }} role="group" aria-label="Select fixture run lookahead">
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Fixture Run:</span>
          {[3, 5, 8, 12].map(w => (
            <button
              key={w}
              onClick={() => setGwWindow(w)}
              aria-label={`Lookahead window: ${w} gameweeks`}
              aria-pressed={gwWindow === w}
              className={`pos-filter-btn ${gwWindow === w ? 'active' : ''}`}
            >
              {w} Gameweeks
            </button>
          ))}
        </div>
      </div>

      <div className="data-table-container">
        <div className="table-scroll-wrapper">
          <table className="data-table" style={{ whiteSpace: 'nowrap' }}>
            <thead>
              <tr>
                <th style={{ position: 'sticky', left: 0, zIndex: 20 }}>Club</th>
                <th style={{ textAlign: 'center' }}>Avg Difficulty</th>
                {Array.from({ length: 12 }, (_, i) => i + 1).map(gw => (
                  <th key={gw} style={{ textAlign: 'center', background: gw === 2 ? 'rgba(16, 185, 129, 0.15)' : undefined }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', justifyContent: 'center' }}>
                      GW{gw}
                      {gw === 2 && <Lightning size={12} weight="fill" color="var(--accent-emerald)" title="Current Active Gameweek" />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map(team => (
                <tr key={team.id}>
                  <td style={{ position: 'sticky', left: 0, zIndex: 10, background: 'var(--bg-surface-1)', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <span className="team-name-full">{team.name}</span>
                    <span className="team-name-short">{team.short_name || team.name.slice(0, 3).toUpperCase()}</span>
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center', fontWeight: 700, color: team.avgDiff <= 2.5 ? 'var(--accent-emerald)' : (team.avgDiff >= 3.8 ? 'var(--accent-crimson)' : 'var(--text-secondary)') }}>
                    {team.avgDiff.toFixed(2)}
                  </td>
                  {team.fixtures.slice(0, 12).map(f => (
                    <td key={f.gw} style={{ padding: '4px', textAlign: 'center' }}>
                      <div
                        className={`fdr-cell ${fdrClass(f.diff)}`}
                        title={`GW${f.gw}: ${f.label} — FDR Difficulty ${f.diff}/5`}
                        aria-label={`Gameweek ${f.gw} vs ${f.label}, difficulty ${f.diff} of 5`}
                      >
                        {f.label}
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
