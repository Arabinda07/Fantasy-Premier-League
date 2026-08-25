import React from 'react';
import {
  X,
  SoccerBall,
  ShieldCheck,
  TrendUp,
  Percent,
  Sparkle,
  CalendarCheck
} from '@phosphor-icons/react';

export default function FixtureProbabilityDrawer({
  isOpen,
  onClose,
  fixtureData,
  dixonColesList = []
}) {
  if (!isOpen) return null;

  // Match against fixtureData or fallback to first fixture
  const fixture = dixonColesList.find(
    f => f.home_team === fixtureData?.home_team || f.away_team === fixtureData?.away_team
  ) || dixonColesList[0] || {
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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content drawer-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Drawer Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="sync-icon-wrapper">
              <SoccerBall size={18} weight="fill" />
            </div>
            <div>
              <span className="profile-tag">MATCH PREVIEW & ODDS SIMULATOR</span>
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
              {fixture.expected_home_goals} <span className="exp-label">xG</span>
            </div>
          </div>

          <div className="vs-badge">
            <span>VS</span>
            <span className="rho-tag font-mono">Simulated</span>
          </div>

          <div className="team-side away">
            <span className="team-role">AWAY</span>
            <div className="team-display-name">{fixture.away_team}</div>
            <div className="exp-goals font-mono">
              {fixture.expected_away_goals} <span className="exp-label">xG</span>
            </div>
          </div>
        </div>

        {/* Win/Draw/Loss Outcome Probability Bar */}
        <div className="prob-breakdown-section">
          <div className="section-label">Match Outcome Odds</div>
          <div className="prob-split-bar">
            <div
              className="split-segment home"
              style={{ width: `${Math.round(fixture.home_win_prob * 100)}%` }}
              title={`Home Win: ${Math.round(fixture.home_win_prob * 100)}%`}
            >
              <span>{fixture.home_team}: {Math.round(fixture.home_win_prob * 100)}%</span>
            </div>
            <div
              className="split-segment draw"
              style={{ width: `${Math.round(fixture.draw_prob * 100)}%` }}
              title={`Draw: ${Math.round(fixture.draw_prob * 100)}%`}
            >
              <span>Draw: {Math.round(fixture.draw_prob * 100)}%</span>
            </div>
            <div
              className="split-segment away"
              style={{ width: `${Math.round(fixture.away_win_prob * 100)}%` }}
              title={`Away Win: ${Math.round(fixture.away_win_prob * 100)}%`}
            >
              <span>{fixture.away_team}: {Math.round(fixture.away_win_prob * 100)}%</span>
            </div>
          </div>
        </div>

        {/* 4-Card Quantitative Metrics Grid */}
        <div className="kpi-strip" style={{ marginTop: '16px', marginBottom: '16px' }}>
          <div className="kpi-card">
            <div className="kpi-label">{fixture.home_team} Clean Sheet Odds</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
              {Math.round(fixture.home_cs_prob * 100)}%
            </div>
            <div className="kpi-subtext">Defensive clean sheet probability</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">{fixture.away_team} Clean Sheet Odds</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
              {Math.round(fixture.away_cs_prob * 100)}%
            </div>
            <div className="kpi-subtext">Defensive clean sheet probability</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Both Teams to Score (BTTS)</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-amber)' }}>
              {Math.round(fixture.btts_prob * 100)}%
            </div>
            <div className="kpi-subtext">Likelihood of both sides scoring</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Over 2.5 Total Goals</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-blue)' }}>
              {Math.round(fixture.over_2_5_prob * 100)}%
            </div>
            <div className="kpi-subtext">High-scoring fixture potential</div>
          </div>
        </div>

        {/* Top 5 Most Likely Exact Scorelines */}
        <div className="data-table-container">
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title">Most Likely Scorelines</span>
              <span className="controls-count font-mono">10,000 Match Simulations</span>
            </div>
          </div>
          <div className="scorelines-grid">
            {fixture.most_likely_scorelines.map((s, idx) => (
              <div key={s.score} className="scoreline-pill-card">
                <span className="scoreline-rank">#{idx + 1}</span>
                <span className="scoreline-result font-mono">{s.score}</span>
                <span className="scoreline-prob font-mono">{Math.round(s.prob * 100)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-actions" style={{ marginTop: '18px' }}>
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
