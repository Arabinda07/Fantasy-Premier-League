import React from 'react';
import {
  SoccerBall,
  ArrowsLeftRight,
  GridNine,
  TrendUp,
  Flask,
  UsersThree,
  ArrowsClockwise
} from '@phosphor-icons/react';

export default function Header({
  activeTab,
  setActiveTab,
  liveData,
  onOpenSyncModal
}) {
  const tabs = [
    { id: 'pitch', label: 'Matchday XI', icon: SoccerBall },
    { id: 'transfers', label: '5-Week Planner', icon: ArrowsLeftRight },
    { id: 'rivals', label: 'Rival Radar', icon: UsersThree },
    { id: 'fixtures', label: 'Fixture Ticker', icon: GridNine },
    { id: 'market', label: 'Price Tracker', icon: TrendUp },
    { id: 'math', label: 'Points Studio', icon: Flask }
  ];

  const manager = liveData?.manager_profile;

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        {/* Brand section */}
        <div className="brand-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ background: 'var(--accent-emerald)', color: 'var(--text-inverse)', padding: '4px 6px', borderRadius: 'var(--radius-xs)', display: 'flex', alignItems: 'center' }}>
              <SoccerBall size={16} weight="fill" />
            </div>
            <span className="brand-title">FPL Quant Cockpit</span>
          </div>
          <span className="brand-meta">
            {liveData?.season || '2026-27'} · GW{liveData?.gameweek || 2}
          </span>
        </div>

        {/* Center navigation tabs */}
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

        {/* Right Action: Sync Team Button */}
        <div className="nav-controls">
          <button
            className="sync-team-nav-btn"
            onClick={onOpenSyncModal}
            title="Sync Official FPL Team ID & Mini-League"
          >
            <ArrowsClockwise size={14} weight="bold" />
            <span className="sync-nav-text">
              {manager?.manager_name ? `${manager.manager_name.split(' ')[0]} (#${manager.entry_id || '9500404'})` : 'Sync My Team'}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
