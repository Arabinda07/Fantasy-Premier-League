import React, { useState, useMemo } from 'react';
import {
  MagnifyingGlass,
  Scales,
  X,
  TrendUp,
  TrendDown
} from '@phosphor-icons/react';

export default function TransferWorkbench({
  roadmap: _roadmap,
  allPlayers,
  squadPlayers = [],
  onInspectPlayer,
  onCompareChange
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPos, setSelectedPos] = useState('ALL');
  const [maxPrice, setMaxPrice] = useState(15.5);
  const [sortBy, setSortBy] = useState('xP');

  // Comparison State
  const [playerOut, setPlayerOut] = useState(null);
  const [playerIn, setPlayerIn] = useState(null);

  // Initialize playerOut with first squad player if available
  const defaultSquadList = squadPlayers.length > 0 ? squadPlayers : (allPlayers ? allPlayers.slice(0, 15) : []);

  // Filter and sort marketplace players
  const filteredPlayers = useMemo(() => {
    if (!allPlayers) return [];
    return allPlayers
      .filter(p => {
        const matchesSearch = (p.web_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                              (p.team || '').toLowerCase().includes(searchQuery.toLowerCase());
        const matchesPos = selectedPos === 'ALL' || p.position === selectedPos;
        const matchesPrice = Number(p.now_cost || p.cost || 0) <= maxPrice;
        return matchesSearch && matchesPos && matchesPrice;
      })
      .sort((a, b) => {
        if (sortBy === 'xP') {
          const xpB = Number(b.expected_points ?? b.xp ?? b.xP ?? 0);
          const xpA = Number(a.expected_points ?? a.xp ?? a.xP ?? 0);
          return xpB - xpA;
        }
        if (sortBy === 'cost_desc') return Number(b.now_cost || b.cost || 0) - Number(a.now_cost || a.cost || 0);
        if (sortBy === 'cost_asc') return Number(a.now_cost || a.cost || 0) - Number(b.now_cost || b.cost || 0);
        return 0;
      })
      .slice(0, 50);
  }, [allPlayers, searchQuery, selectedPos, maxPrice, sortBy]);

  // Handle selecting comparison players
  const handleSelectCompareIn = (player) => {
    setPlayerIn(player);
    if (!playerOut && defaultSquadList.length > 0) {
      // Auto-match position if possible
      const samePos = defaultSquadList.find(p => p.position === player.position);
      setPlayerOut(samePos || defaultSquadList[0]);
    }
    if (onCompareChange) {
      onCompareChange(`${player.web_name} vs ${(playerOut || defaultSquadList[0])?.web_name || 'Squad'}`);
    }
  };

  const handleClearCompare = () => {
    setPlayerIn(null);
    setPlayerOut(null);
    if (onCompareChange) onCompareChange(null);
  };

  // Compute Comparison Deltas
  const xpOut = Number(playerOut?.expected_points ?? playerOut?.xp ?? playerOut?.xP ?? 0);
  const xpIn = Number(playerIn?.expected_points ?? playerIn?.xp ?? playerIn?.xP ?? 0);
  const xpDelta = xpIn - xpOut;

  const costOut = Number(playerOut?.now_cost ?? playerOut?.cost ?? 0);
  const costIn = Number(playerIn?.now_cost ?? playerIn?.cost ?? 0);
  const costDelta = costIn - costOut;

  const xgOut = Number(playerOut?.expected_goals_per_90 ?? playerOut?.short_form_expected_goals_90 ?? playerOut?.xg90 ?? 0);
  const xgIn = Number(playerIn?.expected_goals_per_90 ?? playerIn?.short_form_expected_goals_90 ?? playerIn?.xg90 ?? 0);

  const xaOut = Number(playerOut?.expected_assists_per_90 ?? playerOut?.short_form_expected_assists_90 ?? playerOut?.xa90 ?? 0);
  const xaIn = Number(playerIn?.expected_assists_per_90 ?? playerIn?.short_form_expected_assists_90 ?? playerIn?.xa90 ?? 0);

  return (
    <div className="view-fluid">
      {/* Workbench Context Header */}
      <div className="studio-hero-panel" style={{ marginBottom: '20px' }}>
        <div className="studio-hero-header">
          <div className="studio-badge">
            <Scales size={14} weight="fill" />
            <span>TRANSFER COMPARISON &amp; SCOUT</span>
          </div>
          <span className="studio-version font-mono">PLAYER COMPARISON</span>
        </div>
        <h1 className="studio-title">Head-to-Head Transfer Scout</h1>
        <p className="studio-description">
          Test potential transfer targets against your current players. Compare expected points, price differences, and underlying goal &amp; assist stats before locking in your moves.
        </p>
      </div>

      {/* Side-by-Side Transfer Comparison Workbench */}
      {playerIn ? (
        <div className="compare-workbench-container">
          <div className="compare-workbench-header">
            <div className="compare-header-title">
              <div className="compare-icon-wrap">
                <Scales size={16} weight="bold" />
              </div>
              <span className="compare-title-text">
                Direct Transfer Swap Comparison
              </span>
            </div>
            <button
              onClick={handleClearCompare}
              className="compare-close-btn font-mono"
            >
              <X size={14} weight="bold" />
              <span>Close Comparison</span>
            </button>
          </div>

          <div className="compare-grid">
            {/* Player OUT Card */}
            <div className="compare-player-card out-card">
              <div className="card-role-header">
                <span className="transfer-label out font-mono">SELLING (OUT)</span>
                <select
                  value={playerOut?.player_code || ''}
                  onChange={(e) => {
                    const found = defaultSquadList.find(p => String(p.player_code) === e.target.value);
                    if (found) setPlayerOut(found);
                  }}
                  className="nav-select compare-player-select"
                  aria-label="Select squad player to transfer out"
                >
                  {defaultSquadList.map(p => (
                    <option key={p.player_code} value={p.player_code}>
                      {p.web_name} ({p.team} · £{Number(p.cost || p.now_cost || 0).toFixed(1)}m)
                    </option>
                  ))}
                </select>
              </div>

              <div className="compare-player-name-row">
                <span className={`player-pos-tag ${playerOut?.position}`}>{playerOut?.position}</span>
                <span className="compare-player-name">{playerOut?.web_name}</span>
                <span className="compare-player-team font-mono">({playerOut?.team})</span>
              </div>

              <div className="compare-xp-val font-mono">
                {xpOut.toFixed(1)} <span className="xp-unit">xP next match</span>
              </div>

              <div className="compare-stats-stack font-mono">
                <div className="compare-stat-row">
                  <span className="stat-name">Price</span>
                  <span className="stat-val">£{costOut.toFixed(1)}m</span>
                </div>
                <div className="compare-stat-row">
                  <span className="stat-name">Goal Threat (xG / 90)</span>
                  <span className="stat-val">{xgOut.toFixed(2)}</span>
                </div>
                <div className="compare-stat-row">
                  <span className="stat-name">Assist Threat (xA / 90)</span>
                  <span className="stat-val">{xaOut.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Delta Indicator (Center Column) */}
            <div className="compare-delta-column">
              <div className={`delta-badge ${xpDelta >= 0 ? 'positive' : 'negative'}`}>
                {xpDelta >= 0 ? <TrendUp size={16} weight="bold" /> : <TrendDown size={16} weight="bold" />}
                <span className="font-mono">{xpDelta >= 0 ? `+${xpDelta.toFixed(1)} xP Gain` : `${xpDelta.toFixed(1)} xP`}</span>
              </div>
              <div className="delta-cost-tag font-mono" style={{ color: costDelta <= 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                {costDelta <= 0 ? `Saves £${Math.abs(costDelta).toFixed(1)}m` : `Costs +£${costDelta.toFixed(1)}m`}
              </div>
            </div>

            {/* Player IN Card */}
            <div className="compare-player-card in-card">
              <div className="card-role-header">
                <span className="transfer-label in font-mono">BUYING (IN)</span>
                <span className="in-target-badge font-mono">TARGET ACQUISITION</span>
              </div>

              <div className="compare-player-name-row">
                <span className={`player-pos-tag ${playerIn?.position}`}>{playerIn?.position}</span>
                <span className="compare-player-name">{playerIn?.web_name}</span>
                <span className="compare-player-team font-mono">({playerIn?.team})</span>
              </div>

              <div className="compare-xp-val emerald font-mono">
                {xpIn.toFixed(1)} <span className="xp-unit">xP next match</span>
              </div>

              <div className="compare-stats-stack font-mono">
                <div className="compare-stat-row">
                  <span className="stat-name">Price</span>
                  <span className="stat-val">£{costIn.toFixed(1)}m</span>
                </div>
                <div className="compare-stat-row">
                  <span className="stat-name">Goal Threat (xG / 90)</span>
                  <span className="stat-val">{xgIn.toFixed(2)}</span>
                </div>
                <div className="compare-stat-row">
                  <span className="stat-name">Assist Threat (xA / 90)</span>
                  <span className="stat-val">{xaIn.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="compare-workbench-container compare-placeholder">
          <div className="placeholder-content">
            <Scales size={20} weight="bold" className="placeholder-icon" />
            <span className="placeholder-title">Test Any Transfer Head-to-Head</span>
          </div>
          <p className="placeholder-desc">
            Click the <strong style={{ color: 'var(--accent-emerald)' }}>&quot;Compare&quot;</strong> button on any player in the market below to simulate a direct swap against your squad and inspect points, budget, and goal threat differences.
          </p>
        </div>
      )}

      {/* Transfer Marketplace Table with 2-Tier Filter Bar */}
      <div className="data-table-container" style={{ marginTop: '20px' }}>
        <div className="scout-controls-2tier">
          {/* Tier 1: Search, Position Filter & Sort */}
          <div className="scout-tier-1">
            <div className="scout-search-wrap">
              <MagnifyingGlass size={14} className="scout-search-icon" />
              <input
                type="text"
                placeholder="Search player name or club..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                aria-label="Search players by name or club"
                className="scout-search-input"
              />
            </div>

            <div role="group" aria-label="Filter by player position" className="pos-btn-group">
              {['ALL', 'GK', 'DEF', 'MID', 'FWD'].map(pos => (
                <button
                  key={pos}
                  onClick={() => setSelectedPos(pos)}
                  aria-pressed={selectedPos === pos}
                  className={`pos-filter-btn ${selectedPos === pos ? 'active' : ''}`}
                >
                  {pos}
                </button>
              ))}
            </div>

            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              aria-label="Sort players by metric"
              className="scout-sort-select font-mono"
            >
              <option value="xP">Most Expected Points</option>
              <option value="cost_desc">Price (High to Low)</option>
              <option value="cost_asc">Price (Low to High)</option>
            </select>
          </div>

          {/* Tier 2: Budget Slider & Quick Presets */}
          <div className="scout-tier-2">
            <div className="scout-price-control">
              <span className="price-label font-mono">Max Budget: £{maxPrice}m</span>
              <input
                type="range"
                min="4.0"
                max="15.5"
                step="0.5"
                value={maxPrice}
                onChange={e => setMaxPrice(Number(e.target.value))}
                aria-label={`Maximum player cost slider, currently £${maxPrice}M`}
                className="scout-price-slider"
              />
            </div>

            <div className="scout-budget-presets font-mono">
              <span className="presets-label">QUICK:</span>
              {[
                { label: '< £5.0m', val: 5.0 },
                { label: '< £7.5m', val: 7.5 },
                { label: '< £10.0m', val: 10.0 },
                { label: 'ALL', val: 15.5 }
              ].map(preset => (
                <button
                  key={preset.label}
                  type="button"
                  className={`preset-btn ${maxPrice === preset.val ? 'active' : ''}`}
                  onClick={() => setMaxPrice(preset.val)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="table-scroll-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ position: 'sticky', left: 0, zIndex: 20 }}>Player</th>
                <th>Pos</th>
                <th>Club</th>
                <th>Price</th>
                <th>Exp Pts</th>
                <th>xG / 90</th>
                <th>xA / 90</th>
                <th>Start %</th>
                <th style={{ textAlign: 'center' }}>Compare</th>
              </tr>
            </thead>
            <tbody>
              {filteredPlayers.map(p => (
                <tr
                  key={p.player_code || p.id}
                  onClick={() => onInspectPlayer && onInspectPlayer(p)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      if (onInspectPlayer) onInspectPlayer(p);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`${p.web_name}, ${p.position}, £${Number(p.now_cost || p.cost || 0).toFixed(1)}M, ${Number(p.expected_points ?? p.xp ?? p.xP ?? 0).toFixed(1)} points`}
                  style={{ cursor: 'pointer' }}
                  title="Click to view scouting report & underlying stats"
                >
                  <td style={{ position: 'sticky', left: 0, zIndex: 10, fontWeight: 800, color: 'var(--text-primary)', background: 'var(--bg-surface-1)' }}>
                    {p.web_name}
                  </td>
                  <td>
                    <span className={`player-pos-tag ${p.position}`}>{p.position}</span>
                  </td>
                  <td className="font-mono" style={{ color: 'var(--text-secondary)' }}>{p.team}</td>
                  <td className="font-mono">£{Number(p.now_cost || p.cost || 0).toFixed(1)}m</td>
                  <td className="font-mono" style={{ fontWeight: 800, color: 'var(--accent-emerald)' }}>
                    {Number(p.expected_points ?? p.xp ?? p.xP ?? 0).toFixed(1)} pts
                  </td>
                  <td className="font-mono">{Number(p.expected_goals_per_90 ?? p.short_form_expected_goals_90 ?? p.xg90 ?? 0).toFixed(2)}</td>
                  <td className="font-mono">{Number(p.expected_assists_per_90 ?? p.short_form_expected_assists_90 ?? p.xa90 ?? 0).toFixed(2)}</td>
                  <td className="font-mono">{((p.p_start || 0.85) * 100).toFixed(0)}%</td>
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleSelectCompareIn(p)}
                      className="pos-filter-btn compare-action-btn font-mono"
                      style={{
                        background: playerIn?.web_name === p.web_name ? 'var(--accent-emerald)' : undefined,
                        color: playerIn?.web_name === p.web_name ? 'var(--text-inverse)' : undefined
                      }}
                      title="Compare this player against your squad"
                    >
                      {playerIn?.web_name === p.web_name ? 'Comparing' : 'Compare'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
