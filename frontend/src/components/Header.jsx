import React from 'react';

export default function Header({
  activeTab,
  setActiveTab,
  liveData,
  selectedStrategy,
  setSelectedStrategy,
  activeChip = 'none',
  setActiveChip = () => {}
}) {
  const tabs = [
    { id: 'pitch', label: 'Tactical Pitch', icon: '⚽' },
    { id: 'transfers', label: 'Transfer Hub (3-GW)', icon: '🔄' },
    { id: 'fixtures', label: '38-GW Heatmap', icon: '🗺️' },
    { id: 'market', label: 'Market Velocity', icon: '⚡' },
    { id: 'math', label: '11-Component Studio', icon: '🔬' }
  ];

  return (
    <header className="top-nav">
      <div className="brand-section">
        <span className="brand-badge">FPL QUANT</span>
        <span className="brand-title">Intelligence Terminal</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
          {liveData?.season || '2026-27'} · GW{liveData?.gameweek || 2}
        </span>
      </div>

      <nav className="nav-tabs" role="tablist" aria-label="Main Navigation Tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span aria-hidden="true">{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Chip Strategy Global Selector */}
        <select
          value={activeChip}
          onChange={e => setActiveChip(e.target.value)}
          aria-label="Active Chip Simulation Selector"
          style={{
            background: activeChip !== 'none' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-surface-2)',
            color: activeChip !== 'none' ? 'var(--accent-emerald)' : 'var(--text-primary)',
            border: activeChip !== 'none' ? '1px solid var(--accent-emerald)' : '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 10px',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          <option value="none">Chip: Standard Lineup</option>
          <option value="wildcard">🃏 Chip: Wildcard (£100M)</option>
          <option value="freehit">⚡ Chip: Free Hit</option>
          <option value="bboost">🚀 Chip: Bench Boost</option>
          <option value="3xc">👑 Chip: Triple Captain</option>
        </select>

        {/* Strategy Profile Selector */}
        <select
          value={selectedStrategy}
          onChange={e => setSelectedStrategy(e.target.value)}
          aria-label="Select Optimization Strategy Mode"
          style={{
            background: 'var(--bg-surface-2)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 10px',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer'
          }}
        >
          <option value="pure_xp">Strategy: Pure xP (Neutral)</option>
          <option value="rank_protect">Strategy: Rank Protect (High EO)</option>
          <option value="differential_chase">Strategy: Differential Chase</option>
        </select>
      </div>
    </header>
  );
}
