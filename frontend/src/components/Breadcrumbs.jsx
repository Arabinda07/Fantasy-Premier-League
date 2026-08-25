import React from 'react';
import { CaretRight, House } from '@phosphor-icons/react';

export default function Breadcrumbs({ activeTab, onNavigateTab, subItem, onClearSubItem }) {
  const tabLabels = {
    pitch: 'Matchday XI',
    transfers: 'Transfer Planner',
    fixtures: 'Fixture Run',
    market: 'Price Alerts',
    math: 'Points Breakdown'
  };

  const currentTabLabel = tabLabels[activeTab] || 'Matchday XI';

  return (
    <nav aria-label="Breadcrumb" className="breadcrumbs-bar">
      <div className="breadcrumbs-container">
        {/* L0: Home */}
        <button
          onClick={() => {
            onNavigateTab('pitch');
            if (onClearSubItem) onClearSubItem();
          }}
          className="breadcrumb-item breadcrumb-link"
          title="Return to Matchday XI"
        >
          <House size={14} weight="bold" />
          <span>Home</span>
        </button>

        <CaretRight size={12} className="breadcrumb-separator" />

        {/* L1: Active Section */}
        {subItem ? (
          <button
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
