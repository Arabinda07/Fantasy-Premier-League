import React, { useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  ArrowsLeftRight,
  CalendarCheck,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  ChartLine,
  Scales
} from '@phosphor-icons/react';
import TransferWorkbench from './TransferWorkbench';

const DEFAULT_5GW_ROADMAP = [
  { gw: 2, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 64.72, bank: 0.0, ft_available: 1 },
  { gw: 3, transfers_in: ['Canvot'], transfers_out: ['Ballard'], hits_taken: 0, net_xp: 62.16, bank: 0.0, ft_available: 2 },
  { gw: 4, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 64.16, bank: 0.0, ft_available: 1 },
  { gw: 5, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 63.35, bank: 0.0, ft_available: 2 },
  { gw: 6, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 62.65, bank: 0.0, ft_available: 1 }
];

export default function MultiGwPlanner({
  roadmap = [],
  squadPlayers = [],
  allPlayers = [],
  onInspectPlayer,
  onCompareChange
}) {
  const activeRoadmap = (roadmap && roadmap.length >= 5) ? roadmap : DEFAULT_5GW_ROADMAP;
  const [activeGwIndex, setActiveGwIndex] = useState(0);
  const [viewMode, setViewMode] = useState('roadmap'); // 'roadmap' | 'workbench' | 'both'

  // Compute multi-horizon totals & cumulative trajectory
  const trajectoryData = React.useMemo(() => {
    return activeRoadmap.reduce((acc, r, idx) => {
      const weeklyXp = Number(r.net_xp || 0);
      const prevTotal = idx > 0 ? acc[idx - 1].cumulativeXp : 0;
      const cumulativeXp = Number((prevTotal + weeklyXp).toFixed(1));
      acc.push({
        gw: `GW${r.gw}`,
        weeklyXp: Number(weeklyXp.toFixed(1)),
        cumulativeXp,
        bank: Number(r.bank || 0.0).toFixed(1),
        hits: r.hits_taken || 0
      });
      return acc;
    }, []);
  }, [activeRoadmap]);

  const totalHorizonXp = activeRoadmap.reduce((acc, r) => acc + (r.net_xp || 0), 0);
  const totalHits = activeRoadmap.reduce((acc, r) => acc + (r.hits_taken || 0), 0);

  return (
    <div className="view-fluid">
      {/* Sub-View Switcher Rail */}
      <div className="chip-switcher-bar" style={{ marginBottom: '16px' }}>
        <div className="chip-switcher-left">
          <span className="chip-switcher-label font-mono">Workspace</span>
          <div className="segmented-chip-rail">
            <button
              type="button"
              className={`segmented-chip-btn ${viewMode === 'roadmap' ? 'active' : ''}`}
              onClick={() => setViewMode('roadmap')}
            >
              <CalendarCheck size={14} weight={viewMode === 'roadmap' ? 'fill' : 'bold'} />
              <span>5-Week Roadmap</span>
            </button>
            <button
              type="button"
              className={`segmented-chip-btn ${viewMode === 'workbench' ? 'active' : ''}`}
              onClick={() => setViewMode('workbench')}
            >
              <Scales size={14} weight={viewMode === 'workbench' ? 'fill' : 'bold'} />
              <span>Transfer Scout &amp; Compare</span>
            </button>
            <button
              type="button"
              className={`segmented-chip-btn ${viewMode === 'both' ? 'active' : ''}`}
              onClick={() => setViewMode('both')}
            >
              <ArrowsLeftRight size={14} weight={viewMode === 'both' ? 'fill' : 'bold'} />
              <span>Unified Canvas</span>
            </button>
          </div>
        </div>
        <div className="chip-switcher-right font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {viewMode === 'roadmap' ? '5-Week Plan' : viewMode === 'workbench' ? 'Player Comparison' : 'Full Transfer View'}
        </div>
      </div>

      {(viewMode === 'roadmap' || viewMode === 'both') && (
        <>
          {/* Hero Header */}
          <div className="studio-hero-panel">
            <div className="studio-hero-header">
              <span className="studio-version font-mono">NEXT 5 GAMEWEEKS · GW2 TO GW6</span>
            </div>
            <h2 className="studio-title">5-Gameweek Transfer Planner &amp; Bank Strategy</h2>
            <p className="studio-description">
              Plan your transfers in advance, bank free transfers, and preview your points over the next 5 gameweeks.
            </p>

            {/* Horizon Metric Strip */}
            <div className="kpi-strip">
              <div className="kpi-card">
                <div className="kpi-label">5-Week Expected Total</div>
                <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
                  {totalHorizonXp.toFixed(1)} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
                </div>
                <div className="kpi-subtext">Projected score across 5 gameweeks</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Point Hits Planned</div>
                <div className="kpi-value font-mono" style={{ color: totalHits === 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                  {totalHits} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>(-{totalHits * 4} pts)</span>
                </div>
                <div className="kpi-subtext">No transfer penalties needed</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Bank Balance</div>
                <div className="kpi-value font-mono">
                  £{Number(activeRoadmap[activeGwIndex]?.bank || 0.0).toFixed(1)}m
                </div>
                <div className="kpi-subtext">Available in your bank for upcoming transfers</div>
              </div>
            </div>
          </div>

      {/* Cumulative Projected Points Trajectory Area Chart */}
      <div className="data-table-container">
        <div className="studio-table-controls">
          <div className="controls-left">
            <span className="controls-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ChartLine size={14} weight="bold" />
              Projected Points Growth (Next 5 Weeks)
            </span>
            <span className="controls-count font-mono">Based on planned transfers &amp; fixture difficulty</span>
          </div>
        </div>

        <div className="chart-canvas-container">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trajectoryData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="xpAreaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.35}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <XAxis
                dataKey="gw"
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: 'var(--border-subtle)' }}
              />
              <YAxis
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: 'var(--border-subtle)' }}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-surface-2)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  color: 'var(--text-primary)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                }}
                formatter={(val, name) => [
                  name === 'cumulativeXp' ? `${val} pts (Cumulative)` : `${val} pts (Gameweek)`,
                  name === 'cumulativeXp' ? 'Total Haul' : 'Weekly Target'
                ]}
              />
              <Area
                type="monotone"
                dataKey="cumulativeXp"
                stroke="#10B981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#xpAreaGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 5-Column Gameweek Roadmap Matrix */}
      <div className="multi-gw-matrix-grid">
        {activeRoadmap.map((item, idx) => {
          const isSelected = idx === activeGwIndex;
          const hasTransfers = (item.transfers_in && item.transfers_in.length > 0);

          return (
            <div
              key={item.gw}
              className={`multi-gw-column-card ${isSelected ? 'active-horizon' : ''}`}
              onClick={() => setActiveGwIndex(idx)}
            >
              {/* Gameweek Column Header */}
              <div className="gw-column-header">
                <span className="gw-tag font-mono">GAMEWEEK {item.gw}</span>
                {idx === 0 && <span className="current-badge font-mono">CURRENT</span>}
              </div>

              {/* Weekly Point Projection & Bank */}
              <div className="gw-column-kpi">
                <div className="gw-xp-val font-mono">
                  {Number(item.net_xp || 0).toFixed(1)} <span className="xp-unit">pts</span>
                </div>
                <div className="gw-bank-val font-mono">
                  Bank: £{Number(item.bank || 0.0).toFixed(1)}m
                </div>
              </div>

              {/* Planned Transfer Movements */}
              <div className="gw-transfer-box">
                <div className="box-title">
                  <ArrowsLeftRight size={13} weight="bold" />
                  <span>PLANNED TRANSFERS</span>
                </div>

                {hasTransfers ? (
                  <div className="transfer-moves-list">
                    {item.transfers_in.map((inPlayer, tIdx) => {
                      const outPlayer = item.transfers_out?.[tIdx] || 'Target Out';
                      return (
                        <div key={tIdx} className="transfer-move-item">
                          <div className="move-tag in font-mono">
                            <ArrowUpRight size={11} weight="bold" />
                            <span>BUY: {inPlayer}</span>
                          </div>
                          <div className="move-tag out font-mono">
                            <ArrowDownRight size={11} weight="bold" />
                            <span>SELL: {outPlayer}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="no-transfers-label font-mono">
                    <CheckCircle size={13} weight="fill" color="var(--accent-emerald)" />
                    <span>Save Free Transfer (Bank 1 FT)</span>
                  </div>
                )}
              </div>

              {/* Free Transfers & Hits Status */}
              <div className="gw-footer-meta font-mono">
                <span>Free Transfers: {item.ft_available || 1}</span>
                <span>Hits: {item.hits_taken ? `-${item.hits_taken * 4} pts` : '0 pts'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </>
  )}

  {(viewMode === 'workbench' || viewMode === 'both') && (
    <div style={{ marginTop: viewMode === 'both' ? '32px' : '0' }}>
      <TransferWorkbench
        roadmap={activeRoadmap}
        allPlayers={allPlayers}
        squadPlayers={squadPlayers}
        onInspectPlayer={onInspectPlayer}
        onCompareChange={onCompareChange}
      />
    </div>
  )}
</div>
);
}
