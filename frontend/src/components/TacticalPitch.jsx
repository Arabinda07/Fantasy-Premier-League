import React from 'react';
import PlayerCard from './PlayerCard';
import {
  ShieldCheck,
  Cards,
  Lightning,
  RocketLaunch,
  Crown,
  ArrowsLeftRight,
  ArrowUpRight,
  ArrowDownRight,
  CaretRight
} from '@phosphor-icons/react';

export default function TacticalPitch({
  starters,
  bench,
  selectedPlayer,
  onSelectPlayer,
  onInspectPlayer,
  actionSummary,
  startingXp,
  totalXp,
  chipSimulations = {},
  activeChip = 'none',
  onSelectChip = () => {}
}) {
  // Determine if viewing a chip simulation
  const isChipActive = activeChip !== 'none' && chipSimulations && chipSimulations[activeChip];
  const currentChipData = isChipActive ? chipSimulations[activeChip] : null;

  const displayStarters = isChipActive ? currentChipData.starters : starters;
  const displayBench = isChipActive ? currentChipData.bench : bench;
  const displayStartingXp = isChipActive ? currentChipData.starting_xp : startingXp;
  const displayTotalXp = isChipActive ? currentChipData.total_xp : totalXp;

  // Group starters by position
  const gks = displayStarters.filter(p => p.position === 'GK');
  const defs = displayStarters.filter(p => p.position === 'DEF');
  const mids = displayStarters.filter(p => p.position === 'MID');
  const fwds = displayStarters.filter(p => p.position === 'FWD');

  const formation = isChipActive ? currentChipData.formation : `${defs.length}-${mids.length}-${fwds.length}`;

  const chipOptions = [
    { id: 'none', label: 'Standard XI', icon: ShieldCheck },
    { id: 'wildcard', label: 'Wildcard (£100m)', icon: Cards },
    { id: 'freehit', label: 'Free Hit', icon: Lightning },
    { id: 'bboost', label: 'Bench Boost', icon: RocketLaunch },
    { id: '3xc', label: 'Triple Captain', icon: Crown }
  ];

  // Helper to parse transfer actions into clean icon-driven pills
  const renderTransferPills = (summary) => {
    if (!summary) return null;

    const inMatch = summary.match(/\[IN\]\s*([A-Za-z0-9_.\-\s]+?)(?=\s*\||\s*\[OUT\]|$)/i);
    const outMatch = summary.match(/\[OUT\]\s*([A-Za-z0-9_.\-\s]+?)(?=\s*\||$)/i);

    if (inMatch && outMatch) {
      const inName = inMatch[1].trim();
      const outName = outMatch[1].trim();

      return (
        <div className="rec-transfer-group">
          <div className="rec-transfer-pill in">
            <ArrowUpRight size={13} weight="bold" />
            <span className="rec-tag">IN</span>
            <span className="rec-player-name">{inName}</span>
          </div>
          <CaretRight size={13} className="rec-arrow" />
          <div className="rec-transfer-pill out">
            <ArrowDownRight size={13} weight="bold" />
            <span className="rec-tag">OUT</span>
            <span className="rec-player-name">{outName}</span>
          </div>
        </div>
      );
    }

    return (
      <div className="rec-generic-text">
        <span>{summary.replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '')}</span>
      </div>
    );
  };

  return (
    <div>
      {/* Chip Simulation Toggle Bar */}
      <div style={{ background: 'var(--bg-surface-1)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 16px', marginBottom: '14px', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Simulate Chip:
          </span>
          <div role="group" aria-label="Select active FPL chip" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {chipOptions.map(c => {
              const Icon = c.icon;
              const isSelected = activeChip === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => onSelectChip(c.id)}
                  aria-pressed={isSelected}
                  style={{
                    background: isSelected ? (c.id === 'none' ? 'var(--bg-surface-subtle)' : 'var(--accent-emerald)') : 'var(--bg-surface-2)',
                    color: isSelected ? (c.id === 'none' ? 'var(--text-primary)' : 'var(--text-inverse)') : 'var(--text-secondary)',
                    border: isSelected ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                    boxShadow: isSelected && c.id !== 'none' ? '0 4px 20px rgba(16, 185, 129, 0.25)' : 'none',
                    padding: '6px 11px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                    fontFamily: 'var(--font-sans)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Icon size={14} weight={isSelected ? "fill" : "bold"} />
                  <span>{c.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {isChipActive && (
          <div style={{ fontSize: '12px', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            {currentChipData.chip_name} · {currentChipData.formation} · £{currentChipData.budget_used.toFixed(1)}m squad cost
          </div>
        )}
      </div>

      {/* Gameweek Strategic Recommendation Banner */}
      {isChipActive ? (
        <div className="action-banner chip-active-banner">
          <div className="action-left">
            <span className="action-pill chip-pill">
              <Lightning size={13} weight="fill" />
              <span>{currentChipData.chip_name}</span>
            </span>
            <span className="action-desc">{currentChipData.description}</span>
          </div>
          <div className="action-right">
            <span className="rec-xp-label">Projected:</span>
            <span className="rec-xp-val">{currentChipData.total_xp.toFixed(1)} pts</span>
          </div>
        </div>
      ) : actionSummary && (
        <div className="action-banner">
          <div className="action-left">
            <span className="action-pill transfer-pill">
              <ArrowsLeftRight size={13} weight="bold" />
              <span>1 Free Transfer</span>
            </span>
            {renderTransferPills(actionSummary)}
          </div>
          <div className="action-right">
            <div className="status-indicator">
              <span className="status-dot"></span>
              <span className="status-label">Optimal Lineup</span>
            </div>
          </div>
        </div>
      )}

      {/* Key Numbers Strip */}
      <div className="kpi-strip">
        <div className="kpi-card">
          <div className="kpi-label">Starting XI Projected Points</div>
          <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
            {Number(displayStartingXp || 0).toFixed(1)}
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
          </div>
          <div className="kpi-subtext" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <span>Formation:</span>
            <span style={{ background: 'var(--bg-surface-subtle)', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '11px', padding: '1px 6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
              {formation}
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Full Squad Total</div>
          <div className="kpi-value">
            {Number(displayTotalXp || 0).toFixed(1)}
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
          </div>
          <div className="kpi-subtext">
            {activeChip === 'bboost' ? 'All 15 players scoring points' : 'Starters + auto-sub backup'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Money in the Bank</div>
          <div className="kpi-value">
            £{isChipActive ? (100.0 - currentChipData.budget_used).toFixed(1) : '2.0'}m
          </div>
          {/* Prorated Mini-Gauge */}
          <div style={{ marginTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
              <span>£{Number(isChipActive ? currentChipData.budget_used : 98.0).toFixed(1)}m used</span>
              <span>£100.0m budget</span>
            </div>
            <div style={{ width: '100%', height: '5px', background: 'var(--bg-surface-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(100, ((isChipActive ? currentChipData.budget_used : 98.0) / 100.0) * 100)}%`,
                  height: '100%',
                  background: 'var(--accent-emerald)',
                  borderRadius: '3px',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
          </div>
          <div className="kpi-subtext" style={{ marginTop: '6px' }}>
            {isChipActive ? 'Unlimited free transfers' : '1 free transfer saved'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Planning Horizon</div>
          <div className="kpi-value">
            3 <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Gameweeks</span>
          </div>
          <div className="kpi-subtext">Looking ahead through GW4</div>
        </div>
      </div>

      {/* Main Pitch Workspace */}
      <div className="pitch-workspace">
        {/* 2D Grass Pitch */}
        <div className="pitch-container">
          <div className="pitch-marking-center-line"></div>
          <div className="pitch-marking-center-circle"></div>
          <div className="pitch-marking-penalty-top"></div>
          <div className="pitch-marking-penalty-bottom"></div>

          {/* Goalkeepers */}
          <div className="pitch-row">
            {gks.map(p => (
              <PlayerCard
                key={p.player_code}
                player={p}
                isSelected={selectedPlayer?.player_code === p.player_code}
                onClick={() => onSelectPlayer(p)}
                onInspect={onInspectPlayer}
              />
            ))}
          </div>

          {/* Defenders */}
          <div className="pitch-row">
            {defs.map(p => (
              <PlayerCard
                key={p.player_code}
                player={p}
                isSelected={selectedPlayer?.player_code === p.player_code}
                onClick={() => onSelectPlayer(p)}
                onInspect={onInspectPlayer}
              />
            ))}
          </div>

          {/* Midfielders */}
          <div className="pitch-row">
            {mids.map(p => (
              <PlayerCard
                key={p.player_code}
                player={p}
                isSelected={selectedPlayer?.player_code === p.player_code}
                onClick={() => onSelectPlayer(p)}
                onInspect={onInspectPlayer}
              />
            ))}
          </div>

          {/* Forwards */}
          <div className="pitch-row">
            {fwds.map(p => (
              <PlayerCard
                key={p.player_code}
                player={p}
                isSelected={selectedPlayer?.player_code === p.player_code}
                onClick={() => onSelectPlayer(p)}
                onInspect={onInspectPlayer}
              />
            ))}
          </div>
        </div>

        {/* Substitutes Sidebar */}
        <div className="pitch-sidebar">
          <div className="sidebar-panel">
            <div className="panel-header">
              <span>Substitutes</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>4 on bench</span>
            </div>

            <div className="bench-list">
              {displayBench.map(p => {
                const isSelected = selectedPlayer?.player_code === p.player_code;
                const slotLabel = p.bench_order === 1 ? 'GK Sub' : `Sub ${(p.bench_order || 2) - 1}`;
                return (
                  <div
                    key={p.player_code}
                    className={`bench-item ${isSelected ? 'is-selected' : ''}`}
                    style={activeChip === 'bboost' ? { borderColor: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.08)' } : {}}
                    onClick={() => onSelectPlayer(p)}
                    onDoubleClick={() => onInspectPlayer && onInspectPlayer(p)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectPlayer(p);
                      }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-label={`Bench ${slotLabel}: ${p.web_name}, ${p.position}, £${Number(p.cost || 0).toFixed(1)}M, ${Number(p.expected_points || 0).toFixed(1)} expected points`}
                    title="Click to swap with starter · Double-click for stats"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                      <span className="bench-slot-tag" style={activeChip === 'bboost' ? { background: 'var(--accent-emerald)', color: 'var(--text-inverse)' } : {}}>
                        {activeChip === 'bboost' ? 'Active' : slotLabel}
                      </span>
                      <span className={`player-position-pill ${p.position}`}>{p.position}</span>
                      <div style={{ minWidth: 0, overflow: 'hidden' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                          {p.web_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {p.team} · £{Number(p.cost || 0).toFixed(1)}m
                        </div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        {Number(p.expected_points || 0).toFixed(1)} pts
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '14px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Click any starter and bench player to swap them. Double-click any player to see how their points are calculated.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
