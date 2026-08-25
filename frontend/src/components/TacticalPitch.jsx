import React from 'react';
import PlayerCard from './PlayerCard';

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
    { id: 'none', label: 'Standard Matchday', icon: '🛡️' },
    { id: 'wildcard', label: 'Wildcard (£100M)', icon: '🃏' },
    { id: 'freehit', label: 'Free Hit', icon: '⚡' },
    { id: 'bboost', label: 'Bench Boost', icon: '🚀' },
    { id: '3xc', label: 'Triple Captain', icon: '👑' },
  ];

  return (
    <div>
      {/* Chip Strategy Simulator Bar */}
      <div style={{ background: 'var(--bg-surface-1)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)', padding: '10px 16px', marginBottom: '14px', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            SIMULATE CHIP:
          </span>
          <div role="group" aria-label="Select active FPL chip simulation" style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {chipOptions.map(c => (
              <button
                key={c.id}
                onClick={() => onSelectChip(c.id)}
                aria-pressed={activeChip === c.id}
                style={{
                  background: activeChip === c.id ? (c.id === 'none' ? 'var(--bg-surface-subtle)' : 'var(--accent-emerald)') : 'var(--bg-surface-2)',
                  color: activeChip === c.id ? (c.id === 'none' ? 'var(--text-primary)' : 'var(--text-inverse)') : 'var(--text-secondary)',
                  border: activeChip === c.id ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <span>{c.icon}</span>
                <span>{c.label}</span>
              </button>
            ))}
          </div>
        </div>

        {isChipActive && (
          <div style={{ fontSize: '12px', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            {currentChipData.chip_name.toUpperCase()} ACTIVE · {currentChipData.formation} · £{currentChipData.budget_used.toFixed(1)}M SPENT
          </div>
        )}
      </div>

      {/* Matchday Action Header / Chip Description */}
      {isChipActive ? (
        <div className="action-banner" style={{ borderColor: 'var(--accent-emerald)' }}>
          <div className="action-text">
            <span className="action-pill" style={{ background: 'var(--accent-emerald)', color: 'var(--text-inverse)' }}>
              {currentChipData.chip_name.toUpperCase()} SCENARIO
            </span>
            <span style={{ fontWeight: 600 }}>{currentChipData.description}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Projected Total: <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>{currentChipData.total_xp.toFixed(2)} xP</span>
          </div>
        </div>
      ) : actionSummary && (
        <div className="action-banner">
          <div className="action-text">
            <span className="action-pill">OPTIMAL MATCHDAY MOVE</span>
            <span style={{ fontWeight: 600 }}>{actionSummary}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            MILP Solver Status: <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>OPTIMAL</span>
          </div>
        </div>
      )}

      {/* KPI Top Strip */}
      <div className="kpi-strip">
        <div className="kpi-card">
          <div className="kpi-label">Starting XI Projected xP</div>
          <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
            {Number(displayStartingXp || 0).toFixed(2)}
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
          </div>
          <div className="kpi-subtext" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <span>Active:</span>
            <span style={{ background: 'var(--bg-surface-subtle)', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '11px', padding: '1px 6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
              FORMATION {formation}
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Squad Total Projected xP</div>
          <div className="kpi-value">
            {Number(displayTotalXp || 0).toFixed(2)}
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>pts</span>
          </div>
          <div className="kpi-subtext">
            {activeChip === 'bboost' ? 'All 15 Players Active (Bench Boost)' : 'Includes Vice-Captain & Auto-Sub'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Active Bank Balance</div>
          <div className="kpi-value">
            £2.0<span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>M</span>
          </div>
          <div className="kpi-subtext">1 Free Transfer Available</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Lookahead Horizon</div>
          <div className="kpi-value">
            3 <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>GWs</span>
          </div>
          <div className="kpi-subtext">Temporal Discount: γ = 0.90</div>
        </div>
      </div>

      {/* Main Pitch Workspace */}
      <div className="pitch-workspace">
        {/* The 2D Tactical Grass Pitch */}
        <div className="pitch-container">
          {/* Pitch Field Markings */}
          <div className="pitch-marking-center-line"></div>
          <div className="pitch-marking-center-circle"></div>
          <div className="pitch-marking-penalty-top"></div>
          <div className="pitch-marking-penalty-bottom"></div>

          {/* Goalkeepers Row */}
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

          {/* Defenders Row */}
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

          {/* Midfielders Row */}
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

          {/* Forwards Row */}
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

        {/* Ordered Bench & Squad Tools Sidebar */}
        <div className="pitch-sidebar">
          <div className="sidebar-panel">
            <div className="panel-header">
              <span>ORDERED BENCH HIERARCHY</span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>4 SLOTS</span>
            </div>

            <div className="bench-list">
              {displayBench.map(p => {
                const isSelected = selectedPlayer?.player_code === p.player_code;
                const slotLabel = p.bench_order === 1 ? 'Slot 1 (GK)' : `Slot ${p.bench_order || 2} (Sub ${(p.bench_order || 2) - 1})`;
                return (
                  <div
                    key={p.player_code}
                    className={`bench-item ${isSelected ? 'is-selected' : ''}`}
                    style={activeChip === 'bboost' ? { borderColor: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.08)' } : {}}
                    onClick={() => onSelectPlayer(p)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectPlayer(p);
                      }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-label={`Bench ${slotLabel}: ${p.web_name}, ${p.position}, cost £${Number(p.cost || 0).toFixed(1)}M, ${Number(p.expected_points || 0).toFixed(2)} expected points`}
                    title="Click to swap with starter · Double-click to inspect"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="bench-slot-tag" style={activeChip === 'bboost' ? { background: 'var(--accent-emerald)', color: 'var(--text-inverse)' } : {}}>
                        {activeChip === 'bboost' ? 'ACTIVE' : slotLabel}
                      </span>
                      <span className={`player-position-pill ${p.position}`}>{p.position}</span>
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {p.web_name}
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {p.team} · £{Number(p.cost || 0).toFixed(1)}M
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                          {Number(p.expected_points || 0).toFixed(2)}
                        </div>
                        <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>xP</div>
                      </div>
                      {onInspectPlayer && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspectPlayer(p);
                          }}
                          aria-label={`Inspect ${p.web_name} DNA`}
                          style={{
                            background: 'var(--bg-surface-subtle)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--accent-emerald)',
                            fontSize: '9px',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            padding: '2px 5px',
                            borderRadius: 'var(--radius-xs)',
                            cursor: 'pointer'
                          }}
                        >
                          DNA
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '14px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              💡 <em>Click any starter and bench player to simulate tactical substitutions. Double-click any player for full 11-component mathematical DNA.</em>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
