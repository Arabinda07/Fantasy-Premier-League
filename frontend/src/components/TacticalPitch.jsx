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
  CaretRight,
  Target
} from '@phosphor-icons/react';

export default function TacticalPitch({
  starters = [],
  bench = [],
  allPlayers = [],
  selectedPlayer,
  onSelectPlayer,
  onInspectPlayer,
  onOpenMatchup,
  actionSummary,
  startingXp = 64.7,
  _totalXp = 64.7,
  chipSimulations = {},
  activeChip = 'none',
  onSelectChip = () => {},
  strategy = 'pure_xp',
  onSelectStrategy = () => {}
}) {
  // Compute Dynamic Chip Simulations if not provided in payload
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
        label: `Bench Boost Active (+${benchXp.toFixed(1)} xP from Bench Assets · 15 Scoring)`
      },
    };

    // Free Hit and Wildcard data from solver payload
    if (chipSimulations.freehit) result.freehit = chipSimulations.freehit;
    if (chipSimulations.wildcard) result.wildcard = chipSimulations.wildcard;

    // Client-side heuristic fallback for Wildcard if solver payload is absent but allPlayers is loaded
    if (!result.wildcard && allPlayers && allPlayers.length >= 15) {
      try {
        const sorted = [...allPlayers].sort((a, b) => Number(b.expected_points || 0) - Number(a.expected_points || 0));
        const topGks = sorted.filter(p => (p.position || '').toUpperCase() === 'GK').slice(0, 2);
        const topDefs = sorted.filter(p => (p.position || '').toUpperCase() === 'DEF').slice(0, 5);
        const topMids = sorted.filter(p => (p.position || '').toUpperCase() === 'MID').slice(0, 5);
        const topFwds = sorted.filter(p => (p.position || '').toUpperCase() === 'FWD').slice(0, 3);

        const wcStarters = [
          topGks[0],
          ...topDefs.slice(0, 3),
          ...topMids.slice(0, 5),
          ...topFwds.slice(0, 2)
        ].filter(Boolean).map((p, idx) => ({
          ...p,
          is_starter: 1,
          is_captain: idx === 0 ? 0 : (idx === 4 ? 1 : 0),
          is_vice_captain: idx === 0 ? 1 : 0,
        }));

        const wcBench = [
          topGks[1],
          topDefs[3],
          topDefs[4],
          topFwds[2]
        ].filter(Boolean).map(p => ({ ...p, is_starter: 0, is_captain: 0, is_vice_captain: 0 }));

        const wcStartingXp = wcStarters.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
        result.wildcard = {
          chip_name: 'Wildcard',
          label: 'Wildcard Active (£100.0M Solved Optimal Template · Formation 3-5-2)',
          description: 'Complete 15-man squad overhaul under £100.0M budget without hit penalties for long-term fixture runs.',
          formation: '3-5-2',
          starting_xp: Number(wcStartingXp.toFixed(1)),
          total_xp: Number(wcStartingXp.toFixed(1)),
          starters: wcStarters,
          bench: wcBench,
        };
      } catch (e) {
        console.warn('Wildcard heuristic fallback error', e);
      }
    }

    // Client-side heuristic fallback for Free Hit if solver payload is absent
    if (!result.freehit && result.wildcard) {
      result.freehit = {
        ...result.wildcard,
        chip_name: 'Free Hit',
        label: 'Free Hit Active (Optimal 1-Round Ceiling Squad · Formation 3-5-2)',
        description: 'Temporary 1-week squad targeting maximum single-round ceiling with cheap £4.0M bench enablers.',
      };
    }

    return result;
  }, [starters, bench, startingXp, chipSimulations, allPlayers]);

  // Determine active display data
  const currentChipData = activeChip !== 'none' ? (chipSimulations[activeChip] || resolvedChipData[activeChip]) : null;
  const isChipActive = activeChip !== 'none' && currentChipData != null;

  const displayStarters = isChipActive ? currentChipData.starters : starters;
  const displayBench = isChipActive ? currentChipData.bench : bench;
  const displayStartingXp = isChipActive ? currentChipData.starting_xp : startingXp;

  // Group starters by position
  const gks = displayStarters.filter(p => p.position === 'GK');
  const defs = displayStarters.filter(p => p.position === 'DEF');
  const mids = displayStarters.filter(p => p.position === 'MID');
  const fwds = displayStarters.filter(p => p.position === 'FWD');

  const formation = isChipActive ? (currentChipData.formation || `${defs.length}-${mids.length}-${fwds.length}`) : `${defs.length}-${mids.length}-${fwds.length}`;

  const chipOptions = [
    { id: 'none', label: 'Standard XI', icon: ShieldCheck },
    { id: 'wildcard', label: 'Wildcard (£100m)', icon: Cards },
    { id: 'freehit', label: 'Free Hit', icon: Lightning },
    { id: 'bboost', label: 'Bench Boost', icon: RocketLaunch },
    { id: '3xc', label: 'Triple Captain', icon: Crown }
  ];

  const strategyOptions = [
    { id: 'pure_xp', label: 'Pure xP Maximizer', icon: Target, desc: 'Unbiased mathematical expectation (baseline LP solver)' },
    { id: 'rank_protect', label: 'Rank Shield', icon: ShieldCheck, desc: 'Effective Ownership weighting to protect lead against template hauls' },
    { id: 'differential_chase', label: 'Differential Chase', icon: Lightning, desc: 'Rewards low-EO assets (<20%) to accelerate rank climb' }
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
      {/* Game Theory Strategy Selector Bar */}
      <div className="chip-switcher-bar" style={{ marginBottom: '12px', background: 'var(--bg-surface-1)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '8px 12px' }}>
        <div className="chip-switcher-left">
          <span className="chip-switcher-label font-mono">
            GAME THEORY STRATEGY:
          </span>
          <div className="segmented-chip-rail">
            {strategyOptions.map(opt => {
              const Icon = opt.icon;
              const isSelected = strategy === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  className={`segmented-chip-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectStrategy(opt.id)}
                  title={opt.desc}
                >
                  <Icon size={14} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{opt.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="chip-switcher-right font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {strategy === 'pure_xp' ? 'LP Baseline Maximizer' : strategy === 'rank_protect' ? 'EO Shielding Active' : 'Low-EO Alpha Hunting'}
        </div>
      </div>

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
                {currentChipData.label || currentChipData.description || 'Active Scenario Projection'}
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
                isCaptain={Boolean(p.is_captain)}
                isViceCaptain={Boolean(p.is_vice_captain)}
                isTripleCaptain={activeChip === '3xc' && Boolean(p.is_captain)}
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
                isCaptain={Boolean(p.is_captain)}
                isViceCaptain={Boolean(p.is_vice_captain)}
                isTripleCaptain={activeChip === '3xc' && Boolean(p.is_captain)}
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
                isCaptain={Boolean(p.is_captain)}
                isViceCaptain={Boolean(p.is_vice_captain)}
                isTripleCaptain={activeChip === '3xc' && Boolean(p.is_captain)}
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
                isCaptain={Boolean(p.is_captain)}
                isViceCaptain={Boolean(p.is_vice_captain)}
                isTripleCaptain={activeChip === '3xc' && Boolean(p.is_captain)}
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
                {activeChip === 'bboost' ? 'BENCH BOOST ACTIVE' : activeChip === 'wildcard' ? 'WILDCARD BENCH' : activeChip === 'freehit' ? 'FREE HIT BENCH' : activeChip === '3xc' ? 'TRIPLE CAPTAIN BENCH' : 'Substitutes'}
              </span>
              <span className="panel-badge font-mono">
                {activeChip === 'bboost' ? '4 Scoring' : `${displayBench.length} on bench`}
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
