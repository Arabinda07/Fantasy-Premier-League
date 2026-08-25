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
  liveData
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
      <div className="top-nav-inner">
        <div className="brand-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ background: 'var(--accent-emerald)', color: 'var(--text-inverse)', padding: '4px 6px', borderRadius: 'var(--radius-xs)', display: 'flex', alignItems: 'center' }}>
              <SoccerBall size={16} weight="fill" />
            </div>
            <span className="brand-title">FPL Matchday Hub</span>
          </div>
          <span className="brand-meta">
            {liveData?.season || '2026-27'} · GW{liveData?.gameweek || 2}
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
      </div>
    </header>
  );
}
