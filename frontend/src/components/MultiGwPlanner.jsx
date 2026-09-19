import React, { useState, useMemo, useRef, useEffect } from 'react';
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
  Scales,
  Info
} from '@phosphor-icons/react';
import TransferWorkbench from './TransferWorkbench';

const DEFAULT_5GW_ROADMAP = [
  { gw: 2, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 64.72, bank: 0.0, ft_available: 1 },
  { gw: 3, transfers_in: ['Canvot'], transfers_out: ['Ballard'], hits_taken: 0, net_xp: 62.16, bank: 0.0, ft_available: 2 },
  { gw: 4, transfers_in: ['Rashford'], transfers_out: ['Mbeumo'], hits_taken: 0, net_xp: 54.47, bank: 1.6, ft_available: 0 },
  { gw: 5, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 63.35, bank: 0.0, ft_available: 2 },
  { gw: 6, transfers_in: [], transfers_out: [], hits_taken: 0, net_xp: 62.65, bank: 0.0, ft_available: 1 }
];

export default function MultiGwPlanner({
  roadmap = [],
  squadPlayers = [],
  allPlayers = [],
  allPlayersData = [],
  fixturesData,
  liveData,
  activeChip,
  onSelectChip,
  onInspectPlayer,
  onCompareChange,
  onOpenFixture,
}) {
  const activeRoadmap = (roadmap && roadmap.length > 0)
    ? roadmap
    : (liveData?.multi_horizon_roadmap && liveData.multi_horizon_roadmap.length > 0)
      ? liveData.multi_horizon_roadmap
      : (liveData?.multi_horizon_plan && liveData.multi_horizon_plan.length > 0)
        ? liveData.multi_horizon_plan
        : (liveData?.transfer_roadmap && liveData.transfer_roadmap.length > 0)
          ? liveData.transfer_roadmap
          : DEFAULT_5GW_ROADMAP;

  const activeAllPlayers = (allPlayers && allPlayers.length > 0)
    ? allPlayers
    : (allPlayersData && allPlayersData.length > 0)
      ? allPlayersData
      : (liveData?.players || []);

  const activeSquadPlayers = (squadPlayers && squadPlayers.length > 0)
    ? squadPlayers
    : (liveData?.starters || liveData?.bench)
      ? [...(liveData?.starters || []), ...(liveData?.bench || [])]
      : [];

  const startGw = activeRoadmap[0]?.gw || 2;
  const endGw = activeRoadmap[activeRoadmap.length - 1]?.gw || (startGw + Math.max(0, activeRoadmap.length - 1));

  const [activeGwIndex, setActiveGwIndex] = useState(0);
  const [selectedTransferPair, setSelectedTransferPair] = useState(null);
  const [viewMode, setViewMode] = useState('both'); // 'both' | 'roadmap' | 'workbench'
  const [showChart, setShowChart] = useState(true);

  // Sync active index if roadmap length changes
  useEffect(() => {
    if (activeGwIndex >= activeRoadmap.length) {
      setActiveGwIndex(0);
    }
  }, [activeRoadmap, activeGwIndex]);
  const [showNotes, setShowNotes] = useState(false);
  const notesRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (notesRef.current && !notesRef.current.contains(event.target)) {
        setShowNotes(false);
      }
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setShowNotes(false);
      }
    }
    if (showNotes) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showNotes]);

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
      {/* Multi-Horizon Planner Control Deck */}
      <div className="planner-control-deck" role="region" aria-label="Transfer Planner Workspace Controls">
        <div className="planner-control-left">
          <div className="planner-horizon-badge font-mono">
            <CalendarCheck size={14} weight="fill" />
            <span>GW{startGw}–GW{endGw} HORIZON</span>
          </div>

          <div className="planner-segmented-rail" role="tablist" aria-label="Transfer Workspace Views">
            <button
              type="button"
              className={`planner-rail-btn ${viewMode === 'roadmap' ? 'active' : ''}`}
              onClick={() => setViewMode('roadmap')}
              aria-pressed={viewMode === 'roadmap'}
            >
              <CalendarCheck size={13} weight={viewMode === 'roadmap' ? 'fill' : 'bold'} />
              <span>5-Week Roadmap</span>
            </button>
            <button
              type="button"
              className={`planner-rail-btn ${viewMode === 'workbench' ? 'active' : ''}`}
              onClick={() => setViewMode('workbench')}
              aria-pressed={viewMode === 'workbench'}
            >
              <Scales size={13} weight={viewMode === 'workbench' ? 'fill' : 'bold'} />
              <span>Transfer Scout</span>
            </button>
            <button
              type="button"
              className={`planner-rail-btn ${viewMode === 'both' ? 'active' : ''}`}
              onClick={() => setViewMode('both')}
              aria-pressed={viewMode === 'both'}
            >
              <ArrowsLeftRight size={13} weight={viewMode === 'both' ? 'fill' : 'bold'} />
              <span>Unified Canvas</span>
            </button>
          </div>
        </div>

        <div className="planner-control-right">
          {/* 5-GW Target Projection */}
          <div
            className="telemetry-chip chip-target"
            title={`Projected ${totalHorizonXp.toFixed(1)} pts across ${activeRoadmap.length} gameweeks (~${(totalHorizonXp / Math.max(1, activeRoadmap.length)).toFixed(1)} pts/GW)`}
          >
            <ChartLine size={14} weight="bold" className="telemetry-chip-icon" />
            <span className="telemetry-chip-label">Target:</span>
            <span className="telemetry-chip-val font-mono">{totalHorizonXp.toFixed(1)} pts</span>
            <span className="telemetry-chip-meta font-mono">~{(totalHorizonXp / Math.max(1, activeRoadmap.length)).toFixed(1)}/GW</span>
          </div>

          {/* Point Hits Strategy */}
          <div
            className="telemetry-chip chip-hits"
            title={totalHits === 0 ? 'Optimal: 0 transfer penalties planned' : `${totalHits} transfer hit planned (-${totalHits * 4} pts)`}
          >
            <span className="telemetry-chip-label">Hits:</span>
            <span className="telemetry-chip-val font-mono" style={{ color: totalHits === 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
              {totalHits === 0 ? '0 Hits' : `-${totalHits * 4} pts`}
            </span>
          </div>

          {/* Bank & Free Transfers */}
          <div className="telemetry-chip chip-bank" title="Available in bank for upcoming transfers">
            <span className="telemetry-chip-label">Bank:</span>
            <span className="telemetry-chip-val font-mono">£{Number(activeRoadmap[activeGwIndex]?.bank || 0.0).toFixed(1)}m</span>
            <span className="telemetry-chip-meta font-mono">{activeRoadmap[0]?.ft_available != null ? activeRoadmap[0].ft_available : 0} FT</span>
          </div>

          {/* On-Demand Planner Notes Popover */}
          <div className="telemetry-notes-group" ref={notesRef}>
            <button
              type="button"
              className={`telemetry-notes-btn font-mono ${showNotes ? 'active' : ''}`}
              onClick={() => setShowNotes(prev => !prev)}
              title="Click to view transfer strategy notes"
              aria-expanded={showNotes}
            >
              <Info size={13} weight="bold" />
              <span>Notes</span>
            </button>
            {showNotes && (
              <div className="telemetry-popover-card font-mono" role="tooltip">
                <h3 className="telemetry-popover-title">
                  Multi-Horizon Transfer Strategy &amp; Rules
                </h3>
                <div className="telemetry-popover-body">
                  <p><strong>Free Transfers:</strong> Accumulate up to 5 FTs. Rolling a transfer allows double-moves without taking a -4 point penalty.</p>
                  <p><strong>Point Hits:</strong> Each additional transfer beyond available FTs deducts 4 points from your gameweek score.</p>
                  <p><strong>Trajectory Chart:</strong> Plots expected cumulative points based on planned buy/sell tactical moves and fixture difficulty ratings.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {(viewMode === 'roadmap' || viewMode === 'both') && (
        <>
          {/* Cumulative Projected Points Trajectory Area Chart */}
          <div className="data-table-container">
            <div className="studio-table-controls">
              <div className="controls-left">
                <span className="controls-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ChartLine size={14} weight="bold" />
                  <span>Projected Points Growth ({activeRoadmap.length} Weeks)</span>
                </span>
                <span className="controls-count font-mono">Based on planned transfers &amp; fixture difficulty</span>
              </div>
              <div className="controls-right">
                <button
                  type="button"
                  className="table-action-btn font-mono"
                  onClick={() => setShowChart(prev => !prev)}
                  title={showChart ? "Collapse trajectory chart" : "Expand trajectory chart"}
                >
                  {showChart ? 'Hide Chart' : 'Show Chart'}
                </button>
              </div>
            </div>

            {showChart && (
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
            )}
          </div>

      {/* 5-Column Gameweek Strategic Horizon Stepper */}
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
                <div className="gw-header-left">
                  <span className="gw-tag pill-base pill-sm font-mono">GW{item.gw}</span>
                  {idx === 0 && <span className="current-badge pill-base pill-xs font-mono">CURRENT</span>}
                </div>
                <span className="gw-ft-badge font-mono" title={`${item.ft_available != null ? item.ft_available : (idx === 0 ? 0 : 1)} Free Transfers available`}>
                  {item.ft_available != null ? item.ft_available : (idx === 0 ? 0 : 1)} FT
                </span>
              </div>

              {/* Weekly Point Projection & Bank */}
              <div className="gw-column-kpi">
                <div className="gw-xp-group">
                  <span className="gw-kpi-label">EXPECTED</span>
                  <div className="gw-xp-val font-mono">
                    {Number(item.net_xp || 0).toFixed(1)} <span className="xp-unit">xP</span>
                  </div>
                </div>
                <div className="gw-bank-group font-mono">
                  <span className="gw-kpi-label">BANK</span>
                  <span className="gw-bank-val">£{Number(item.bank || 0.0).toFixed(1)}m</span>
                </div>
              </div>

              {/* Planned Transfer Movements */}
              <div className="gw-transfer-box">
                <div className="box-title font-mono">
                  <ArrowsLeftRight size={12} weight="bold" />
                  <span>TACTICAL MOVES</span>
                </div>

                {hasTransfers ? (
                  <div className="transfer-moves-list">
                    {item.transfers_in.map((inPlayer, tIdx) => {
                      const outPlayer = item.transfers_out?.[tIdx] || 'Target Out';
                      return (
                        <div
                          key={tIdx}
                          className="transfer-move-item interactive-move-item"
                          role="button"
                          tabIndex={0}
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveGwIndex(idx);
                            setSelectedTransferPair({ inName: inPlayer, outName: outPlayer, timestamp: Date.now() });
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.stopPropagation();
                              setActiveGwIndex(idx);
                              setSelectedTransferPair({ inName: inPlayer, outName: outPlayer, timestamp: Date.now() });
                            }
                          }}
                          title={`Load ${outPlayer} ➔ ${inPlayer} into comparison workbench`}
                        >
                          <div className="move-tag in font-mono">
                            <ArrowUpRight size={12} weight="bold" />
                            <span>BUY: {inPlayer}</span>
                          </div>
                          <div className="move-tag out font-mono">
                            <ArrowDownRight size={12} weight="bold" />
                            <span>SELL: {outPlayer}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="no-transfers-label font-mono">
                    <CheckCircle size={13} weight="fill" color="var(--accent-emerald)" />
                    <span>Roll Free Transfer (+1 FT)</span>
                  </div>
                )}
              </div>

              {/* Free Transfers & Hits Status Footer */}
              <div className="gw-footer-meta font-mono">
                <span className="gw-meta-hits" style={{ color: item.hits_taken ? 'var(--accent-crimson)' : 'var(--text-muted)' }}>
                  Hits: {item.hits_taken ? `-${item.hits_taken * 4} pts` : '0 pts'}
                </span>
                <span className="gw-horizon-status" style={{ color: isSelected ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                  {isSelected ? '● ACTIVE TARGET' : 'CLICK TO VIEW'}
                </span>
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
        allPlayers={activeAllPlayers}
        squadPlayers={activeSquadPlayers}
        activeGwItem={activeRoadmap[activeGwIndex]}
        activeGwIndex={activeGwIndex}
        selectedTransferPair={selectedTransferPair}
        onInspectPlayer={onInspectPlayer}
        onCompareChange={onCompareChange}
      />
    </div>
  )}
</div>
);
}
