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
  onOpenMatchup,
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

    // Humanized fallback for locked initial squad or rolling transfer
    const cleanMsg = summary.includes('LOCKED') || summary.includes('INITIAL')
      ? 'Optimal 15-man squad locked · 1 Free Transfer saved for GW3 · 0 hits taken'
      : summary.replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '');

    return (
      <div className="rec-generic-text">
        <span>{cleanMsg}</span>
      </div>
    );
  };

  return (
    <div>
      {/* Chip Simulation Segmented Switcher (Rule 3) */}
      <div className="chip-switcher-bar">
        <div className="chip-switcher-left">
          <span className="chip-switcher-label">
            Active Scenario:
          </span>
          <div role="group" aria-label="Select active FPL chip" className="segmented-chip-rail">
            {chipOptions.map(c => {
              const Icon = c.icon;
              const isSelected = activeChip === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => onSelectChip(c.id)}
                  aria-pressed={isSelected}
                  className={`segmented-chip-btn ${isSelected ? 'active' : ''}`}
                >
                  <Icon size={13} weight={isSelected ? "fill" : "bold"} />
                  <span>{c.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {isChipActive ? (
          <div className="chip-active-tag font-mono">
            {currentChipData.chip_name} · {currentChipData.formation} · £{currentChipData.budget_used.toFixed(1)}m squad cost
          </div>
        ) : (
          <div className="chip-status-tag font-mono">
            Standard Lineup · 1 FT Saved · £2.0m Bank
          </div>
        )}
      </div>

      {/* Strategic Recommendation Status Bar (Rule 4) */}
      {isChipActive ? (
        <div className="strategy-status-bar chip-active">
          <div className="strategy-status-left">
            <span className="status-tag chip-tag">
              <Lightning size={12} weight="fill" />
              <span>{currentChipData.chip_name.toUpperCase()}</span>
            </span>
            <span className="strategy-desc">{currentChipData.description}</span>
          </div>
          <div className="strategy-status-right">
            <span className="rec-xp-label">Horizon Target:</span>
            <span className="rec-xp-val font-mono">{currentChipData.total_xp.toFixed(1)} pts</span>
          </div>
        </div>
      ) : actionSummary && (
        <div className="strategy-status-bar">
          <div className="strategy-status-left">
            <span className="status-tag optimal-tag">
              <span className="status-dot"></span>
              <span>MATCHDAY STRATEGY</span>
            </span>
            {renderTransferPills(actionSummary)}
          </div>
          <div className="strategy-status-right">
            <span className="rec-xp-label">Horizon:</span>
            <span className="rec-xp-val font-mono">GW2 → GW4</span>
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
          <div className="kpi-label">Squad Total (Bench Weighted)</div>
          <div className="kpi-value">
            {Number(displayTotalXp || 0).toFixed(1)}
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
          </div>
          <div className="kpi-subtext">
            {activeChip === 'bboost' ? 'All 15 players scoring points' : 'Starters + auto-sub safety net'}
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
          <div className="kpi-label">Lookahead Horizon</div>
          <div className="kpi-value">
            3 <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Gameweeks</span>
          </div>
          <div className="kpi-subtext">Planning ahead through GW4</div>
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
                onOpenMatchup={onOpenMatchup}
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
                onOpenMatchup={onOpenMatchup}
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
                onOpenMatchup={onOpenMatchup}
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
                onOpenMatchup={onOpenMatchup}
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
                      {p.ceiling_p90 && (
                        <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          max {p.ceiling_p90}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '14px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Click any starter and bench player to swap. Double-click any card to see full player breakdown.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
