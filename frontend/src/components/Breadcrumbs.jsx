import React from 'react';
import { CaretRight, House } from '@phosphor-icons/react';

export default function Breadcrumbs({ activeTab, onNavigateTab, subItem, onClearSubItem }) {
  const tabLabels = {
    pitch: 'My Lineup',
    transfers: 'Transfer Planner',
    rivals: 'Mini-Leagues & Rivals',
    fixtures: 'Fixture Ticker',
    market: 'Price Trends',
    math: 'Points Forecaster'
  };

  if (!subItem) {
    return null;
  }

  const currentTabLabel = tabLabels[activeTab] || 'Matchday Starting XI';

  return (
    <nav aria-label="Breadcrumb" className="breadcrumbs-bar">
      <div className="breadcrumbs-container">
        {/* L0: Home */}
        <button
          type="button"
          onClick={() => {
            onNavigateTab('pitch');
            if (onClearSubItem) onClearSubItem();
          }}
          className="breadcrumb-item breadcrumb-link"
          title="Return to Matchday Starting XI"
        >
          <House size={14} weight="bold" />
          <span>Home</span>
        </button>

        <CaretRight size={12} className="breadcrumb-separator" />

        {/* L1: Active Section */}
        {subItem ? (
          <button
            type="button"
            onClick={() => {
              if (onClearSubItem) onClearSubItem();
            }}
            className="breadcrumb-item breadcrumb-link"
          >
            {currentTabLabel}
          </button>
        ) : (
          <span className="breadcrumb-item active" aria-current="page">
            {currentTabLabel}
          </span>
        )}

        {/* L2: Detail Sub-Item (Player or Comparison) */}
        {subItem && (
          <>
            <CaretRight size={12} className="breadcrumb-separator" />
            <span className="breadcrumb-item active" aria-current="page">
              {subItem}
            </span>
          </>
        )}
      </div>
    </nav>
  );
}
