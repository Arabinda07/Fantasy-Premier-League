import React, { useState, useMemo } from 'react';
import {
  Flask,
  SlidersHorizontal,
  Lightning,
  CaretLeft,
  CaretRight,
  CaretDoubleLeft,
  CaretDoubleRight
} from '@phosphor-icons/react';

// Positional baseline rates (league averages per 90)
const POSITIONAL_BASELINES = {
  GK: { label: 'Goalkeepers', xG90: 0.00, xA90: 0.01, cleanSheet: 0.32, savePts90: 0.95, bonus90: 0.25 },
  DEF: { label: 'Defenders', xG90: 0.05, xA90: 0.08, cleanSheet: 0.30, savePts90: 0.00, bonus90: 0.35 },
  MID: { label: 'Midfielders', xG90: 0.20, xA90: 0.22, cleanSheet: 0.08, savePts90: 0.00, bonus90: 0.45 },
  FWD: { label: 'Forwards', xG90: 0.42, xA90: 0.16, cleanSheet: 0.00, savePts90: 0.00, bonus90: 0.55 },
};

export default function ComponentStudio({ players, onInspectPlayer }) {
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
      {/* Studio Header */}
      <div className="studio-hero-panel">
        <h2 className="studio-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Flask size={20} weight="bold" />
          How Points Projections Work
        </h2>
        <p className="studio-description">
          Instead of chasing a lucky brace or overreacting to a two-game dry spell, our projection model breaks performance down into discrete building blocks: expected goals, expected assists, clean sheet chances, and bonus point potential. We blend recent player form with league-wide historical averages so you get steady, dependable expected points.
        </p>

        {/* Sliders */}
        <div className="studio-sliders-grid">
          <div className="studio-slider-card">
            <div className="slider-header">
              <span className="slider-label">
                <SlidersHorizontal size={14} weight="bold" />
                Recent Form vs Historical Baseline
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
              <span>100m (Rapid Form Reaction)</span>
              <span>500m (Balanced)</span>
              <span>1200m (Proven Track Record)</span>
            </div>
            <div className="slider-hint">
              Controls how much weight is given to a player&apos;s recent minutes versus their long-term league baseline.
            </div>
          </div>

          <div className="studio-slider-card">
            <div className="slider-header">
              <span className="slider-label">
                <Lightning size={14} weight="bold" />
                Home Advantage Multiplier
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
              <span>1.30x (Fortress Venue)</span>
            </div>
            <div className="slider-hint">
              Scales expected goals and clean sheet odds for players playing in their home stadium.
            </div>
          </div>
        </div>
      </div>

      {/* Positional Baseline Rates Reference */}
      <div className="studio-baselines-panel">
        <div className="studio-baselines-header">
          <div>
            <h3 className="studio-section-title">
              Premier League Positional Baselines (per 90 minutes)
            </h3>
            <div className="studio-section-subtitle">
              League-wide prior baselines (μ₀) used for Empirical Bayesian Shrinkage on low-sample players
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
            <span className="controls-title">Adjusted Player Point Projections</span>
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
                <th>Blended xG</th>
                <th>Blended xA</th>
                <th>Form Sample &amp; Baseline Split</th>
                <th>Adjusted Points</th>
              </tr>
            </thead>
            <tbody>
              {paginatedPlayers.map((p, idx) => (
                <tr
                  key={p.player_code || p.id || p.web_name}
                  onClick={() => onInspectPlayer && onInspectPlayer(p)}
                  style={{ cursor: 'pointer' }}
                  title="Click to inspect points breakdown"
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
                      {(p.shrinkageWeight * 100).toFixed(0)}% Form ({p.observedMinutes}m)
                    </span> · {((1 - p.shrinkageWeight) * 100).toFixed(0)}% Baseline
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
    </div>
  );
}
