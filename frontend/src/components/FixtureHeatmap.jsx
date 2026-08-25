import React, { useState, useMemo } from 'react';

export default function FixtureHeatmap({ fixtures, teams }) {
  const [filterMode, setFilterMode] = useState('ALL');
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
        // Find match for this team in this GW
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
            label: 'BLANK'
          });
        }
      }

      // Compute average difficulty over next N gameweeks (GW2 to GW2 + window)
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            38-GAMEWEEK FIXTURE DIFFICULTY HEATMAP (FDR SCALE 1 TO 5)
          </h3>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Sorted by easiest fixture schedule over the next {gwWindow} Gameweeks (GW2–GW{1 + gwWindow})
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Lookahead Run:</span>
          {[3, 5, 8, 12].map(w => (
            <button
              key={w}
              onClick={() => setGwWindow(w)}
              style={{
                background: gwWindow === w ? 'var(--accent-emerald)' : 'var(--bg-surface-2)',
                color: gwWindow === w ? '#06261C' : 'var(--text-secondary)',
                border: '1px solid var(--border-subtle)',
                padding: '4px 10px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                borderRadius: 'var(--radius-xs)',
                cursor: 'pointer'
              }}
            >
              {w} GWs
            </button>
          ))}
        </div>
      </div>

      <div className="data-table-container" style={{ overflowX: 'auto' }}>
        <table className="data-table" style={{ whiteSpace: 'nowrap' }}>
          <thead>
            <tr>
              <th style={{ position: 'sticky', left: 0, zIndex: 20, background: 'var(--bg-surface-2)' }}>Club</th>
              <th style={{ textAlign: 'center' }}>Next {gwWindow} Avg FDR</th>
              {Array.from({ length: 12 }, (_, i) => i + 1).map(gw => (
                <th key={gw} style={{ textAlign: 'center', background: gw === 2 ? 'rgba(16, 185, 129, 0.15)' : undefined }}>
                  GW{gw} {gw === 2 ? '⚡' : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map(team => (
              <tr key={team.id}>
                <td style={{ position: 'sticky', left: 0, zIndex: 10, background: 'var(--bg-surface-1)', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {team.name}
                </td>
                <td className="font-mono" style={{ textAlign: 'center', fontWeight: 700, color: team.avgDiff <= 2.5 ? 'var(--accent-emerald)' : (team.avgDiff >= 3.8 ? 'var(--accent-crimson)' : 'var(--text-secondary)') }}>
                  {team.avgDiff.toFixed(2)}
                </td>
                {team.fixtures.slice(0, 12).map(f => (
                  <td key={f.gw} style={{ padding: '4px', textAlign: 'center' }}>
                    <div className={`fdr-cell ${fdrClass(f.diff)}`}>
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
  );
}
