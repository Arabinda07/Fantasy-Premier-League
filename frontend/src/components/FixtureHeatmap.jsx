import React, { useState, useMemo } from 'react';
import { GridNine } from '@phosphor-icons/react';

export default function FixtureHeatmap({
  fixtures,
  fixturesData,
  teams,
  teamsData,
  selectedGw = 2,
  onOpenFixture,
  onOpenMatchup
}) {
  const [gwWindow, setGwWindow] = useState(6);

  const activeFixtures = fixtures || fixturesData || [];
  const activeTeams = teams || teamsData || [];
  const handleOpen = onOpenFixture || onOpenMatchup;

  // Build matrix: team_name -> [GW1, GW2, ... GW38]
  const matrix = useMemo(() => {
    if (!activeFixtures || activeFixtures.length === 0 || !activeTeams || activeTeams.length === 0) {
      return [];
    }

    const teamList = activeTeams.map(t => ({
      id: Number(t.id),
      name: t.name,
      short_name: t.short_name
    }));

    const teamIdToName = Object.fromEntries(activeTeams.map(t => [Number(t.id), t.name]));
    const teamIdToShort = Object.fromEntries(activeTeams.map(t => [Number(t.id), t.short_name]));

    const result = teamList.map(team => {
      const teamFixtures = [];
      for (let gw = 1; gw <= 38; gw++) {
        const match = activeFixtures.find(
          f => Number(f.event) === gw && (Number(f.team_h) === team.id || Number(f.team_a) === team.id)
        );

        if (match) {
          const isHome = Number(match.team_h) === team.id;
          const oppId = isHome ? Number(match.team_a) : Number(match.team_h);
          const oppName = match.home_team && match.away_team
            ? (isHome ? match.away_team : match.home_team)
            : (teamIdToName[oppId] || `Team ${oppId}`);
          const oppShort = match.home_short && match.away_short
            ? (isHome ? match.away_short : match.home_short)
            : (teamIdToShort[oppId] || oppName.slice(0, 3).toUpperCase());
          const diff = isHome ? Number(match.team_h_difficulty || 3) : Number(match.team_a_difficulty || 3);

          teamFixtures.push({
            gw,
            isHome,
            oppShort,
            oppName,
            diff: diff || 3,
            label: `${oppShort} (${isHome ? 'H' : 'A'})`,
            fixture_id: match.id,
            home_team: isHome ? team.name : oppName,
            away_team: isHome ? oppName : team.name,
          });
        } else {
          teamFixtures.push({
            gw,
            isHome: false,
            oppShort: 'BLANK',
            oppName: null,
            diff: 0,
            label: 'Blank'
          });
        }
      }

      const currentGw = Number(selectedGw || 2);
      const nextN = teamFixtures.slice(Math.max(0, currentGw - 1), currentGw - 1 + gwWindow);
      const avgDiff = nextN.reduce((acc, f) => acc + (f.diff || 3), 0) / (nextN.length || 1);

      return {
        ...team,
        fixtures: teamFixtures,
        avgDiff
      };
    });

    // Sort by easiest upcoming run
    return result.sort((a, b) => a.avgDiff - b.avgDiff);
  }, [activeFixtures, activeTeams, gwWindow, selectedGw]);

  const fdrClass = (diff) => {
    if (diff === 1) return 'fdr-1';
    if (diff === 2) return 'fdr-2';
    if (diff === 3) return 'fdr-3';
    if (diff === 4) return 'fdr-4';
    if (diff >= 5) return 'fdr-5';
    return '';
  };

  const handleCellClick = (f) => {
    if (f.oppShort === 'BLANK' || !handleOpen) return;
    handleOpen({
      home_team: f.home_team,
      away_team: f.away_team,
      fixture_id: f.fixture_id,
      event: f.gw
    });
  };

  return (
    <div className="view-fluid">
      {/* Ticker Header & Controls Bar */}
      <div className="ticker-controls-bar">
        <div className="ticker-title-group">
          <h3 className="ticker-title">
            <GridNine size={18} weight="bold" />
            <span>Fixture Difficulty &amp; Schedule Ticker</span>
          </h3>
          <div className="ticker-subtitle">
            Teams sorted from easiest to toughest fixture run over the next {gwWindow} gameweeks (GW{selectedGw} to GW{Math.min(38, Number(selectedGw) + gwWindow - 1)}). Click any match to view clean sheet chances and scoreline odds.
          </div>
        </div>

        <div className="ticker-window-controls" role="group" aria-label="Select fixture run lookahead">
          <span className="ticker-window-label font-mono">Lookahead</span>
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
                <th className="avg-col font-mono">Avg Difficulty</th>
                {Array.from({ length: 38 }, (_, i) => i + 1).map(gw => (
                  <th key={gw} className={`gw-col font-mono ${gw === Number(selectedGw) ? 'current-gw-header' : ''}`}>
                    GW{gw}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.length === 0 ? (
                <tr>
                  <td colSpan={40} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Loading fixture schedule &amp; difficulty data...
                  </td>
                </tr>
              ) : (
                matrix.map((team, idx) => (
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
                    {team.fixtures.map(f => {
                      const isInteractive = f.oppShort !== 'BLANK' && Boolean(handleOpen);
                      return (
                        <td
                          key={f.gw}
                          className={`fdr-cell ${fdrClass(f.diff)} ${f.gw === Number(selectedGw) ? 'current-gw-col' : ''}`}
                          onClick={() => handleCellClick(f)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleCellClick(f);
                            }
                          }}
                          tabIndex={isInteractive ? 0 : undefined}
                          role={isInteractive ? 'button' : undefined}
                          style={{ cursor: isInteractive ? 'pointer' : 'default' }}
                          title={isInteractive ? `Click to view ${f.home_team} vs ${f.away_team} match odds & clean sheet chances (GW${f.gw})` : undefined}
                        >
                          <div className="fdr-cell-content">
                            <span className="opp-name font-mono">{f.oppShort}</span>
                            <span className="venue-tag font-mono">{f.isHome ? 'H' : 'A'}</span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
