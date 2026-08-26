import React, { useState, useMemo } from 'react';
import {
  MagnifyingGlass,
  Scales,
  X,
  TrendUp,
  TrendDown
} from '@phosphor-icons/react';

export default function TransferWorkbench({
  _roadmap,
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
        if (sortBy === 'xP') return Number(b.expected_points || 0) - Number(a.expected_points || 0);
        if (sortBy === 'cost_desc') return Number(b.now_cost || 0) - Number(a.now_cost || 0);
        if (sortBy === 'cost_asc') return Number(a.now_cost || 0) - Number(b.now_cost || 0);
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
  const xpOut = Number(playerOut?.expected_points || 0);
  const xpIn = Number(playerIn?.expected_points || 0);
  const xpDelta = xpIn - xpOut;

  const costOut = Number(playerOut?.now_cost || playerOut?.cost || 0);
  const costIn = Number(playerIn?.now_cost || playerIn?.cost || 0);
  const costDelta = costIn - costOut;

  const xgOut = Number(playerOut?.expected_goals_per_90 || playerOut?.short_form_expected_goals_90 || 0);
  const xgIn = Number(playerIn?.expected_goals_per_90 || playerIn?.short_form_expected_goals_90 || 0);

  const xaOut = Number(playerOut?.expected_assists_per_90 || playerOut?.short_form_expected_assists_90 || 0);
  const xaIn = Number(playerIn?.expected_assists_per_90 || playerIn?.short_form_expected_assists_90 || 0);

  return (
    <div className="view-fluid">
      {/* Workbench Context Header */}
      <div className="studio-hero-panel" style={{ marginBottom: '20px' }}>
        <div className="studio-hero-header">
          <div className="studio-badge">
            <Scales size={14} weight="fill" />
            <span>H2H TRANSFER SIMULATOR &amp; SCOUT MARKETPLACE</span>
          </div>
          <span className="studio-version font-mono">LIVE OPTIMIZATION WORKBENCH</span>
        </div>
        <h1 className="studio-title">Head-to-Head Transfer Simulator &amp; Target Scout</h1>
        <p className="studio-description">
          Test potential transfers against your current 15-man squad in real time. Compare expected points ($\Delta\text{xP}$), budget impact ($\Delta\text{Cost}$), and underlying goal &amp; assist threat ($\Delta\text{xG90} / \Delta\text{xA90}$) before locking in your deadline moves.
        </p>
      </div>

      {/* Side-by-Side Transfer Comparison Workbench */}
      {playerIn ? (
        <div className="compare-workbench-container" style={{ margin: '24px 0', background: 'var(--bg-surface-1)', border: '1px solid var(--border-active)', borderRadius: 'var(--radius-lg)', padding: 'clamp(14px, 2vw, 20px)', boxShadow: '0 8px 24px rgba(0,0,0,0.5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ background: 'var(--accent-emerald)', color: 'var(--text-inverse)', padding: '3px 6px', borderRadius: 'var(--radius-xs)', display: 'flex', alignItems: 'center' }}>
                <Scales size={15} weight="bold" />
              </div>
              <span style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>
                Head-to-Head Transfer Comparison
              </span>
            </div>
            <button
              onClick={handleClearCompare}
              className="pos-filter-btn"
              style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px' }}
            >
              <X size={14} weight="bold" />
              <span>Close Comparison</span>
            </button>
          </div>

          <div className="compare-grid">
            {/* Player OUT Card */}
            <div className="compare-player-card out-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="transfer-label out">TRANSFER OUT</span>
                <select
                  value={playerOut?.player_code || ''}
                  onChange={(e) => {
                    const found = defaultSquadList.find(p => String(p.player_code) === e.target.value);
                    if (found) setPlayerOut(found);
                  }}
                  className="nav-select"
                  style={{ fontSize: '11px', padding: '3px 6px' }}
                  aria-label="Select squad player to transfer out"
                >
                  {defaultSquadList.map(p => (
                    <option key={p.player_code} value={p.player_code}>
                      {p.web_name} ({p.team} · £{Number(p.cost || p.now_cost || 0).toFixed(1)}m)
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span className={`player-position-pill ${playerOut?.position}`}>{playerOut?.position}</span>
                <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {playerOut?.web_name}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>({playerOut?.team})</span>
              </div>

              <div className="font-mono" style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                {xpOut.toFixed(1)} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>projected pts</span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div>Price: £{costOut.toFixed(1)}m</div>
                <div>Expected Goals (xG90): {xgOut.toFixed(2)}</div>
                <div>Expected Assists (xA90): {xaOut.toFixed(2)}</div>
              </div>
            </div>

            {/* Delta Indicator (Center) */}
            <div className="compare-delta-column">
              <div className={`delta-badge ${xpDelta >= 0 ? 'positive' : 'negative'}`}>
                {xpDelta >= 0 ? <TrendUp size={16} weight="bold" /> : <TrendDown size={16} weight="bold" />}
                <span>{xpDelta >= 0 ? `+${xpDelta.toFixed(1)}` : xpDelta.toFixed(1)} pts</span>
              </div>
              <div style={{ fontSize: '11px', color: costDelta <= 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontFamily: 'var(--font-mono)', marginTop: '4px', fontWeight: 700 }}>
                {costDelta <= 0 ? `Saves £${Math.abs(costDelta).toFixed(1)}m` : `Costs +£${costDelta.toFixed(1)}m`}
              </div>
            </div>

            {/* Player IN Card */}
            <div className="compare-player-card in-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="transfer-label in">TRANSFER IN</span>
                <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 700 }}>
                  Target Acquisition
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span className={`player-position-pill ${playerIn?.position}`}>{playerIn?.position}</span>
                <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {playerIn?.web_name}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>({playerIn?.team})</span>
              </div>

              <div className="font-mono" style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-emerald)', marginBottom: '8px' }}>
                {xpIn.toFixed(1)} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>projected pts</span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div>Price: £{costIn.toFixed(1)}m</div>
                <div>Expected Goals (xG90): {xgIn.toFixed(2)}</div>
                <div>Expected Assists (xA90): {xaIn.toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="compare-workbench-container" style={{ margin: '20px 0', background: 'var(--bg-surface-1)', border: '1px dashed var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: '20px', textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--accent-emerald)', marginBottom: '6px' }}>
            <Scales size={20} weight="bold" />
            <span style={{ fontWeight: 700, fontSize: '14px' }}>Head-to-Head Transfer Simulator Ready</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0 }}>
            Click the <strong style={{ color: 'var(--text-primary)' }}>&quot;Compare&quot;</strong> button on any player in the Transfer Market below to test a live swap against your squad and inspect point, budget, and threat deltas.
          </p>
        </div>
      )}

      {/* Transfer Marketplace */}
      <div className="data-table-container" style={{ marginTop: '20px' }}>
        <div className="scout-controls">
          <div className="scout-title-group">
            <span className="scout-title">Player Scout &amp; Transfer Market</span>
            <span className="scout-hint">(Click row to view stats · Click Compare to test transfer)</span>
          </div>

          <div className="scout-filters">
            {/* Search Input */}
            <div className="scout-search-wrap">
              <MagnifyingGlass size={14} className="scout-search-icon" />
              <input
                type="text"
                placeholder="Search player or team..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                aria-label="Search players by name or club"
                className="scout-search-input"
              />
            </div>

            {/* Position Filter */}
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

            {/* Max Price Slider */}
            <div className="scout-price-control">
              <span>Max: £{maxPrice}m</span>
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

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              aria-label="Sort players by metric"
              className="scout-sort-select"
            >
              <option value="xP">Highest Projected Points</option>
              <option value="cost_desc">Price (High to Low)</option>
              <option value="cost_asc">Price (Low to High)</option>
            </select>
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
                <th>Projected Points</th>
                <th>Expected Goals (xG90)</th>
                <th>Expected Assists (xA90)</th>
                <th>Start Chance</th>
                <th style={{ textAlign: 'center' }}>Action</th>
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
                  aria-label={`${p.web_name}, ${p.position}, £${Number(p.now_cost || p.cost || 0).toFixed(1)}M, ${Number(p.expected_points || 0).toFixed(1)} points`}
                  style={{ cursor: 'pointer' }}
                  title="Click to view detailed point projections"
                >
                  <td style={{ position: 'sticky', left: 0, zIndex: 10, fontWeight: 700, color: 'var(--text-primary)', background: 'var(--bg-surface-1)' }}>
                    {p.web_name}
                  </td>
                  <td>
                    <span className={`player-position-pill ${p.position}`}>{p.position}</span>
                  </td>
                  <td>{p.team}</td>
                  <td className="font-mono">£{Number(p.now_cost || p.cost || 0).toFixed(1)}m</td>
                  <td className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                    {Number(p.expected_points || 0).toFixed(1)} pts
                  </td>
                  <td className="font-mono">{Number(p.expected_goals_per_90 || p.short_form_expected_goals_90 || 0).toFixed(2)}</td>
                  <td className="font-mono">{Number(p.expected_assists_per_90 || p.short_form_expected_assists_90 || 0).toFixed(2)}</td>
                  <td className="font-mono">{((p.p_start || 0.85) * 100).toFixed(0)}%</td>
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleSelectCompareIn(p)}
                      className="pos-filter-btn"
                      style={{
                        padding: '3px 8px',
                        fontSize: '11px',
                        background: playerIn?.web_name === p.web_name ? 'var(--accent-emerald)' : undefined,
                        color: playerIn?.web_name === p.web_name ? 'var(--text-inverse)' : undefined
                      }}
                      title="Compare this player against your squad"
                    >
                      Compare
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
