import React, { useState, useMemo } from 'react';
import {
  X,
  SoccerBall,
  Table
} from '@phosphor-icons/react';

// Factorial helper
const factorial = (n) => {
  if (n <= 1) return 1;
  let res = 1;
  for (let i = 2; i <= n; i++) res *= i;
  return res;
};

// Poisson PMF
const poissonPmf = (k, lambda) => {
  return (Math.pow(lambda, k) * Math.exp(-lambda)) / factorial(k);
};

// Dixon-Coles adjustment tau
const dixonColesTau = (x, y, lambda, mu, rho = -0.05) => {
  if (x === 0 && y === 0) return 1 - lambda * mu * rho;
  if (x === 1 && y === 0) return 1 + mu * rho;
  if (x === 0 && y === 1) return 1 + lambda * rho;
  if (x === 1 && y === 1) return 1 - rho;
  return 1.0;
};

// Baseline attack/defense strength approximations for Premier League teams (goals/game)
const TEAM_STRENGTHS = {
  'man city': { att: 2.25, def: 0.90 },
  'arsenal': { att: 2.15, def: 0.85 },
  'liverpool': { att: 2.10, def: 0.95 },
  'chelsea': { att: 1.80, def: 1.20 },
  'aston villa': { att: 1.65, def: 1.25 },
  'tottenham': { att: 1.75, def: 1.35 },
  'newcastle': { att: 1.70, def: 1.20 },
  'man utd': { att: 1.55, def: 1.30 },
  'brighton': { att: 1.50, def: 1.35 },
  'brentford': { att: 1.45, def: 1.40 },
  'bournemouth': { att: 1.40, def: 1.45 },
  'fulham': { att: 1.35, def: 1.40 },
  'crystal palace': { att: 1.35, def: 1.35 },
  'west ham': { att: 1.30, def: 1.50 },
  'everton': { att: 1.15, def: 1.35 },
  'nottingham forest': { att: 1.20, def: 1.45 },
  'wolves': { att: 1.15, def: 1.50 },
  'leicester': { att: 1.10, def: 1.60 },
  'ipswich': { att: 1.05, def: 1.65 },
  'southampton': { att: 1.00, def: 1.70 },
  'leeds': { att: 1.10, def: 1.55 },
  'sunderland': { att: 1.05, def: 1.60 },
};

