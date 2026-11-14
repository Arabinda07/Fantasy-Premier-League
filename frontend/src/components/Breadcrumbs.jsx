import React from 'react';
import { Breadcrumbs as AstryxBreadcrumbs, BreadcrumbItem } from '@astryxdesign/core';
import { CaretRight, House } from '@phosphor-icons/react';

export default function Breadcrumbs({ activeTab, onNavigateTab, subItem, onClearSubItem }) {
  const tabLabels = {
    pitch: 'My Lineup',
    transfers: 'Transfer Planner',
    rivals: 'Mini-Leagues & Rivals',
    fixtures: 'Fixture Ticker',
    market: 'Price Trends',
    math: 'Points Forecaster',
    vault: 'Historical Vault'
  };

  if (!subItem) {
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
            if (onClearSubItem) onClearSubItem();
          }}
          startIcon={<House size={14} weight="bold" />}
          className="breadcrumb-item breadcrumb-link"
        >
          Home
        </BreadcrumbItem>

        <BreadcrumbItem
          onClick={() => {
            if (onClearSubItem) onClearSubItem();
          }}
          isCurrent={!subItem}
          className="breadcrumb-item breadcrumb-link"
        >
          {currentTabLabel}
        </BreadcrumbItem>

        {subItem && (
          <BreadcrumbItem isCurrent className="breadcrumb-item active">
            {subItem}
          </BreadcrumbItem>
        )}
      </AstryxBreadcrumbs>
    </div>
  );
}
