import React, { useState, useMemo, useEffect } from 'react';
import {
  MagnifyingGlass,
  Scales,
  X,
  TrendUp,
  TrendDown,
  ArrowsLeftRight
} from '@phosphor-icons/react';

export default function TransferWorkbench({
  roadmap = [],
  allPlayers = [],
  squadPlayers = [],
  activeGwItem = null,
  activeGwIndex = 0,
  selectedTransferPair = null,
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

  // Current Horizon Plan derived from activeGwItem, roadmap[activeGwIndex], or roadmap[0]
  const currentPlan = activeGwItem || (roadmap && roadmap.length > 0 ? roadmap[activeGwIndex || 0] : null);

  // Compute recommended pairs from the active roadmap item
  const recommendedPairs = useMemo(() => {
    if (!currentPlan || !Array.isArray(currentPlan.transfers_in) || currentPlan.transfers_in.length === 0) {
      return [];
    }

    const pairs = [];
    const pool = allPlayers || [];
    const squad = defaultSquadList || [];

    currentPlan.transfers_in.forEach((inName, idx) => {
      const outName = currentPlan.transfers_out?.[idx] || '';

      const pIn = pool.find(p => (p.web_name || '').toLowerCase() === (inName || '').toLowerCase()) ||
                  pool.find(p => (p.web_name || '').toLowerCase().includes((inName || '').toLowerCase()));

      const pOut = squad.find(p => (p.web_name || '').toLowerCase() === (outName || '').toLowerCase()) ||
                   squad.find(p => (p.web_name || '').toLowerCase().includes((outName || '').toLowerCase())) ||
                   pool.find(p => (p.web_name || '').toLowerCase() === (outName || '').toLowerCase());

      if (pIn && pOut) {
        const xpInVal = Number(pIn.expected_points ?? pIn.xp ?? pIn.xP ?? 0);
        const xpOutVal = Number(pOut.expected_points ?? pOut.xp ?? pOut.xP ?? 0);
        const costInVal = Number(pIn.now_cost ?? pIn.cost ?? 0);
        const costOutVal = Number(pOut.now_cost ?? pOut.cost ?? 0);

        pairs.push({
          inPlayer: pIn,
          outPlayer: pOut,
          inName: pIn.web_name || inName,
          outName: pOut.web_name || outName,
          xpDelta: Number((xpInVal - xpOutVal).toFixed(1)),
          costDelta: Number((costInVal - costOutVal).toFixed(1)),
        });
      }
    });

    return pairs;
  }, [currentPlan, allPlayers, defaultSquadList]);

  // Sync with selectedTransferPair prop or auto-populate 1st recommended move
  useEffect(() => {
    if (selectedTransferPair?.inName && selectedTransferPair?.outName) {
      const pool = allPlayers || [];
      const squad = defaultSquadList || [];
      const pIn = pool.find(p => (p.web_name || '').toLowerCase() === selectedTransferPair.inName.toLowerCase()) ||
                  pool.find(p => (p.web_name || '').toLowerCase().includes(selectedTransferPair.inName.toLowerCase()));
      const pOut = squad.find(p => (p.web_name || '').toLowerCase() === selectedTransferPair.outName.toLowerCase()) ||
                   squad.find(p => (p.web_name || '').toLowerCase().includes(selectedTransferPair.outName.toLowerCase())) ||
                   pool.find(p => (p.web_name || '').toLowerCase() === selectedTransferPair.outName.toLowerCase());

      if (pIn && pOut) {
        setPlayerIn(pIn);
        setPlayerOut(pOut);
        if (onCompareChange) onCompareChange(`${pIn.web_name} vs ${pOut.web_name}`);
      }
    } else if (!playerIn && !playerOut && recommendedPairs.length > 0) {
      const first = recommendedPairs[0];
      setPlayerIn(first.inPlayer);
      setPlayerOut(first.outPlayer);
      if (onCompareChange) onCompareChange(`${first.inPlayer.web_name} vs ${first.outPlayer.web_name}`);
    }
  }, [selectedTransferPair, recommendedPairs]);

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
      {/* Recommended Tactical Moves Panel */}
      {recommendedPairs.length > 0 && (
        <div className="recommended-moves-panel">
          <div className="rec-panel-header">
            <div className="rec-panel-title-group">
              <span className="rec-panel-eyebrow font-mono">
                {currentPlan?.gw ? `GW${currentPlan.gw} RECOMMENDED TRANSFERS` : 'RECOMMENDED TRANSFERS'}
              </span>
              <span className="rec-panel-subtitle">
                Target moves calculated by transfer model to maximize expected points
              </span>
            </div>
            <span className="rec-panel-badge font-mono">
              {recommendedPairs.length} {recommendedPairs.length === 1 ? 'TRANSFER' : 'TRANSFERS'}
            </span>
          </div>

          <div className="rec-pairs-grid">
            {recommendedPairs.map((pair, idx) => {
              const isCurrentActive =
                playerIn?.player_code === pair.inPlayer.player_code &&
                playerOut?.player_code === pair.outPlayer.player_code;

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setPlayerIn(pair.inPlayer);
                    setPlayerOut(pair.outPlayer);
                    if (onCompareChange) {
                      onCompareChange(`${pair.inPlayer.web_name} vs ${pair.outPlayer.web_name}`);
                    }
                  }}
                  className={`rec-pair-card ${isCurrentActive ? 'active' : ''}`}
                >
                  <div className="rec-pair-flow">
                    <div className="rec-card-player out">
                      <span className="rec-action-badge out font-mono">SELL</span>
                      <span className="rec-card-name">{pair.outName}</span>
                      <span className="rec-card-meta font-mono">
                        [{pair.outPlayer.position}] · £{Number(pair.outPlayer.cost || pair.outPlayer.now_cost || 0).toFixed(1)}m
                      </span>
                    </div>

                    <ArrowsLeftRight size={16} className="rec-flow-arrow" />

                    <div className="rec-card-player in">
                      <span className="rec-action-badge in font-mono">BUY</span>
                      <span className="rec-card-name">{pair.inName}</span>
                      <span className="rec-card-meta font-mono">
                        [{pair.inPlayer.position}] · £{Number(pair.inPlayer.cost || pair.inPlayer.now_cost || 0).toFixed(1)}m
                      </span>
                    </div>
                  </div>

                  <div className="rec-pair-footer font-mono">
                    <span className="rec-delta-tag font-mono">
                      {pair.xpDelta >= 0 ? `+${pair.xpDelta.toFixed(1)}` : pair.xpDelta.toFixed(1)} xP
                    </span>
                    <span className="rec-cost-tag font-mono">
                      {pair.costDelta <= 0
                        ? `Saves £${Math.abs(pair.costDelta).toFixed(1)}m`
                        : `Costs +£${pair.costDelta.toFixed(1)}m`}
                    </span>
                    <span className={`rec-status-tag font-mono ${isCurrentActive ? 'active' : ''}`}>
                      {isCurrentActive ? '[ACTIVE IN WORKBENCH]' : 'COMPARE ↗'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Side-by-Side Transfer Comparison Workbench */}
      {playerIn ? (
        <div className="compare-workbench-container">
          <div className="compare-workbench-header">
            <div className="compare-header-title">
              <Scales size={16} weight="bold" className="modal-unboxed-icon" />
              <span className="compare-title-text font-mono">
                DIRECT TRANSFER SWAP COMPARISON
              </span>
            </div>
            <button
              onClick={handleClearCompare}
              className="compare-close-btn font-mono"
              aria-label="Close Comparison"
            >
              <X size={14} weight="bold" />
              <span>Close</span>
            </button>
          </div>

          <div className="compare-grid">
            {/* Player OUT Card */}
            <div className="compare-player-card out-card">
              <div className="card-role-header">
                <span className="transfer-role-tag out font-mono">[OUT] SELLING</span>
                <select
                  value={playerOut?.player_code || ''}
                  onChange={(e) => {
                    const found = defaultSquadList.find(p => String(p.player_code) === e.target.value);
                    if (found) setPlayerOut(found);
                  }}
                  className="wire-select compare-player-select font-mono"
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
                <span className="dna-player-pos font-mono">[{playerOut?.position}]</span>
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
              <div className={`compare-delta-readout font-mono ${xpDelta >= 0 ? 'positive' : 'negative'}`}>
                {xpDelta >= 0 ? <TrendUp size={16} weight="bold" /> : <TrendDown size={16} weight="bold" />}
                <span>{xpDelta >= 0 ? `+${xpDelta.toFixed(1)}` : xpDelta.toFixed(1)} xP</span>
              </div>
              <div className="delta-cost-tag font-mono">
                {costDelta <= 0 ? `Saves £${Math.abs(costDelta).toFixed(1)}m` : `Costs +£${costDelta.toFixed(1)}m`}
              </div>
            </div>

            {/* Player IN Card */}
            <div className="compare-player-card in-card">
              <div className="card-role-header">
                <span className="transfer-role-tag in font-mono">[IN] BUYING</span>
                <span className="in-target-tag font-mono">[TARGET ACQUISITION]</span>
              </div>

              <div className="compare-player-name-row">
                <span className="dna-player-pos font-mono">[{playerIn?.position}]</span>
                <span className="compare-player-name">{playerIn?.web_name}</span>
                <span className="compare-player-team font-mono">({playerIn?.team})</span>
              </div>

              <div className="compare-xp-val font-mono">
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
        <div className="compare-workbench-compact-cue font-mono">
          <div className="cue-content">
            <Scales size={14} weight="bold" className="cue-icon" />
            <span>Select any player in the marketplace below to simulate a direct swap against your squad</span>
          </div>
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
                className="scout-search-input font-mono"
              />
            </div>

            <div role="group" aria-label="Filter by player position" className="wire-segments">
              {['ALL', 'GK', 'DEF', 'MID', 'FWD'].map(pos => (
                <button
                  key={pos}
                  type="button"
                  onClick={() => setSelectedPos(pos)}
                  aria-pressed={selectedPos === pos}
                  className={`wire-segment font-mono ${selectedPos === pos ? 'active' : ''}`}
                >
                  {pos}
                </button>
              ))}
            </div>

            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              aria-label="Sort players by metric"
              className="wire-select scout-sort-select font-mono"
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
              <span className="presets-label font-mono">QUICK:</span>
              {[
                { label: '< £5.0m', val: 5.0 },
                { label: '< £7.5m', val: 7.5 },
                { label: '< £10.0m', val: 10.0 },
                { label: 'ALL', val: 15.5 }
              ].map(preset => (
                <button
                  key={preset.label}
                  type="button"
                  className={`preset-btn font-mono ${maxPrice === preset.val ? 'active' : ''}`}
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
                <th scope="col" style={{ position: 'sticky', left: 0, zIndex: 20 }}>Player</th>
                <th scope="col">Pos</th>
                <th scope="col">Club</th>
                <th scope="col">Price</th>
                <th scope="col">Exp Pts</th>
                <th scope="col">xG / 90</th>
                <th scope="col">xA / 90</th>
                <th scope="col">Start %</th>
                <th scope="col" style={{ textAlign: 'center' }}>Compare</th>
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
                  <th scope="row" style={{ position: 'sticky', left: 0, zIndex: 10, fontWeight: 800, textAlign: 'left', color: 'var(--text-primary)', background: 'var(--bg-surface-1)' }}>
                    {p.web_name}
                  </th>
                  <td>
                    <span className="dna-player-pos font-mono">[{p.position}]</span>
                  </td>
                  <td className="font-mono" style={{ color: 'var(--text-secondary)' }}>{p.team}</td>
                  <td className="font-mono">£{Number(p.now_cost || p.cost || 0).toFixed(1)}m</td>
                  <td className="font-mono table-cell-xp">
                    {Number(p.expected_points ?? p.xp ?? p.xP ?? 0).toFixed(1)} pts
                  </td>
                  <td className="font-mono">{Number(p.expected_goals_per_90 ?? p.short_form_expected_goals_90 ?? p.xg90 ?? 0).toFixed(2)}</td>
                  <td className="font-mono">{Number(p.expected_assists_per_90 ?? p.short_form_expected_assists_90 ?? p.xa90 ?? 0).toFixed(2)}</td>
                  <td className="font-mono">{((p.p_start || 0.85) * 100).toFixed(0)}%</td>
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={() => handleSelectCompareIn(p)}
                      className={`compare-action-btn font-mono ${playerIn?.web_name === p.web_name ? 'active' : ''}`}
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