export default function FixtureProbabilityDrawer({
  isOpen,
  onClose,
  fixtureData,
  dixonColesList = []
}) {
  const [hoveredCell, setHoveredCell] = useState(null);

  const cleanStr = (s) => (s || '').toLowerCase().trim();

  // Match against pre-computed list or generate dynamically for any 38-GW matchup
  const fixture = useMemo(() => {
    if (!fixtureData) return null;

    const targetHome = cleanStr(fixtureData.home_team || fixtureData.team || 'Aston Villa');
    const targetAway = cleanStr(fixtureData.away_team || fixtureData.opponent || 'Arsenal');

    // 1. Try matching against live matchday pre-computed list
    if (dixonColesList && dixonColesList.length > 0) {
      const matched = dixonColesList.find(f => {
        const fHome = cleanStr(f.home_team);
        const fAway = cleanStr(f.away_team);
        return (
          (fHome.includes(targetHome) || targetHome.includes(fHome)) &&
          (fAway.includes(targetAway) || targetAway.includes(fAway))
        );
      });
      if (matched) return matched;
    }

    // 2. Dynamically compute Dixon-Coles parameters for ANY of the 380 PL fixtures
    const homeProfile = Object.entries(TEAM_STRENGTHS).find(([k]) => targetHome.includes(k) || k.includes(targetHome))?.[1] || { att: 1.40, def: 1.35 };
    const awayProfile = Object.entries(TEAM_STRENGTHS).find(([k]) => targetAway.includes(k) || k.includes(targetAway))?.[1] || { att: 1.30, def: 1.40 };

    // Expected goals = HomeAtt * AwayDef * HomeAdvantage (1.12) / LeagueAvg (~1.40)
    const expHome = Number(Math.max(0.6, Math.min(3.5, (homeProfile.att * awayProfile.def * 1.12) / 1.35)).toFixed(2));
    const expAway = Number(Math.max(0.5, Math.min(3.2, (awayProfile.att * homeProfile.def * 0.90) / 1.35)).toFixed(2));

    // Calculate outcomes over 0..6 goals
    let homeWin = 0;
    let draw = 0;
    let awayWin = 0;
    let btts = 0;
    let over25 = 0;
    const scorelines = [];

    for (let h = 0; h <= 6; h++) {
      for (let a = 0; a <= 6; a++) {
        const p = Math.max(0, dixonColesTau(h, a, expHome, expAway, -0.05) * poissonPmf(h, expHome) * poissonPmf(a, expAway));
        if (h > a) homeWin += p;
        else if (h === a) draw += p;
        else awayWin += p;

        if (h > 0 && a > 0) btts += p;
        if (h + a > 2.5) over25 += p;

        scorelines.push({ score: `${h}-${a}`, prob: p });
      }
    }

    scorelines.sort((a, b) => b.prob - a.prob);

    return {
      home_team: fixtureData.home_team || fixtureData.team || 'Home Club',
      away_team: fixtureData.away_team || fixtureData.opponent || 'Away Club',
      expected_home_goals: expHome,
      expected_away_goals: expAway,
      home_win_prob: Number(homeWin.toFixed(3)),
      draw_prob: Number(draw.toFixed(3)),
      away_win_prob: Number(awayWin.toFixed(3)),
      home_cs_prob: Number(Math.exp(-expAway).toFixed(3)),
      away_cs_prob: Number(Math.exp(-expHome).toFixed(3)),
      btts_prob: Number(btts.toFixed(3)),
      over_2_5_prob: Number(over25.toFixed(3)),
      most_likely_scorelines: scorelines.slice(0, 5)
    };
  }, [fixtureData, dixonColesList]);

  const activeFixture = fixture || {
    home_team: 'Aston Villa',
    away_team: 'Arsenal',
    expected_home_goals: 1.18,
    expected_away_goals: 1.62,
    home_win_prob: 0.284,
    draw_prob: 0.262,
    away_win_prob: 0.454,
    home_cs_prob: 0.248,
    away_cs_prob: 0.345,
    btts_prob: 0.582,
    over_2_5_prob: 0.524,
    most_likely_scorelines: [
      { score: '1-1', prob: 0.128 },
      { score: '1-2', prob: 0.114 },
      { score: '0-1', prob: 0.098 },
      { score: '0-2', prob: 0.082 },
      { score: '1-0', prob: 0.076 }
    ]
  };

  const lambda = Number(activeFixture.expected_home_goals || 1.25);
  const mu = Number(activeFixture.expected_away_goals || 1.45);

  // Compute 5x5 Joint Poisson Probability Matrix
  const { matrix, maxProb } = useMemo(() => {
    const goals = [0, 1, 2, 3, 4];
    const grid = [];
    let highest = 0;

    for (let h of goals) {
      const row = [];
      for (let a of goals) {
        const p = Math.max(0, dixonColesTau(h, a, lambda, mu, -0.05) * poissonPmf(h, lambda) * poissonPmf(a, mu));
        if (p > highest) highest = p;
        row.push({ home: h, away: a, prob: p });
      }
      grid.push(row);
    }
    return { matrix: grid, maxProb: highest || 0.15 };
  }, [lambda, mu]);

  // Conditional early return AFTER all hooks
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content drawer-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        style={{ maxWidth: '680px' }}
      >
        {/* Drawer Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="sync-icon-wrapper">
              <SoccerBall size={18} weight="fill" />
            </div>
            <div>
              <span className="profile-tag">MATCH PREVIEW &amp; PROBABILITY FORECAST</span>
              <h2 id="drawer-title" className="modal-title" style={{ marginTop: '2px' }}>
                {fixture.home_team} vs {fixture.away_team}
              </h2>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close drawer">
            <X size={18} weight="bold" />
          </button>
        </div>

        {/* Big Matchup Header Banner */}
        <div className="fixture-hero-card">
          <div className="team-side home">
            <span className="team-role">HOME</span>
            <div className="team-display-name">{fixture.home_team}</div>
            <div className="exp-goals font-mono">
              {lambda.toFixed(2)} <span className="exp-label">Exp Goals</span>
            </div>
          </div>

          <div className="vs-badge">
            <span>VS</span>
          </div>

          <div className="team-side away">
            <span className="team-role">AWAY</span>
            <div className="team-display-name">{fixture.away_team}</div>
            <div className="exp-goals font-mono">
              {mu.toFixed(2)} <span className="exp-label">Exp Goals</span>
            </div>
          </div>
        </div>

        {/* Win/Draw/Loss Outcome Probability Bar */}
        <div className="prob-breakdown-section" style={{ marginBottom: '16px' }}>
          <div className="section-label">Win / Draw / Loss Chances</div>
          <div className="prob-split-bar">
            <div
              className="split-segment home"
              style={{ width: `${Math.round((fixture.home_win_prob || 0.38) * 100)}%` }}
              title={`Home Win: ${Math.round((fixture.home_win_prob || 0.38) * 100)}%`}
            >
              <span>{fixture.home_team}: {Math.round((fixture.home_win_prob || 0.38) * 100)}%</span>
            </div>
            <div
              className="split-segment draw"
              style={{ width: `${Math.round((fixture.draw_prob || 0.26) * 100)}%` }}
              title={`Draw: ${Math.round((fixture.draw_prob || 0.26) * 100)}%`}
            >
              <span>Draw: {Math.round((fixture.draw_prob || 0.26) * 100)}%</span>
            </div>
            <div
              className="split-segment away"
              style={{ width: `${Math.round((fixture.away_win_prob || 0.36) * 100)}%` }}
              title={`Away Win: ${Math.round((fixture.away_win_prob || 0.36) * 100)}%`}
            >
              <span>{fixture.away_team}: {Math.round((fixture.away_win_prob || 0.36) * 100)}%</span>
            </div>
          </div>
        </div>

        {/* 5x5 Joint Scoreline Probability Matrix */}
        <div className="data-table-container" style={{ marginBottom: '16px' }}>
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Table size={14} weight="bold" />
                Most Likely Match Scorelines (Probability Grid)
              </span>
              <span className="controls-count font-mono">Scoreline Chances</span>
            </div>
          </div>

          <div style={{ padding: '12px 14px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
              ◀ {fixture.home_team} (Home Goals) &nbsp;&nbsp;|&nbsp;&nbsp; {fixture.away_team} (Away Goals) ▼
            </div>

            <div className="matrix-wrapper">
              <table className="scoreline-matrix-table">
                <thead>
                  <tr>
                    <th className="matrix-corner">H \ A</th>
                    {[0, 1, 2, 3, 4].map(a => (
                      <th key={`head-${a}`} className="matrix-col-header font-mono">
                        {a === 4 ? '4+' : a}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.map((row, hIdx) => (
                    <tr key={`row-${hIdx}`}>
                      <td className="matrix-row-header font-mono">
                        {hIdx === 4 ? '4+' : hIdx}
                      </td>
                      {row.map(cell => {
                        const isHovered = hoveredCell && hoveredCell.home === cell.home && hoveredCell.away === cell.away;
                        const isDraw = cell.home === cell.away;
                        const isHomeWin = cell.home > cell.away;
                        const isAwayWin = cell.home < cell.away;
                        const pct = (cell.prob * 100).toFixed(1);
                        const intensity = Math.min(1, cell.prob / maxProb);

                        // Heatmap color calculation
                        const baseColor = isHomeWin
                          ? `rgba(59, 130, 246, ${0.08 + intensity * 0.40})`
                          : isAwayWin
                          ? `rgba(16, 185, 129, ${0.08 + intensity * 0.40})`
                          : `rgba(245, 158, 11, ${0.08 + intensity * 0.35})`;

                        return (
                          <td
                            key={`cell-${cell.home}-${cell.away}`}
                            className={`matrix-cell ${isHovered ? 'hovered' : ''} ${isDraw ? 'is-draw' : ''}`}
                            style={{ background: baseColor }}
                            onMouseEnter={() => setHoveredCell(cell)}
                            onMouseLeave={() => setHoveredCell(null)}
                            title={`${fixture.home_team} ${cell.home} - ${cell.away} ${fixture.away_team}: ${pct}% chance (${isHomeWin ? 'Home Win' : isAwayWin ? 'Away Win' : 'Draw'})`}
                          >
                            <span className="matrix-val font-mono">{pct}%</span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Matrix Hover Readout */}
            <div style={{ marginTop: '8px', minHeight: '22px', fontSize: '11.5px', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
              {hoveredCell ? (
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
                  Scoreline: {fixture.home_team} {hoveredCell.home} – {hoveredCell.away} {fixture.away_team} · {(hoveredCell.prob * 100).toFixed(2)}% ({hoveredCell.home > hoveredCell.away ? `${fixture.home_team} Win` : hoveredCell.home < hoveredCell.away ? `${fixture.away_team} Win` : 'Draw'})
                </span>
              ) : (
                <span style={{ color: 'var(--text-muted)' }}>
                  Hover over any scoreline to see exact probability
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 4-Card Quantitative Metrics Grid */}
        <div className="kpi-strip" style={{ marginBottom: '16px' }}>
          <div className="kpi-card">
            <div className="kpi-label">{fixture.home_team} Clean Sheet</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-blue)' }}>
              {Math.round((fixture.home_cs_prob || 0.28) * 100)}%
            </div>
            <div className="kpi-subtext">Chance of shutting out {fixture.away_team}</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">{fixture.away_team} Clean Sheet</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
              {Math.round((fixture.away_cs_prob || 0.32) * 100)}%
            </div>
            <div className="kpi-subtext">Chance of shutting out {fixture.home_team}</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Both Teams to Score</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-amber)' }}>
              {Math.round((fixture.btts_prob || 0.54) * 100)}%
            </div>
            <div className="kpi-subtext">Both sides find the net</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Over 2.5 Total Goals</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--text-primary)' }}>
              {Math.round((fixture.over_2_5_prob || 0.51) * 100)}%
            </div>
            <div className="kpi-subtext">3 or more total goals expected</div>
          </div>
        </div>

        {/* Top 5 Most Likely Exact Scorelines */}
        <div className="data-table-container">
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title">Top 5 Most Likely Final Scores</span>
              <span className="controls-count font-mono">Ranked by Likelihood</span>
            </div>
          </div>
          <div className="scorelines-grid">
            {(fixture.most_likely_scorelines || [
              { score: '1-1', prob: 0.128 },
              { score: '1-2', prob: 0.114 },
              { score: '0-1', prob: 0.098 },
              { score: '0-2', prob: 0.082 },
              { score: '1-0', prob: 0.076 }
            ]).map((s, idx) => (
              <div key={s.score} className="scoreline-pill-card">
                <span className="scoreline-rank">#{idx + 1}</span>
                <span className="scoreline-result font-mono">{s.score}</span>
                <span className="scoreline-prob font-mono">{Math.round(s.prob * 100)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-actions" style={{ marginTop: '16px' }}>
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
