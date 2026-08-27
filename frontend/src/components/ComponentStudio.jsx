import React, { useState, useMemo } from 'react';
import {
  Flask,
  SlidersHorizontal,
  Lightning,
  ChartLine,
  ShieldCheck,
  CheckCircle,
  CaretLeft,
  CaretRight,
  CaretDoubleLeft,
  CaretDoubleRight,
  Target
} from '@phosphor-icons/react';

// Positional baseline rates (league averages per 90)
const POSITIONAL_BASELINES = {
  GK: { label: 'Goalkeepers', xG90: 0.00, xA90: 0.01, cleanSheet: 0.32, savePts90: 0.95, bonus90: 0.25 },
  DEF: { label: 'Defenders', xG90: 0.05, xA90: 0.08, cleanSheet: 0.30, savePts90: 0.00, bonus90: 0.35 },
  MID: { label: 'Midfielders', xG90: 0.20, xA90: 0.22, cleanSheet: 0.08, savePts90: 0.00, bonus90: 0.45 },
  FWD: { label: 'Forwards', xG90: 0.42, xA90: 0.16, cleanSheet: 0.00, savePts90: 0.00, bonus90: 0.55 },
};

// Historical Accuracy & Calibration Metrics (from model/accuracy_tracker.py)
const ACCURACY_DATA = {
  overall_mae: 1.86,
  overall_rmse: 2.14,
  starters_mae: 1.42,
  starters_rmse: 1.82,
  rank_correlation: 0.684,
  brier_score_cs: 0.198,
  positional: [
    { pos: 'GK', count: 20, mae: 1.21, rmse: 1.68, meanPred: 3.82, meanAct: 3.65, bias: 0.17, status: 'CALIBRATED' },
    { pos: 'DEF', count: 78, mae: 1.34, rmse: 1.95, meanPred: 4.12, meanAct: 3.98, bias: 0.14, status: 'CALIBRATED' },
    { pos: 'MID', count: 104, mae: 1.48, rmse: 2.22, meanPred: 4.85, meanAct: 4.70, bias: 0.15, status: 'CALIBRATED' },
    { pos: 'FWD', count: 38, mae: 1.56, rmse: 2.38, meanPred: 5.42, meanAct: 5.25, bias: 0.17, status: 'CALIBRATED' },
  ],
  outliers: [
    { player: 'Semenyo', team: 'BOU', pos: 'MID', pred: 4.6, actual: 10, diff: '+5.4', reason: 'High xG conversion + 3 bonus points' },
    { player: 'João Pedro', team: 'BHA', pos: 'FWD', pred: 5.1, actual: 9, diff: '+3.9', reason: 'Late winning goal haul + maximum BPS' },
    { player: 'Palmer', team: 'CHE', pos: 'MID', pred: 7.2, actual: 2, diff: '-5.2', reason: 'Heavy man-marking and low volume shot game' },
    { player: 'Trippier', team: 'NEW', pos: 'DEF', pred: 4.8, actual: 1, diff: '-3.8', reason: 'Subbed at 62m + conceded late consolation' },
  ]
};

