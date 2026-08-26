import React, { useMemo } from 'react';
import PlayerCard from './PlayerCard';
import {
  ShieldCheck,
  Cards,
  Lightning,
  RocketLaunch,
  Crown,
  ArrowUpRight,
  ArrowDownRight,
  CaretRight
} from '@phosphor-icons/react';

export default function TacticalPitch({
  starters = [],
  bench = [],
  selectedPlayer,
  onSelectPlayer,
  onInspectPlayer,
  onOpenMatchup,
  actionSummary,
  startingXp = 64.7,
  totalXp = 64.7,
  chipSimulations = {},
  activeChip = 'none',
  onSelectChip = () => {}
}) {
  // Compute Dynamic Chip Simulations if not provided in payload
  // Compute Dynamic Chip Simulations for TC and BB only.
  // Free Hit and Wildcard require solver output — consumed from chipSimulations prop.
  const resolvedChipData = useMemo(() => {
    // 1. Triple Captain Simulation
    const capt = starters.find(p => p.is_captain);
    const captXp = capt ? Number(capt.expected_points || 0) : 0;
    const tripleCaptainXp = startingXp + captXp; // Adds another 1x captain points

    // 2. Bench Boost Simulation
    const benchXp = bench.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
    const benchBoostXp = startingXp + benchXp;

    const result = {
      '3xc': {
        starters: starters,
        bench: bench,
        starting_xp: Number(tripleCaptainXp.toFixed(1)),
        total_xp: Number(tripleCaptainXp.toFixed(1)),
        formation: `${starters.filter(p => p.position === 'DEF').length}-${starters.filter(p => p.position === 'MID').length}-${starters.filter(p => p.position === 'FWD').length}`,
        label: `Triple Captain Active (${capt?.web_name || 'Captain'} 3x Points)`
      },
      'bboost': {
        starters: starters,
        bench: bench.map(p => ({ ...p, is_boosted: true })),
        starting_xp: Number(benchBoostXp.toFixed(1)),
        total_xp: Number(benchBoostXp.toFixed(1)),
        formation: `${starters.filter(p => p.position === 'DEF').length}-${starters.filter(p => p.position === 'MID').length}-${starters.filter(p => p.position === 'FWD').length}`,
        label: `Bench Boost Active (+${benchXp.toFixed(1)} xP from Bench Assets)`
      },
    };

    // F-11 fix: Free Hit and Wildcard data comes from solver payload (chipSimulations prop),
    // NOT from hardcoded player lists. Only include if provided externally.
    if (chipSimulations.freehit) result.freehit = chipSimulations.freehit;
    if (chipSimulations.wildcard) result.wildcard = chipSimulations.wildcard;

    return result;
  }, [starters, bench, startingXp, chipSimulations]);

  // Determine active display data
  const currentChipData = activeChip !== 'none' ? (chipSimulations[activeChip] || resolvedChipData[activeChip]) : null;
  const isChipActive = activeChip !== 'none' && currentChipData != null;

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
    const summaryStr = typeof summary === 'string' ? summary : (summary.headline || summary.action || '');
    if (!summaryStr) return null;

    const inMatch = summaryStr.match(/\[IN\]\s*([A-Za-z0-9_.\-\s]+?)(?=\s*\||\s*\[OUT\]|$)/i);
    const outMatch = summaryStr.match(/\[OUT\]\s*([A-Za-z0-9_.\-\s]+?)(?=\s*\||$)/i);

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

    const cleanMsg = summaryStr.includes('LOCKED') || summaryStr.includes('INITIAL') || summaryStr.includes('BENCHMARK')
      ? (summaryStr.includes('BENCHMARK') ? 'Unconstrained 3-5-2 Optimal Benchmark Template' : 'Optimal 15-man squad locked · 1 Free Transfer saved · 0 hits taken')
      : summaryStr.replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '');

    return (
      <div className="rec-generic-text">
        <span>{cleanMsg}</span>
      </div>
    );
  };

  return (
    <div>
      {/* Chip Simulation Segmented Switcher */}
      <div className="chip-switcher-bar">
        <div className="chip-switcher-left">
          <span className="chip-switcher-label font-mono">
            ACTIVE SCENARIO:
          </span>
          <div className="segmented-chip-rail">
            {chipOptions.map(chip => {
              const Icon = chip.icon;
              const isSelected = activeChip === chip.id;
              return (
                <button
                  key={chip.id}
                  type="button"
                  className={`segmented-chip-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectChip(chip.id)}
                  title={`Switch to ${chip.label} projection scenario`}
                >
                  <Icon size={14} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{chip.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Formation & Scenario Target Score */}
        <div className="chip-switcher-right">
          <span className="formation-badge font-mono">
            FORMATION: {formation}
          </span>
          <span className="font-mono" style={{ fontSize: '13px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            {displayStartingXp} <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>xP Target</span>
          </span>
        </div>
      </div>

      {/* Integrated Strategy Status Bar */}
      <div className="strategy-status-bar">
        <div className="status-bar-inner">
          <div className="status-indicator-dot" />
          <span className="status-bar-title font-mono">
            {isChipActive ? 'ACTIVE SCENARIO:' : 'MATCHDAY DIRECTIVE:'}
          </span>
          <div className="status-bar-content">
            {isChipActive ? (
              <span className="rec-generic-text" style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
                {currentChipData.label}
              </span>
            ) : (
              renderTransferPills(actionSummary)
            )}
          </div>
        </div>
      </div>

      {/* Classical 2-Column Pitch Workspace (Pitch on Left, Substitutes Sidebar on Right) */}
      <div className="pitch-workspace">
        {/* Tactical Pitch Surface (Left Column) */}
        <div className="pitch-container">
          <div className="pitch-marking-center-line" />
          <div className="pitch-marking-center-circle" />
          <div className="pitch-marking-penalty-top" />
          <div className="pitch-marking-penalty-bottom" />

          {/* Row 1: Goalkeepers */}
          <div className="pitch-row">
            {gks.map(p => (
              <PlayerCard
                key={p.player_code || p.id || p.web_name}
                player={p}
                isCaptain={p.is_captain}
                isViceCaptain={p.is_vice_captain}
                isTripleCaptain={activeChip === '3xc' && p.is_captain}
                isBoosted={activeChip === 'bboost'}
                isSubTarget={selectedPlayer?.player_code === p.player_code}
                onSelectSub={onSelectPlayer}
                onInspect={onInspectPlayer}
                onOpenMatchup={onOpenMatchup}
              />
            ))}
          </div>

          {/* Row 2: Defenders */}
          <div className="pitch-row">
            {defs.map(p => (
              <PlayerCard
                key={p.player_code || p.id || p.web_name}
                player={p}
                isCaptain={p.is_captain}
                isViceCaptain={p.is_vice_captain}
                isTripleCaptain={activeChip === '3xc' && p.is_captain}
                isBoosted={activeChip === 'bboost'}
                isSubTarget={selectedPlayer?.player_code === p.player_code}
                onSelectSub={onSelectPlayer}
                onInspect={onInspectPlayer}
                onOpenMatchup={onOpenMatchup}
              />
            ))}
          </div>

          {/* Row 3: Midfielders */}
          <div className="pitch-row">
            {mids.map(p => (
              <PlayerCard
                key={p.player_code || p.id || p.web_name}
                player={p}
                isCaptain={p.is_captain}
                isViceCaptain={p.is_vice_captain}
                isTripleCaptain={activeChip === '3xc' && p.is_captain}
                isBoosted={activeChip === 'bboost'}
                isSubTarget={selectedPlayer?.player_code === p.player_code}
                onSelectSub={onSelectPlayer}
                onInspect={onInspectPlayer}
                onOpenMatchup={onOpenMatchup}
              />
            ))}
          </div>

          {/* Row 4: Forwards */}
          <div className="pitch-row">
            {fwds.map(p => (
              <PlayerCard
                key={p.player_code || p.id || p.web_name}
                player={p}
                isCaptain={p.is_captain}
                isViceCaptain={p.is_vice_captain}
                isTripleCaptain={activeChip === '3xc' && p.is_captain}
                isBoosted={activeChip === 'bboost'}
                isSubTarget={selectedPlayer?.player_code === p.player_code}
                onSelectSub={onSelectPlayer}
                onInspect={onInspectPlayer}
                onOpenMatchup={onOpenMatchup}
              />
            ))}
          </div>
        </div>

        {/* Substitutes Sidebar (Right Column) */}
        <div className="pitch-sidebar">
          <div className="sidebar-panel">
            <div className="panel-header">
              <span className="panel-title">
                {activeChip === 'bboost' ? 'BENCH BOOST ACTIVE' : 'Substitutes'}
              </span>
              <span className="panel-badge font-mono">
                {activeChip === 'bboost' ? '4 Scoring' : '4 on bench'}
              </span>
            </div>

            <div className="bench-list">
              {displayBench.map((p, idx) => {
                const isSelected = selectedPlayer?.player_code === p.player_code;
                const slotLabel = idx === 0 ? 'GK Sub' : `Sub ${idx}`;
                return (
                  <div
                    key={p.player_code || p.id || p.web_name}
                    className={`bench-item ${isSelected ? 'is-selected' : ''} ${activeChip === 'bboost' ? 'boost-active' : ''}`}
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
                    title="Click to swap with starter · Double-click for DNA stats"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                      <span className={`bench-slot-tag font-mono ${activeChip === 'bboost' ? 'boost-tag' : ''}`}>
                        {activeChip === 'bboost' ? 'ACTIVE' : slotLabel}
                      </span>
                      <span className={`player-pos-tag ${p.position}`}>{p.position}</span>
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
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                        {Number(p.expected_points || 0).toFixed(1)} pts
                      </div>
                      <div style={{ fontSize: '9.5px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        exp xP
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="bench-help-text">
              Click any starter and bench player to swap. Double-click any player card to view full Player DNA breakdown.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
