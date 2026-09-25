import React, { useState, useMemo, useEffect, useRef } from 'react';
import { GridNine, Info, Sparkle } from '@phosphor-icons/react';

export default function FixtureHeatmap({
  fixtures,
  fixturesData,
  teams,
  teamsData,
  selectedGw = 2,
  onOpenFixture,
  onOpenMatchup
}) {
  const [horizon, setHorizon] = useState('5');
  const [showFormulaTooltip, setShowFormulaTooltip] = useState(false);
  const formulaRef = useRef(null);

  useEffect(() => {
    if (!showFormulaTooltip) return;
    const handleClickOutside = (e) => {
      if (formulaRef.current && !formulaRef.current.contains(e.target)) {
        setShowFormulaTooltip(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowFormulaTooltip(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [showFormulaTooltip]);

  const activeFixtures = fixtures || fixturesData || [];
  const activeTeams = teams || teamsData || [];
  const handleOpen = onOpenFixture || onOpenMatchup;
  const currentGw = Number(selectedGw || 2);
  const effectiveWindow = horizon === 'all' ? 5 : Number(horizon);

  // Compute visible gameweeks based on active horizon filter
  const visibleGws = useMemo(() => {
    if (horizon === 'all') {
      return Array.from({ length: 38 }, (_, i) => i + 1);
    }
    const count = Number(horizon);
    const gws = [];
    for (let i = 0; i < count; i++) {
      const gw = currentGw + i;
      if (gw <= 38) {
        gws.push(gw);
      }
    }
    return gws;
  }, [horizon, currentGw]);

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

      const nextN = teamFixtures.slice(Math.max(0, currentGw - 1), currentGw - 1 + effectiveWindow);
      const avgDiff = nextN.reduce((acc, f) => acc + (f.diff || 3), 0) / (nextN.length || 1);

      return {
        ...team,
        fixtures: teamFixtures,
        avgDiff
      };
    });

    // Sort by easiest upcoming run
    return result.sort((a, b) => a.avgDiff - b.avgDiff);
  }, [activeFixtures, activeTeams, effectiveWindow, currentGw]);

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

  const horizonOptions = [
    { id: '3', label: 'Next 3 GWs' },
    { id: '5', label: 'Next 5 GWs' },
    { id: '8', label: 'Next 8 GWs' },
    { id: 'all', label: 'All 38 GWs' }
  ];

  return (
    <div className="view-fluid">
      {/* Ticker Header & Controls Bar */}
      <div className="ticker-controls-bar">
        <div className="ticker-title-group">
          <h1 className="ticker-title">
            <GridNine size={18} weight="bold" />
            <span>Fixture Difficulty &amp; Schedule Ticker</span>
          </h1>
          <div className="ticker-subtitle">
            {horizon === 'all'
              ? `Full 38-gameweek season view with completed matchdays shaded. Teams sorted from easiest to toughest fixture run over the next 5 gameweeks (GW${currentGw} to GW${Math.min(38, currentGw + 4)}). Click any match to view clean sheet chances and scoreline odds.`
              : `Teams sorted from easiest to toughest fixture run over the next ${effectiveWindow} gameweeks (GW${currentGw} to GW${Math.min(38, currentGw + effectiveWindow - 1)}). Click any match to view clean sheet chances and scoreline odds.`}
          </div>
        </div>

        <div className="ticker-window-controls" role="group" aria-label="Select fixture planning horizon">
          <span className="ticker-window-label font-mono">HORIZON:</span>
          <div className="wire-segments" role="group" aria-label="Planning Horizon">
            {horizonOptions.map(h => (
              <button
                key={h.id}
                type="button"
                onClick={() => setHorizon(h.id)}
                aria-label={`Planning horizon: ${h.label}`}
                aria-pressed={horizon === h.id}
                className="wire-segment font-mono"
              >
                <span>{h.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Streamlined FDR Legend & Formula Explainer */}
      <div className="fixture-legend-bar">
        <div className="legend-scale-group">
          <span className="legend-label font-mono">FDR:</span>
          <div className="legend-items">
            <div className="legend-chip" title="FDR 1: Very Easy (Home vs promoted / bottom tier)">
              <span className="legend-fdr-tag font-mono fdr-1">1</span>
              <span className="legend-text">Very Easy</span>
            </div>
            <div className="legend-chip" title="FDR 2: Easy (Home vs lower-half opponent)">
              <span className="legend-fdr-tag font-mono fdr-2">2</span>
              <span className="legend-text">Easy</span>
            </div>
            <div className="legend-chip" title="FDR 3: Moderate (Mid-table matchup)">
              <span className="legend-fdr-tag font-mono fdr-3">3</span>
              <span className="legend-text">Moderate</span>
            </div>
            <div className="legend-chip" title="FDR 4: Tough (Away vs top-six)">
              <span className="legend-fdr-tag font-mono fdr-4">4</span>
              <span className="legend-text">Tough</span>
            </div>
            <div className="legend-chip" title="FDR 5: Very Tough (Away vs title contenders)">
              <span className="legend-fdr-tag font-mono fdr-5">5</span>
              <span className="legend-text">Very Tough</span>
            </div>
            <div className="legend-chip" title="Blank Gameweek: No fixture scheduled">
              <span className="legend-fdr-tag font-mono fdr-blank">-</span>
              <span className="legend-text">Blank</span>
            </div>
            <div className="legend-chip" title="Completed Matchday">
              <span className="legend-fdr-tag font-mono fdr-past">✓</span>
              <span className="legend-text">Past</span>
            </div>
          </div>
        </div>

        <div className="legend-formula-group" ref={formulaRef}>
          <button
            type="button"
            className={`formula-trigger-btn font-mono ${showFormulaTooltip ? 'active' : ''}`}
            onClick={() => setShowFormulaTooltip(prev => !prev)}
            title="Click to view Avg Difficulty formula"
            aria-expanded={showFormulaTooltip}
          >
            <Info size={13} weight="bold" />
            <span>Avg Difficulty Formula</span>
          </button>
          {showFormulaTooltip && (
            <div className="formula-popover-card font-mono" role="tooltip">
              <div className="formula-popover-title">
                Avg Difficulty = (Σ FDR over next {effectiveWindow} GWs) / {effectiveWindow}
              </div>
              <div className="formula-popover-desc">
                Sorted ascending: lower score indicates an easier fixture run.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="data-table-container">
        <div className="table-scroll-wrapper">
          <table
            className={`heatmap-table ${horizon !== 'all' ? 'horizon-focused' : 'horizon-all'}`}
            aria-label="Premier League Fixture Difficulty Table"
          >
            <thead>
              <tr>
                <th scope="col" className="sticky-col team-col">Team</th>
                <th scope="col" className="avg-col font-mono" title={`Mathematical average of FDR ratings over the next ${effectiveWindow} gameweeks. Lower score indicates an easier schedule.`}>
                  Avg Difficulty ({effectiveWindow} GWs)
                </th>
                {visibleGws.map(gw => {
                  const isPast = gw < currentGw;
                  const isCurrent = gw === currentGw;
                  return (
                    <th
                      key={gw}
                      scope="col"
                      className={`gw-col font-mono ${isPast ? 'past-gw-header' : ''} ${isCurrent ? 'current-gw-header' : ''}`}
                    >
                      GW{gw}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {matrix.length === 0 ? (
                <tr>
                  <td colSpan={visibleGws.length + 2} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Loading fixture schedule &amp; difficulty data...
                  </td>
                </tr>
              ) : (
                matrix.map((team, idx) => (
                  <tr key={team.id || team.name}>
                    <th scope="row" className="sticky-col team-cell" style={{ fontWeight: 'normal', textAlign: 'left' }}>
                      <span className="rank-num font-mono">{idx + 1}</span>
                      <span className="team-name">{team.name}</span>
                    </th>
                    <td className="avg-cell font-mono">
                      <span className="table-avg-diff font-mono">
                        {team.avgDiff.toFixed(2)}
                      </span>
                    </td>
                    {visibleGws.map(gw => {
                      const f = team.fixtures[gw - 1] || team.fixtures.find(m => m.gw === gw);
                      if (!f) return <td key={gw} className="fdr-cell" />;
                      const isInteractive = f.oppShort !== 'BLANK' && Boolean(handleOpen);
                      const isPast = f.gw < currentGw;
                      const isCurrent = f.gw === currentGw;
                      const cellTitle = isInteractive
                        ? (isPast
                            ? `Matchday GW${f.gw} (Completed): ${f.home_team} vs ${f.away_team}`
                            : `Click to view ${f.home_team} vs ${f.away_team} match odds & clean sheet chances (GW${f.gw})`)
                        : undefined;
                      return (
                        <td
                          key={f.gw}
                          className={`fdr-cell ${fdrClass(f.diff)} ${isPast ? 'past-gw' : ''} ${isCurrent ? 'current-gw-col' : ''}`}
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
                          title={cellTitle}
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
