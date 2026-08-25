import React from 'react';

export default function Header({ activeTab, setActiveTab, liveData, selectedStrategy, setSelectedStrategy }) {
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

      <nav className="nav-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <select
          value={selectedStrategy}
          onChange={e => setSelectedStrategy(e.target.value)}
          style={{
            background: 'var(--bg-surface-2)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-sm)',
            padding: '5px 10px',
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
