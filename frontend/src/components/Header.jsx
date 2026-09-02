import React from 'react';
import {
  SoccerBall,
  ArrowsLeftRight,
  GridNine,
  TrendUp,
  Flask,
  UsersThree,
  User,
  Gear
} from '@phosphor-icons/react';

export default function Header({
  activeTab,
  setActiveTab,
  liveData,
  selectedGw,
  availableGameweeks,
  onSelectGw,
  onOpenSyncModal,
  strategy = 'pure_xp',
  onSelectStrategy,
  activeChip = 'none'
}) {
  const tabs = [
    {
      id: 'pitch',
      label: 'My Lineup',
      shortLabel: 'Lineup',
      icon: SoccerBall,
      badge: activeChip !== 'none' ? activeChip.toUpperCase() : null,
      badgeType: 'chip'
    },
    {
      id: 'transfers',
      label: 'Transfer Planner',
      shortLabel: 'Planner',
      icon: ArrowsLeftRight,
      badge: '1 FT',
      badgeType: 'neutral'
    },
    {
      id: 'rivals',
      label: 'Mini-Leagues',
      shortLabel: 'Rivals',
      icon: UsersThree
    },
    {
      id: 'fixtures',
      label: 'Fixture Ticker',
      shortLabel: 'Fixtures',
      icon: GridNine
    },
    {
      id: 'market',
      label: 'Price Trends',
      shortLabel: 'Prices',
      icon: TrendUp,
      badge: '🔥',
      badgeType: 'alert'
    },
    {
      id: 'math',
      label: 'Points Forecaster',
      shortLabel: 'Forecaster',
      icon: Flask
    }
  ];

  const manager = liveData?.manager_profile;

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        {/* Tier 1: Brand section */}
        <div className="brand-section">
          <div className="brand-badge-group">
            <div className="brand-icon-box">
              <SoccerBall size={16} weight="fill" />
            </div>
            <span className="brand-title brand-title-full">FPL Dugout</span>
            <span className="brand-title brand-title-short">Dugout</span>
          </div>
          <span className="brand-meta font-mono" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span className="brand-season-tag">{liveData?.season || '2026-27'}</span>
            <span className="brand-dot">·</span>
            {availableGameweeks && availableGameweeks.length > 1 ? (
              <select
                value={selectedGw || liveData?.gameweek || 1}
                onChange={(e) => onSelectGw && onSelectGw(Number(e.target.value))}
                className="font-mono brand-gw-select"
                aria-label="Select Gameweek"
              >
                {availableGameweeks.map(gw => (
                  <option key={gw} value={gw}>GW{gw}</option>
                ))}
              </select>
            ) : (
              <span className="brand-gw-static">GW{liveData?.gameweek || selectedGw || 1}</span>
            )}
          </span>
        </div>

        {/* Tier 2: Center navigation tabs (Full-width scroll rail on mobile) */}
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
                  <span className="tab-label-full">{tab.label}</span>
                  <span className="tab-label-short">{tab.shortLabel}</span>
                  {tab.badge && (
                    <span className={`tab-pip font-mono ${tab.badgeType || ''}`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tier 1 / Right Action: Manager Badge & Sync Switcher */}
        <div className="nav-controls">
          <button
            className="live-manager-chip font-mono"
            onClick={onOpenSyncModal}
            title="Configure FPL Team ID & Mini-League Tracker"
            aria-label="Manager Settings"
          >
            <span className="live-sync-pulse" />
            <User size={13} weight="bold" />
            <span className="manager-chip-name">
              {manager?.manager_name
                ? `${manager.manager_name.split(' ')[0]} (#${manager.entry_id || '9500404'})`
                : 'Sync Team'}
            </span>
            <Gear size={12} weight="bold" style={{ opacity: 0.6, marginLeft: '2px' }} />
          </button>
        </div>
      </div>
    </header>
  );
}
