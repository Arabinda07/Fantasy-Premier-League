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
  selectedGw,
  availableGameweeks,
  onSelectGw,
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
          <div className="brand-badge-group">
            <div className="brand-icon-box">
              <SoccerBall size={16} weight="fill" />
            </div>
            <span className="brand-title">FPL Analytics Terminal</span>
          </div>
          <span className="brand-meta font-mono" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span>{liveData?.season || '2026-27'}</span>
            <span>·</span>
            {availableGameweeks && availableGameweeks.length > 1 ? (
              <select
                value={selectedGw || liveData?.gameweek || 1}
                onChange={(e) => onSelectGw && onSelectGw(Number(e.target.value))}
                className="font-mono"
                style={{
                  background: 'var(--bg-surface-2, #182035)',
                  color: 'var(--accent-emerald, #10B981)',
                  border: '1px solid var(--border-subtle, rgba(255,255,255,0.15))',
                  borderRadius: '3px',
                  padding: '1px 5px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  outline: 'none',
                }}
                aria-label="Select Gameweek"
              >
                {availableGameweeks.map(gw => (
                  <option key={gw} value={gw}>GW{gw}</option>
                ))}
              </select>
            ) : (
              <span>GW{liveData?.gameweek || selectedGw || 1}</span>
            )}
          </span>
        </div>

        {/* Center navigation tabs */}
        <div className="nav-tabs-wrapper">
          <nav className="nav-tabs segmented-nav-rail" role="tablist" aria-label="Main Navigation">
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
                  <Icon size={15} weight={isActive ? "fill" : "bold"} />
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
            <span className="sync-nav-text font-mono">
              {manager?.manager_name ? `${manager.manager_name.split(' ')[0]} (#${manager.entry_id || '9500404'})` : 'Sync My Team'}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
