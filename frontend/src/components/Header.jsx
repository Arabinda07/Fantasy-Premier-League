import React from 'react';
import {
  SoccerBall,
  ArrowsLeftRight,
  GridNine,
  TrendUp,
  Flask
} from '@phosphor-icons/react';

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
    { id: 'pitch', label: 'Matchday XI', icon: SoccerBall },
    { id: 'transfers', label: 'Transfer Planner', icon: ArrowsLeftRight },
    { id: 'fixtures', label: 'Fixture Run', icon: GridNine },
    { id: 'market', label: 'Price Alerts', icon: TrendUp },
    { id: 'math', label: 'Points Breakdown', icon: Flask }
  ];

  return (
    <header className="top-nav">
      <div className="brand-section">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: 'var(--accent-emerald)', color: '#090D16', padding: '4px 6px', borderRadius: 'var(--radius-xs)', display: 'flex', alignItems: 'center' }}>
            <SoccerBall size={16} weight="fill" />
          </div>
          <span className="brand-title">FPL Matchday Hub</span>
        </div>
        <span className="brand-meta">
          {liveData?.season || '2026-27'} · Gameweek {liveData?.gameweek || 2}
        </span>
      </div>

      <div className="nav-tabs-wrapper">
        <nav className="nav-tabs" role="tablist" aria-label="Main Navigation">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                role="tab"
                aria-selected={isActive}
                aria-controls={`panel-${tab.id}`}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} weight={isActive ? "fill" : "bold"} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="nav-controls">
        {/* Chip Strategy Global Selector */}
        <select
          value={activeChip}
          onChange={e => setActiveChip(e.target.value)}
          aria-label="Select FPL Chip"
          className={`nav-select ${activeChip !== 'none' ? 'active-chip' : ''}`}
        >
          <option value="none">Standard Lineup</option>
          <option value="wildcard">Wildcard Active</option>
          <option value="freehit">Free Hit Active</option>
          <option value="bboost">Bench Boost Active</option>
          <option value="3xc">Triple Captain Active</option>
        </select>

        {/* Strategy Profile Selector */}
        <select
          value={selectedStrategy}
          onChange={e => setSelectedStrategy(e.target.value)}
          aria-label="Select Optimizer Strategy"
          className="nav-select"
        >
          <option value="pure_xp">Balanced Points</option>
          <option value="rank_protect">Rank Protection (High Ownership)</option>
          <option value="differential_chase">Differential Upside</option>
        </select>
      </div>
    </header>
  );
}
