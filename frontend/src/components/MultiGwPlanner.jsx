import React, { useState } from 'react';
import {
  ArrowsLeftRight,
  Sparkle,
  TrendUp,
  CalendarCheck,
  Coins,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  PlusCircle
} from '@phosphor-icons/react';

export default function MultiGwPlanner({
  roadmap = [],
  squadPlayers = [],
  allPlayers = [],
  onInspectPlayer
}) {
  const [activeGwIndex, setActiveGwIndex] = useState(0);

  // Compute multi-horizon totals
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
                  <div className="transfer-list">
                    {item.transfers_in.map((inPlayer, tIdx) => {
                      const outPlayer = item.transfers_out[tIdx] || 'Player';
                      return (
                        <div key={inPlayer} className="transfer-action-row">
                          <div className="rec-transfer-pill in">
                            <ArrowUpRight size={12} weight="bold" />
                            <span className="rec-tag">IN</span>
                            <span className="rec-player-name">{inPlayer}</span>
                          </div>
                          <div className="rec-transfer-pill out" style={{ marginTop: '4px' }}>
                            <ArrowDownRight size={12} weight="bold" />
                            <span className="rec-tag">OUT</span>
                            <span className="rec-player-name">{outPlayer}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="no-transfers-msg">
                    <CheckCircle size={14} weight="fill" color="var(--accent-emerald)" />
                    <span>Roll Free Transfer (Bank +1 FT)</span>
                  </div>
                )}
              </div>

              {/* Strategic Horizon Annotation */}
              <div className="gw-rationale-note">
                {item.gw === 2 && "Lock the 15-man squad. Roll the free transfer into GW3."}
                {item.gw === 3 && "Target Palace's home fixture: Ballard → Canvot (£5.0m)."}
                {item.gw === 4 && "Roll the transfer. Bank 2 FTs ahead of Chelsea & Spurs fixture swings."}
                {item.gw === 5 && "Hold the core premiums (Haaland, Fernandes)."}
                {item.gw === 6 && "Use 2 banked FTs for a double move before the international break."}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
