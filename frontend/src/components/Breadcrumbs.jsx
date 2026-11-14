import React from 'react';
import { Breadcrumbs as AstryxBreadcrumbs, BreadcrumbItem } from '@astryxdesign/core';
import { CaretRight, House } from '@phosphor-icons/react';

export default function Breadcrumbs({
  activeTab,
  activeChip = 'none',
  inspectedPlayer = null,
  activeFixture = null,
  onNavigateTab,
  onClearChip,
  onClearPlayer,
  onClearFixture,
  subItem,
  onClearSubItem
}) {
  const tabLabels = {
    pitch: 'My Lineup',
    transfers: 'Transfer Planner',
    rivals: 'Mini-Leagues & Rivals',
    fixtures: 'Fixture Ticker',
    market: 'Price Trends',
    math: 'Points Forecaster',
    vault: 'Historical Vault'
  };

  const resolvedSubItem = subItem || (
    inspectedPlayer
      ? inspectedPlayer.web_name || inspectedPlayer.name
      : activeFixture
        ? `${activeFixture.home_team || 'Home'} vs ${activeFixture.away_team || 'Away'}`
        : activeChip && activeChip !== 'none'
          ? `Chip: ${activeChip.toUpperCase()}`
          : null
  );

  const handleClear = () => {
    if (onClearSubItem) onClearSubItem();
    if (inspectedPlayer && onClearPlayer) onClearPlayer();
    else if (activeFixture && onClearFixture) onClearFixture();
    else if (activeChip && activeChip !== 'none' && onClearChip) onClearChip();
  };

  if (!resolvedSubItem) {
    return null;
  }

  const currentTabLabel = tabLabels[activeTab] || 'Matchday Starting XI';

  return (
    <div className="breadcrumbs-bar">
      <AstryxBreadcrumbs
        className="breadcrumbs-container"
        variant="supporting"
        separator={<CaretRight size={12} className="breadcrumb-separator" />}
      >
        <BreadcrumbItem
          onClick={() => {
            onNavigateTab('pitch');
            handleClear();
          }}
          startIcon={<House size={14} weight="bold" />}
          className="breadcrumb-item breadcrumb-link"
        >
          Home
        </BreadcrumbItem>

        <BreadcrumbItem
          onClick={handleClear}
          isCurrent={!resolvedSubItem}
          className="breadcrumb-item breadcrumb-link"
        >
          {currentTabLabel}
        </BreadcrumbItem>

        {resolvedSubItem && (
          <BreadcrumbItem isCurrent className="breadcrumb-item active">
            {resolvedSubItem}
          </BreadcrumbItem>
        )}
      </AstryxBreadcrumbs>
    </div>
  );
}
