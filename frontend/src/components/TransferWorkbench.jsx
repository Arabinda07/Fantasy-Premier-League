import React, { useState, useMemo } from 'react';

export default function TransferWorkbench({ roadmap, allPlayers, onInspectPlayer }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPos, setSelectedPos] = useState('ALL');
  const [maxPrice, setMaxPrice] = useState(15.5);
  const [sortBy, setSortBy] = useState('xP');

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

  return (
    <div>
      {/* 3-Gameweek Lookahead Roadmap */}
      <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>
        MULTI-GAMEWEEK TRANSFER ROADMAP (3-GW LOOKAHEAD)
      </h3>

      <div className="roadmap-grid">
        {(roadmap || []).map(step => (
          <div key={step.gw} className={`roadmap-card ${step.gw === 2 ? 'active' : ''}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span className="roadmap-gw-badge">GAMEWEEK {step.gw}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Bank: £{Number(step.bank || 0).toFixed(1)}M
              </span>
            </div>

            <div className="transfer-pair">
              {step.transfers_in?.length > 0 ? (
                <>
                  <div className="transfer-row">
                    <span className="transfer-label in">IN</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      {step.transfers_in.join(', ')}
                    </span>
                  </div>
                  <div className="transfer-row">
                    <span className="transfer-label out">OUT</span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {step.transfers_out.join(', ')}
                    </span>
                  </div>
                </>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '13px', fontStyle: 'italic' }}>
                  Roll Free Transfer (Accumulate 2 FTs)
                </div>
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Projected xP</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                {Number(step.net_xp || 0).toFixed(2)} pts
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Transfer Marketplace */}
      <div className="data-table-container" style={{ marginTop: '32px' }}>
        <div style={{ padding: '16px 20px', background: 'var(--bg-surface-2)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
              PLAYER VALUATION & TRANSFER MARKETPLACE
            </span>
            <span style={{ marginLeft: '10px', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Showing {filteredPlayers.length} assets
            </span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
            {/* Search Input */}
            <input
              type="text"
              placeholder="Search player or team..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                background: 'var(--bg-surface-1)',
                border: '1px solid var(--border-medium)',
                color: 'var(--text-primary)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                width: '180px'
              }}
            />

            {/* Position Filter */}
            <div style={{ display: 'flex', gap: '2px' }}>
              {['ALL', 'GK', 'DEF', 'MID', 'FWD'].map(pos => (
                <button
                  key={pos}
                  onClick={() => setSelectedPos(pos)}
                  style={{
                    background: selectedPos === pos ? 'var(--accent-emerald)' : 'var(--bg-surface-1)',
                    color: selectedPos === pos ? '#06261C' : 'var(--text-secondary)',
                    border: '1px solid var(--border-subtle)',
                    padding: '4px 8px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    borderRadius: 'var(--radius-xs)',
                    cursor: 'pointer'
                  }}
                >
                  {pos}
                </button>
              ))}
            </div>

            {/* Max Price Slider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              <span>Max: £{maxPrice}M</span>
              <input
                type="range"
                min="4.0"
                max="15.5"
                step="0.5"
                value={maxPrice}
                onChange={e => setMaxPrice(Number(e.target.value))}
                style={{ width: '80px', cursor: 'pointer' }}
              />
            </div>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              style={{
                background: 'var(--bg-surface-1)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-sm)',
                padding: '5px 8px',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer'
              }}
            >
              <option value="xP">Sort by xP (High to Low)</option>
              <option value="cost_desc">Cost (High to Low)</option>
              <option value="cost_asc">Cost (Low to High)</option>
            </select>
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Club</th>
              <th>Cost (£M)</th>
              <th>Projected xP</th>
              <th>xG90</th>
              <th>xA90</th>
              <th>P(Start)</th>
              <th>P(Clean Sheet)</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredPlayers.map(p => (
              <tr key={p.player_code || p.id}>
                <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {p.web_name}
                </td>
                <td>
                  <span className={`player-position-pill ${p.position}`}>{p.position}</span>
                </td>
                <td>{p.team}</td>
                <td className="font-mono">£{Number(p.now_cost || p.cost || 0).toFixed(1)}</td>
                <td className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                  {Number(p.expected_points || 0).toFixed(2)}
                </td>
                <td className="font-mono">{Number(p.expected_goals_per_90 || p.short_form_expected_goals_90 || 0).toFixed(2)}</td>
                <td className="font-mono">{Number(p.expected_assists_per_90 || p.short_form_expected_assists_90 || 0).toFixed(2)}</td>
                <td className="font-mono">{((p.p_start || 0.85) * 100).toFixed(0)}%</td>
                <td className="font-mono">{((p.p_clean_sheet || 0.3) * 100).toFixed(0)}%</td>
                <td>
                  <button
                    onClick={() => onInspectPlayer(p)}
                    style={{
                      background: 'var(--bg-surface-subtle)',
                      border: '1px solid var(--border-medium)',
                      color: 'var(--text-primary)',
                      padding: '3px 8px',
                      fontSize: '11px',
                      borderRadius: 'var(--radius-xs)',
                      cursor: 'pointer'
                    }}
                  >
                    Inspect DNA
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