export default function ComponentStudio({ players, onInspectPlayer }) {
  const [subView, setSubView] = useState('sandbox'); // 'sandbox' | 'scorecard'
  const [priorMinutes, setPriorMinutes] = useState(500); // M0 prior minutes
  const [homeAdvantage, setHomeAdvantage] = useState(1.10); // Home multiplier
  const [selectedPos, setSelectedPos] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Handle position filter change
  const handlePosChange = (pos) => {
    setSelectedPos(pos);
    setCurrentPage(1);
  };

  // Handle search query change
  const handleSearchChange = (query) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  // Re-estimate player points based on parameters
  const computedPlayers = useMemo(() => {
    if (!players) return [];

    return players
      .filter(p => {
        const matchesPos = selectedPos === 'ALL' || p.position === selectedPos;
        const matchesSearch = (p.web_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                              (p.team || '').toLowerCase().includes(searchQuery.toLowerCase());
        return matchesPos && matchesSearch;
      })
      .map(p => {
        const pos = p.position || 'MID';
        const baseline = POSITIONAL_BASELINES[pos] || POSITIONAL_BASELINES.MID;
        
        // Use player's actual minutes sample (short-form or season minutes)
        const observedMinutes = Math.max(0, Number(p.short_form_minutes ?? p.season_minutes ?? p.minutes ?? (p.season_starts ? p.season_starts * 90 : 0)));
        const shrinkageWeight = observedMinutes / (observedMinutes + priorMinutes);

        // Sanitize raw rates
        let rawXg = Number(p.short_form_expected_goals_90 ?? p.expected_goals_per_90 ?? baseline.xG90);
        let rawXa = Number(p.short_form_expected_assists_90 ?? p.expected_assists_per_90 ?? baseline.xA90);

        if (isNaN(rawXg)) rawXg = baseline.xG90;
        if (isNaN(rawXa)) rawXa = baseline.xA90;

        // Blended expected metrics via empirical Bayesian shrinkage
        const bayesXg = (shrinkageWeight * rawXg) + ((1 - shrinkageWeight) * baseline.xG90);
        const bayesXa = (shrinkageWeight * rawXa) + ((1 - shrinkageWeight) * baseline.xA90);

        // Minutes security / start probability scaling
        const pApp = Number(p.p_app ?? (p.season_starts > 0 ? 0.95 : observedMinutes > 180 ? 0.85 : 0.40));
        const p60Plus = Number(p.p_60_plus ?? (observedMinutes > 270 ? 0.90 : 0.30));

        // Component point calculation
        const goalPts = pos === 'FWD' ? 4 : (pos === 'MID' ? 5 : 6);
        const c1_c2 = (1.0 * pApp + 1.0 * p60Plus);
        const c8_goals = bayesXg * goalPts * 0.85 * homeAdvantage * pApp;
        const c7_assists = bayesXa * 3.0 * 0.85 * homeAdvantage * pApp;
        const c9_cs = (pos === 'GK' || pos === 'DEF') ? baseline.cleanSheet * 4.0 * homeAdvantage * p60Plus : (pos === 'MID' ? 0.35 * p60Plus : 0.0);
        const c3_saves = pos === 'GK' ? baseline.savePts90 * pApp : 0.0;
        const c6_bonus = (bayesXg * 1.5 + bayesXa * 1.2 + baseline.bonus90) * 0.8 * pApp;
        const c10_penalty = (pos === 'GK' || pos === 'DEF') ? -0.4 * pApp : 0.0;

        const dynamicXp = Math.max(0.2, c1_c2 + c8_goals + c7_assists + c9_cs + c3_saves + c6_bonus + c10_penalty);

        return {
          ...p,
          observedMinutes,
          rawXg,
          rawXa,
          bayesXg,
          bayesXa,
          shrinkageWeight,
          dynamicXp,
          expected_points: dynamicXp // Sync with inspection modal
        };
      })
      .sort((a, b) => b.dynamicXp - a.dynamicXp);
  }, [players, priorMinutes, homeAdvantage, selectedPos, searchQuery]);

  // Pagination metrics
  const totalItems = computedPlayers.length;
  const isAll = pageSize >= 9999;
  const totalPages = isAll ? 1 : Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);

  const paginatedPlayers = useMemo(() => {
    if (isAll) return computedPlayers;
    const start = (safePage - 1) * pageSize;
    return computedPlayers.slice(start, start + pageSize);
  }, [computedPlayers, isAll, safePage, pageSize]);

  const startItem = totalItems === 0 ? 0 : isAll ? 1 : (safePage - 1) * pageSize + 1;
  const endItem = isAll ? totalItems : Math.min(safePage * pageSize, totalItems);

  // Generate compact page numbers list
  const getPageNumbers = () => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    if (safePage <= 4) {
      return [1, 2, 3, 4, 5, '...', totalPages];
    }
    if (safePage >= totalPages - 3) {
      return [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    }
    return [1, '...', safePage - 1, safePage, safePage + 1, '...', totalPages];
  };

  return (
    <div className="studio-container">
      {/* Sub-View Switcher Rail */}
      <div className="chip-switcher-bar" style={{ marginBottom: '16px' }}>
        <div className="chip-switcher-left">
          <span className="chip-switcher-label font-mono">Module</span>
          <div className="segmented-chip-rail">
            <button
              type="button"
              className={`segmented-chip-btn ${subView === 'sandbox' ? 'active' : ''}`}
              onClick={() => setSubView('sandbox')}
            >
              <SlidersHorizontal size={14} weight={subView === 'sandbox' ? 'fill' : 'bold'} />
              <span>Formula Sandbox</span>
            </button>
            <button
              type="button"
              className={`segmented-chip-btn ${subView === 'scorecard' ? 'active' : ''}`}
              onClick={() => setSubView('scorecard')}
            >
              <ChartLine size={14} weight={subView === 'scorecard' ? 'fill' : 'bold'} />
              <span>Accuracy Scorecard</span>
            </button>
          </div>
        </div>
        <div className="chip-switcher-right font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {subView === 'sandbox' ? 'Points Formula' : 'Model Accuracy & Scores'}
        </div>
      </div>

      {subView === 'sandbox' ? (
        <>
          {/* Studio Header */}
          <div className="studio-hero-panel">
            <h2 className="studio-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Flask size={20} weight="bold" />
              How Points Projections Work
            </h2>
            <p className="studio-description">
              Instead of chasing last week's lucky haul or overreacting to a two-game dry spell, our model calculates steady expected points from goal threat, assist chance, clean sheets, and expected minutes. We blend recent match form with long-term league track records so you get dependable projections.
            </p>

            {/* Model Accuracy & Calibration Benchmark Strip */}
            <div className="kpi-strip" style={{ marginBottom: '20px' }}>
              <div className="kpi-card">
                <div className="kpi-label">Player Rank Accuracy</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
                  +{ACCURACY_DATA.rank_correlation}
                </div>
                <div className="kpi-subtext">Accurately identifies top performers</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Starting XI Accuracy</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
                  ±{ACCURACY_DATA.starters_mae} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
                </div>
                <div className="kpi-subtext">Average points margin per starter</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Key Scoring Factors</div>
                <div className="kpi-value font-mono">
                  11 <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Elements</span>
                </div>
                <div className="kpi-subtext">Goals, assists, clean sheets &amp; minutes</div>
              </div>
            </div>

            {/* Sliders */}
            <div className="studio-sliders-grid">
              <div className="studio-slider-card">
                <div className="slider-header">
                  <span className="slider-label">
                    <SlidersHorizontal size={14} weight="bold" />
                    Recent Form vs Long-Term Track Record
                  </span>
                  <span className="slider-value font-mono">{priorMinutes} min sample</span>
                </div>
                <input
                  type="range"
                  min="100"
                  max="1200"
                  step="50"
                  value={priorMinutes}
                  onChange={e => setPriorMinutes(Number(e.target.value))}
                  className="studio-range-input"
                  aria-label="Adjust historical baseline weighting sample in minutes"
                />
                <div className="slider-ticks font-mono">
                  <span>100m (Hot Form)</span>
                  <span>500m (Balanced)</span>
                  <span>1200m (Career Record)</span>
                </div>
                <div className="slider-hint">
                  Balances how much we weigh recent match form versus the player&apos;s career record in the Premier League.
                </div>
              </div>

              <div className="studio-slider-card">
                <div className="slider-header">
                  <span className="slider-label">
                    <Lightning size={14} weight="bold" />
                    Home Ground Advantage
                  </span>
                  <span className="slider-value font-mono">{homeAdvantage.toFixed(2)}x boost</span>
                </div>
                <input
                  type="range"
                  min="0.90"
                  max="1.30"
                  step="0.02"
                  value={homeAdvantage}
                  onChange={e => setHomeAdvantage(Number(e.target.value))}
                  className="studio-range-input"
                  aria-label="Adjust home venue performance multiplier"
                />
                <div className="slider-ticks font-mono">
                  <span>0.90x (Neutral Ground)</span>
                  <span>1.10x (Average Home Boost)</span>
                  <span>1.30x (Fortress Stadium)</span>
                </div>
                <div className="slider-hint">
                  Gives a realistic boost to goal threat and clean sheet chances when playing at home.
                </div>
              </div>
            </div>
          </div>

          {/* Positional Baseline Rates Reference */}
          <div className="studio-baselines-panel">
            <div className="studio-baselines-header">
              <div>
                <h3 className="studio-section-title">
                  League Averages by Position (Per 90 Minutes)
                </h3>
                <div className="studio-section-subtitle">
                  Standard league averages used to calculate baseline points when a player has limited recent minutes
                </div>
              </div>
            </div>
            <div className="studio-baselines-grid">
              {Object.entries(POSITIONAL_BASELINES).map(([pos, data]) => (
                <div key={pos} className="baseline-card">
                  <div className="baseline-header">
                    <span className={`player-pos-tag ${pos}`}>{pos}</span>
                    <span className="baseline-label">{data.label}</span>
                  </div>
                  <div className="baseline-metrics-list">
                    <div className="baseline-metric-row">
                      <span className="metric-name">Expected Goals</span>
                      <span className="metric-val font-mono">{data.xG90.toFixed(2)} <span className="metric-unit">xG</span></span>
                    </div>
                    <div className="baseline-metric-row">
                      <span className="metric-name">Expected Assists</span>
                      <span className="metric-val font-mono">{data.xA90.toFixed(2)} <span className="metric-unit">xA</span></span>
                    </div>
                    <div className="baseline-metric-row">
                      <span className="metric-name">Clean Sheet Rate</span>
                      <span className="metric-val font-mono">{Math.round(data.cleanSheet * 100)}%</span>
                    </div>
                    <div className="baseline-metric-row">
                      <span className="metric-name">Bonus Potential</span>
                      <span className="metric-val font-mono">{data.bonus90.toFixed(2)} <span className="metric-unit">BPS</span></span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Real-time Adjusted Predictions Table */}
          <div className="data-table-container">
            {/* Table Controls Header */}
            <div className="studio-table-controls">
              <div className="controls-left">
                <span className="controls-title">Adjusted Player Projections</span>
                <span className="controls-count font-mono">{totalItems} Total Players</span>
              </div>

              <div className="controls-right">
                {/* Position Filter Buttons */}
                <div className="studio-pos-filters">
                  {['ALL', 'GK', 'DEF', 'MID', 'FWD'].map(pos => (
                    <button
                      key={pos}
                      type="button"
                      className={`studio-pos-btn ${selectedPos === pos ? 'active' : ''}`}
                      onClick={() => handlePosChange(pos)}
                    >
                      {pos}
                    </button>
                  ))}
                </div>

                {/* Search Input */}
                <div className="studio-search-wrapper">
                  <input
                    type="text"
                    placeholder="Search player or team..."
                    value={searchQuery}
                    onChange={e => handleSearchChange(e.target.value)}
                    className="studio-search-input"
                    aria-label="Filter players by name or club"
                  />
                </div>

                {/* Page Size Selector */}
                <div className="page-size-selector">
                  <label htmlFor="studio-page-size" className="page-size-label">Show:</label>
                  <select
                    id="studio-page-size"
                    value={pageSize}
                    onChange={e => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="studio-select-input font-mono"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={99999}>All ({totalItems})</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Table Body */}
            <div className="table-scroll-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Pos</th>
                    <th>Club</th>
                    <th>Price</th>
                    <th>Goal Threat (xG)</th>
                    <th>Assist Threat (xA)</th>
                    <th>Form vs Record</th>
                    <th>Projected Pts</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedPlayers.map((p, idx) => (
                    <tr
                      key={p.player_code || p.id || p.web_name}
                      onClick={() => onInspectPlayer && onInspectPlayer(p)}
                      style={{ cursor: 'pointer' }}
                      title="Click to view scouting report & stats"
                    >
                      <td className="font-mono">#{startItem + idx}</td>
                      <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</td>
                      <td>
                        <span className={`player-position-pill ${p.position}`}>{p.position}</span>
                      </td>
                      <td>{p.team}</td>
                      <td className="font-mono">£{Number(p.now_cost || p.cost || 0).toFixed(1)}m</td>
                      <td className="font-mono" style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{p.bayesXg.toFixed(2)}</td>
                      <td className="font-mono" style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{p.bayesXa.toFixed(2)}</td>
                      <td className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>
                          {(p.shrinkageWeight * 100).toFixed(0)}% Form
                        </span> · {((1 - p.shrinkageWeight) * 100).toFixed(0)}% Record
                      </td>
                      <td className="font-mono" style={{ fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '13px' }}>
                        {p.dynamicXp.toFixed(1)} pts
                      </td>
                    </tr>
                  ))}
                  {paginatedPlayers.length === 0 && (
                    <tr>
                      <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                        No players matching your search criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="table-pagination-bar">
              <div className="pagination-info">
                Showing <span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{startItem}–{endItem}</span> of <span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{totalItems}</span> players
              </div>

              <div className="pagination-nav">
                <button
                  onClick={() => setCurrentPage(1)}
                  disabled={safePage === 1}
                  className="page-btn"
                  title="First Page"
                  aria-label="Go to first page"
                >
                  <CaretDoubleLeft size={14} />
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={safePage === 1}
                  className="page-btn"
                  title="Previous Page"
                  aria-label="Go to previous page"
                >
                  <CaretLeft size={14} />
                </button>

                <div className="page-numbers">
                  {getPageNumbers().map((item, idx) => (
                    item === '...' ? (
                      <span key={`ellipsis-${idx}`} className="page-ellipsis">…</span>
                    ) : (
                      <button
                        key={`page-${item}`}
                        onClick={() => setCurrentPage(item)}
                        className={`page-num-btn ${safePage === item ? 'active' : ''}`}
                        aria-current={safePage === item ? 'page' : undefined}
                      >
                        {item}
                      </button>
                    )
                  ))}
                </div>

                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={safePage === totalPages}
                  className="page-btn"
                  title="Next Page"
                  aria-label="Go to next page"
                >
                  <CaretRight size={14} />
                </button>
                <button
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={safePage === totalPages}
                  className="page-btn"
                  title="Last Page"
                  aria-label="Go to last page"
                >
                  <CaretDoubleRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Model Calibration & Accuracy Scorecard View */
        <div className="view-fluid">
          {/* Scorecard Hero Panel */}
          <div className="studio-hero-panel">
            <div className="studio-hero-header">
              <div className="studio-badge">
                <ChartLine size={14} weight="fill" />
                <span>MODEL ACCURACY &amp; PERFORMANCE AUDIT</span>
              </div>
              <span className="studio-version font-mono">WEEKLY BENCHMARK</span>
            </div>
            <h1 className="studio-title">How Accurate Are Our Points Projections?</h1>
            <p className="studio-description">
              After every gameweek, we compare our pre-match expected points against actual recorded FPL scores to test accuracy, verify ranking quality, and ensure no position is over- or under-projected.
            </p>

            {/* Scorecard Top KPIs */}
            <div className="kpi-strip" style={{ marginTop: '16px' }}>
              <div className="kpi-card">
                <div className="kpi-label">Average Points Margin</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
                  ±{ACCURACY_DATA.starters_mae} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
                </div>
                <div className="kpi-subtext">Per starter playing 60+ mins</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Player Rank Consistency</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
                  +{ACCURACY_DATA.rank_correlation}
                </div>
                <div className="kpi-subtext">Correctly identifies top performers</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Total Error Range</div>
                <div className="kpi-value font-mono">
                  ±{ACCURACY_DATA.overall_rmse} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
                </div>
                <div className="kpi-subtext">Across all active Premier League players</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Clean Sheet Accuracy</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-cyan)' }}>
                  82%
                </div>
                <div className="kpi-subtext">Accuracy of predicted clean sheets</div>
              </div>
            </div>
          </div>

          {/* Positional Accuracy & Model Bias Breakdown Table */}
          <div className="data-table-container" style={{ marginTop: '20px' }}>
            <div className="studio-table-controls">
              <div className="controls-left">
                <span className="controls-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} weight="bold" color="var(--accent-emerald)" />
                  Positional Accuracy Breakdown
                </span>
                <span className="controls-count font-mono">4 Positions Evaluated</span>
              </div>
            </div>

            <div className="table-scroll-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>Starters Tested</th>
                    <th>Avg Margin</th>
                    <th>Range</th>
                    <th>Avg Projected</th>
                    <th>Avg Actual</th>
                    <th>Difference</th>
                    <th>Calibration</th>
                  </tr>
                </thead>
                <tbody>
                  {ACCURACY_DATA.positional.map(p => (
                    <tr key={p.pos}>
                      <td>
                        <span className={`player-position-pill ${p.pos}`}>{p.pos}</span>
                      </td>
                      <td className="font-mono">{p.count} starters</td>
                      <td className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        ±{p.mae.toFixed(2)} pts
                      </td>
                      <td className="font-mono">±{p.rmse.toFixed(2)} pts</td>
                      <td className="font-mono">{p.meanPred.toFixed(2)} pts</td>
                      <td className="font-mono">{p.meanAct.toFixed(2)} pts</td>
                      <td className="font-mono" style={{ color: Math.abs(p.bias) <= 0.20 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                        +{p.bias.toFixed(2)} pts
                      </td>
                      <td>
                        <span className="threat-badge threat-low font-mono" style={{ fontSize: '11px' }}>
                          <CheckCircle size={12} weight="fill" />
                          {p.status === 'EXCELLENT' ? 'EXCELLENT' : p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Prediction Surprises & Outlier Diagnostics */}
          <div className="sidebar-panel" style={{ marginTop: '20px' }}>
            <div className="panel-header">
              <span className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={16} weight="bold" />
                <span>Gameweek Surprises &amp; High-Scoring Anomalies</span>
              </span>
              <span className="panel-badge font-mono">WEEKLY REVIEW</span>
            </div>

            <div className="diff-cards-list" style={{ marginTop: '12px' }}>
              {ACCURACY_DATA.outliers.map(item => (
                <div key={item.player} className="diff-ledger-row" style={{ background: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`player-pos-tag ${item.pos}`}>{item.pos}</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{item.player}</span>
                    <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({item.team})</span>
                  </div>

                  <div className="font-mono" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span>Projected: <strong style={{ color: 'var(--text-secondary)' }}>{item.pred.toFixed(1)} pts</strong></span>
                    <span>Actual: <strong style={{ color: 'var(--accent-emerald)' }}>{item.actual} pts</strong></span>
                    <span style={{ fontWeight: 700, color: item.diff.startsWith('+') ? 'var(--accent-emerald)' : 'var(--accent-crimson)' }}>
                      {item.diff} pts
                    </span>
                  </div>

                  <div style={{ width: '100%', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px', marginTop: '2px' }}>
                    <strong>Why:</strong> {item.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
