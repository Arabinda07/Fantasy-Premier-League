import React, { useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  ArrowsLeftRight,
  Sparkle,
  TrendUp,
  CalendarCheck,
  Coins,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  PlusCircle,
  ChartLine
} from '@phosphor-icons/react';

export default function MultiGwPlanner({
  roadmap = [],
  squadPlayers = [],
  allPlayers = [],
  onInspectPlayer
}) {
  const [activeGwIndex, setActiveGwIndex] = useState(0);

  // Compute multi-horizon totals & cumulative trajectory
  let runningTotal = 0;
  const trajectoryData = roadmap.map(r => {
    const weeklyXp = Number(r.net_xp || 0);
    runningTotal += weeklyXp;
    return {
      gw: `GW${r.gw}`,
      weeklyXp: Number(weeklyXp.toFixed(1)),
      cumulativeXp: Number(runningTotal.toFixed(1)),
      bank: Number(r.bank || 0.0).toFixed(1),
      hits: r.hits_taken || 0
    };
  });

  const totalHorizonXp = roadmap.reduce((acc, r) => acc + (r.net_xp || 0), 0);
  const totalHits = roadmap.reduce((acc, r) => acc + (r.hits_taken || 0), 0);

  return (
    <div className="view-fluid">
      {/* Hero Header */}
      <div className="studio-hero-panel">
        <div className="studio-hero-header">
          <div className="studio-badge">
            <CalendarCheck size={14} weight="fill" />
            <span>5-WEEK TRANSFER ROADMAP</span>
          </div>
          <span className="studio-version font-mono">HORIZON: GW2 → GW6</span>
        </div>
        <h1 className="studio-title">5-Week Transfer Roadmap & Bank Strategy</h1>
        <p className="studio-description">
          Plan your moves ahead: roll free transfers to build flexibility, avoid unnecessary minus-4 hits, and save cash for the big fixture swings.
        </p>

        {/* Horizon Metric Strip */}
        <div className="kpi-strip" style={{ marginBottom: 0 }}>
          <div className="kpi-card">
            <div className="kpi-label">5-GW Points Target</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
              {totalHorizonXp.toFixed(1)} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
            </div>
            <div className="kpi-subtext">Projected haul across 5 gameweeks</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Transfer Hits Budgeted</div>
            <div className="kpi-value font-mono" style={{ color: totalHits === 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
              {totalHits} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Hits (0 pts lost)</span>
            </div>
            <div className="kpi-subtext">No point deductions needed</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Bank Balance</div>
            <div className="kpi-value font-mono">
              £{Number(roadmap[activeGwIndex]?.bank || 0.0).toFixed(1)}m
            </div>
            <div className="kpi-subtext">Ready for the GW3 Canvot move</div>
          </div>
        </div>
      </div>

      {/* Cumulative Projected Points Trajectory Area Chart */}
      <div className="data-table-container" style={{ marginBottom: '16px' }}>
        <div className="studio-table-controls">
          <div className="controls-left">
            <span className="controls-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ChartLine size={14} weight="bold" />
              Cumulative Points Growth Trajectory
            </span>
            <span className="controls-count font-mono">Multi-Horizon LP Forecast</span>
          </div>
        </div>

        <div style={{ padding: '14px 16px 6px 6px', height: '180px' }}>
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
                  borderRadius: '4px',
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
        {roadmap.map((item, idx) => {
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
                {idx === 0 && <span className="current-badge">CURRENT</span>}
              </div>

              {/* Weekly Point Projection & Bank */}
              <div className="gw-column-kpi">
                <div className="gw-xp-val font-mono">
                  {Number(item.net_xp || 0).toFixed(1)} <span className="xp-unit">xP</span>
                </div>
                <div className="gw-bank-val font-mono">
                  Bank: £{Number(item.bank || 0.0).toFixed(1)}m
                </div>
              </div>

              {/* Planned Transfer Movements */}
              <div className="gw-transfer-box">
                <div className="box-title">
                  <ArrowsLeftRight size={13} weight="bold" />
                  <span>TRANSFER MOVES</span>
                </div>

                {hasTransfers ? (
                  <div className="transfer-moves-list">
                    {item.transfers_in.map((inPlayer, tIdx) => {
                      const outPlayer = item.transfers_out?.[tIdx] || 'Target Out';
                      return (
                        <div key={tIdx} className="transfer-move-item">
                          <div className="move-tag in">
                            <ArrowUpRight size={11} weight="bold" />
                            <span>IN: {inPlayer}</span>
                          </div>
                          <div className="move-tag out">
                            <ArrowDownRight size={11} weight="bold" />
                            <span>OUT: {outPlayer}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="no-transfers-label">
                    <CheckCircle size={13} weight="fill" color="var(--accent-emerald)" />
                    <span>Roll Free Transfer (Bank FT)</span>
                  </div>
                )}
              </div>

              {/* Free Transfers & Hits Status */}
              <div className="gw-footer-meta font-mono">
                <span>FT Available: {item.ft_available || 1}</span>
                <span>Hits: {item.hits_taken ? `-${item.hits_taken * 4} pts` : '0'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
