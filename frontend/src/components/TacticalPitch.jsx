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
  Target,
  Sparkle
} from '@phosphor-icons/react';

export default function TacticalPitch({
  liveData,
  starters = [],
  bench = [],
  allPlayersData = [],
  _allPlayers = [],
  selectedPlayer,
  selectedSwapPlayer,
  setSelectedSwapPlayer,
  onSelectPlayer,
  onSwapPlayers,
  onInspectPlayer,
  onOpenMatchup,
  onOpenFixture,
  actionSummary,
  startingXp = 64.7,
  _totalXp = 64.7,
  strategies = {},
  chipSimulations = {},
  activeChip = 'none',
  onSelectChip = () => {},
  strategy = 'pure_xp',
  onSelectStrategy = () => {}
}) {
  // Extract data from liveData payload if provided
  const effectiveChipSimulations = liveData?.chip_simulations || chipSimulations || {};
  const effectiveStrategies = liveData?.strategies || strategies || {};
  const effectiveActionSummary = liveData?.action_summary || actionSummary;
  const effectiveStartingXp = liveData?.starting_xp != null ? liveData.starting_xp : startingXp;
  const activeSelectedPlayer = selectedSwapPlayer || selectedPlayer;

  const handlePlayerSelect = (p) => {
    if (activeChip !== 'none') {
      if (onInspectPlayer) onInspectPlayer(p);
      return;
    }

    if (onSwapPlayers && activeSelectedPlayer) {
      if ((activeSelectedPlayer.player_code || activeSelectedPlayer.code) !== (p.player_code || p.code)) {
        onSwapPlayers(activeSelectedPlayer, p);
      } else {
        if (setSelectedSwapPlayer) setSelectedSwapPlayer(null);
      }
    } else if (setSelectedSwapPlayer) {
      setSelectedSwapPlayer(activeSelectedPlayer?.player_code === p.player_code ? null : p);
    } else if (onSelectPlayer) {
      onSelectPlayer(p);
    }
  };

  const handleMatchupClick = (details) => {
    if (onOpenFixture) onOpenFixture(details);
    else if (onOpenMatchup) onOpenMatchup(details);
  };

  // Compute Dynamic Chip Simulations
  const resolvedChipData = useMemo(() => {
    const capt = starters.find(p => p.is_captain) || starters[0];
    const captXp = capt ? Number(capt.expected_points || 0) : 0;
    const tripleCaptainXp = effectiveStartingXp + captXp;

    const benchXp = bench.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
    const benchBoostXp = effectiveStartingXp + benchXp;

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
        formation: '15 Active (2-5-5-3)',
        label: `Bench Boost Active (+${benchXp.toFixed(1)} xP from Bench Assets · 15 Scoring)`
      },
    };

    if (effectiveChipSimulations.wildcard) result.wildcard = effectiveChipSimulations.wildcard;
    if (effectiveChipSimulations.freehit) result.freehit = effectiveChipSimulations.freehit;
    if (effectiveChipSimulations.bboost) result.bboost = effectiveChipSimulations.bboost;
    if (effectiveChipSimulations['3xc']) result['3xc'] = effectiveChipSimulations['3xc'];

    return result;
  }, [starters, bench, effectiveStartingXp, effectiveChipSimulations]);

  // Determine active strategy squad if chip is none
  const currentStrategyData = effectiveStrategies && effectiveStrategies[strategy] ? effectiveStrategies[strategy] : null;

  // Determine active display data: Priority: Active Chip > Active Strategy > Base Matchday Squad
  const currentChipData = activeChip !== 'none' ? (effectiveChipSimulations[activeChip] || resolvedChipData[activeChip]) : null;
  const isChipActive = activeChip !== 'none' && currentChipData != null;
  const isBenchBoost = activeChip === 'bboost';

  const displayStarters = isChipActive
    ? (currentChipData.starters || starters)
    : (currentStrategyData ? currentStrategyData.starters : starters);

  const displayBench = isChipActive
    ? (currentChipData.bench || (isBenchBoost ? [] : bench))
    : (currentStrategyData ? currentStrategyData.bench : bench);

  const displayStartingXp = isChipActive
    ? (currentChipData.starting_xp != null ? currentChipData.starting_xp : currentChipData.total_xp)
    : (currentStrategyData ? currentStrategyData.starting_xp : effectiveStartingXp);

  // Group players for pitch rendering
  // For Bench Boost: combine all 15 players onto the pitch in expanded 2-5-5-3 layout
  const allPitchPlayers = useMemo(() => {
    if (!isBenchBoost) return displayStarters;
    if (currentChipData?.starters && currentChipData.starters.length === 15) {
      return currentChipData.starters.map(p => ({
        ...p,
        is_boosted: true
      }));
    }
    return [
      ...displayStarters,
      ...bench.map(p => ({ ...p, is_boosted: true, is_bench_asset: true }))
    ];
  }, [isBenchBoost, currentChipData, displayStarters, bench]);

  const gks = allPitchPlayers.filter(p => p.position === 'GK');
  const defs = allPitchPlayers.filter(p => p.position === 'DEF');
  const mids = allPitchPlayers.filter(p => p.position === 'MID');
  const fwds = allPitchPlayers.filter(p => p.position === 'FWD');

  const formation = isBenchBoost
    ? '15 Active (2-5-5-3)'
    : isChipActive
    ? (currentChipData.formation || `${defs.length}-${mids.length}-${fwds.length}`)
    : (currentStrategyData?.formation || `${defs.length}-${mids.length}-${fwds.length}`);

  // Helper for strategy badges on player cards
  const getStrategyBadge = (p) => {
    if (isChipActive) return null;
    if (strategy === 'differential_chase') {
      const own = Number(p.ownership_pct || (p.eo || 0.1));
      if (own < 0.20) return 'DIFF';
    } else if (strategy === 'rank_protect') {
      const own = Number(p.ownership_pct || (p.eo || 0.5));
      if (own > 0.25 || p.is_captain) return 'SHIELD';
    }
    return null;
  };

  const chipOptions = [
    { id: 'none', label: 'Standard XI', icon: ShieldCheck },
    { id: 'wildcard', label: 'Wildcard', icon: Cards },
    { id: 'freehit', label: 'Free Hit', icon: Lightning },
    { id: 'bboost', label: 'Bench Boost', icon: RocketLaunch },
    { id: '3xc', label: 'Triple Capt', icon: Crown }
  ];

  const strategyOptions = [
    { id: 'pure_xp', label: 'Pure xP', icon: Target, desc: 'Mathematical baseline LP solver' },
    { id: 'rank_protect', label: 'Rank Shield', icon: ShieldCheck, desc: 'Effective Ownership weighting to protect lead' },
    { id: 'differential_chase', label: 'Diff Chase', icon: Lightning, desc: 'Rewards low-EO assets to accelerate rank climb' }
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
      ? (summaryStr.includes('BENCHMARK') ? 'Optimal Starting XI template locked · 0 transfers needed' : 'Optimal 15-man squad locked · 1 Free Transfer saved · 0 hits taken')
      : summaryStr.replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '');

    return (
      <div className="rec-generic-text">
        <span>{cleanMsg}</span>
      </div>
    );
  };

  const boostedBenchList = useMemo(() => {
    return bench.map((p, idx) => ({
      ...p,
      is_boosted: true,
      slotLabel: idx === 0 ? 'GK Sub' : `Sub ${idx}`
    }));
  }, [bench]);

  const benchUpliftTotal = useMemo(() => {
    return bench.reduce((acc, p) => acc + Number(p.expected_points || 0), 0).toFixed(1);
  }, [bench]);

  return (
    <div>
      {/* Streamlined Matchday Control Deck */}
      <div className="matchday-control-deck">
        <div className="deck-group">
          <span className="deck-label font-mono">Scenario</span>
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
                  title={`Switch to ${chip.label} scenario`}
                >
                  <Icon size={13} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{chip.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="deck-group">
          <span className="deck-label font-mono">Strategy</span>
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
                  <Icon size={13} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{opt.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="deck-telemetry">
          <div className="deck-telemetry-item font-mono">
            <span className="telemetry-label">Formation</span>
            <span className="telemetry-value">{formation}</span>
          </div>
          <div className="deck-telemetry-divider" />
          <div className="deck-telemetry-item font-mono">
            <span className="telemetry-label">Projected</span>
            <span className="telemetry-value xp-highlight">{displayStartingXp} <span className="telemetry-unit">xP</span></span>
          </div>
        </div>
      </div>

      {/* Streamlined Contextual Directive Strip */}
      <div className="matchday-directive-strip">
        <div className="directive-tag-box font-mono">
          {isChipActive ? 'SCENARIO' : strategy !== 'pure_xp' ? 'STRATEGY' : 'MATCHDAY'}
        </div>
        <div className="directive-body">
          {isChipActive ? (
            <span className="directive-text chip-active-text">
              {currentChipData.label || currentChipData.description || 'Active Scenario Projection'}
            </span>
          ) : currentStrategyData && strategy !== 'pure_xp' ? (
            <span className="directive-text strategy-active-text">
              {currentStrategyData.label} ({currentStrategyData.subtitle || 'Tactical Optimization Active'}) · Formation {currentStrategyData.formation}
            </span>
          ) : (
            renderTransferPills(effectiveActionSummary)
          )}
        </div>
      </div>

      {/* Classical 2-Column Pitch Workspace (Pitch on Left, Sidebar on Right) */}
      <div className="pitch-workspace">
        {/* Tactical Pitch Surface (Left Column) */}
        <div className={`pitch-container ${isBenchBoost ? 'bench-boost-active-pitch' : ''}`}>
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
                isBoosted={Boolean(p.is_boosted || isBenchBoost)}
                strategyBadge={getStrategyBadge(p)}
                isSubTarget={activeSelectedPlayer?.player_code === p.player_code}
                onSelectSub={handlePlayerSelect}
                onInspect={onInspectPlayer}
                onOpenMatchup={handleMatchupClick}
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
                isBoosted={Boolean(p.is_boosted || isBenchBoost)}
                strategyBadge={getStrategyBadge(p)}
                isSubTarget={activeSelectedPlayer?.player_code === p.player_code}
                onSelectSub={handlePlayerSelect}
                onInspect={onInspectPlayer}
                onOpenMatchup={handleMatchupClick}
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
                isBoosted={Boolean(p.is_boosted || isBenchBoost)}
                strategyBadge={getStrategyBadge(p)}
                isSubTarget={activeSelectedPlayer?.player_code === p.player_code}
                onSelectSub={handlePlayerSelect}
                onInspect={onInspectPlayer}
                onOpenMatchup={handleMatchupClick}
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
                isBoosted={Boolean(p.is_boosted || isBenchBoost)}
                strategyBadge={getStrategyBadge(p)}
                isSubTarget={activeSelectedPlayer?.player_code === p.player_code}
                onSelectSub={handlePlayerSelect}
                onInspect={onInspectPlayer}
                onOpenMatchup={handleMatchupClick}
              />
            ))}
          </div>
        </div>

        {/* Sidebar (Right Column) - Transforms into Bench Boost Telemetry Hub if Bench Boost is active */}
        <div className="pitch-sidebar">
          {isBenchBoost ? (
            <div className="sidebar-panel bench-boost-telemetry-panel">
              <div className="panel-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <RocketLaunch size={16} weight="fill" color="var(--accent-emerald)" />
                  <span className="panel-title" style={{ color: 'var(--accent-emerald)' }}>
                    BENCH BOOST ACTIVE
                  </span>
                </div>
                <span className="panel-badge font-mono" style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
                  15 / 15 Scoring
                </span>
              </div>

              <div className="bench-boost-summary-card" style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', padding: '10px 12px', margin: '8px 0 12px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    Bench Uplift
                  </span>
                  <span className="font-mono" style={{ fontSize: '14px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                    +{benchUpliftTotal} xP
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  All 15 squad members are deployed on the tactical pitch. Both starting XI and all 4 bench assets contribute to your total gameweek score.
                </div>
              </div>

              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
                Activated Bench Assets (4)
              </div>

              <div className="bench-list">
                {boostedBenchList.map((p) => (
                  <div
                    key={p.player_code || p.id || p.web_name}
                    className="bench-item boost-active"
                    onClick={() => onInspectPlayer && onInspectPlayer(p)}
                    onDoubleClick={() => onInspectPlayer && onInspectPlayer(p)}
                    tabIndex={0}
                    role="button"
                    title="Click to view player DNA"
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                      <span className="bench-slot-tag font-mono boost-tag" style={{ background: 'rgba(16, 185, 129, 0.25)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.5)' }}>
                        ACTIVE
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
                        +{Number(p.expected_points || 0).toFixed(1)} pts
                      </div>
                      <div style={{ fontSize: '9.5px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        bench xP
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bench-help-text" style={{ marginTop: '10px' }}>
                All 15 cards are active on the pitch. Double-click any player card to inspect comprehensive Player DNA metrics.
              </div>
            </div>
          ) : (
            <div className="sidebar-panel">
              <div className="panel-header">
                <span className="panel-title">
                  {activeChip === 'wildcard' ? 'WILDCARD BENCH' : activeChip === 'freehit' ? 'FREE HIT BENCH' : activeChip === '3xc' ? 'TRIPLE CAPTAIN BENCH' : 'Substitutes'}
                </span>
                <span className="panel-badge font-mono">
                  {`${displayBench.length} on bench`}
                </span>
              </div>

              <div className="bench-list">
                {displayBench.map((p, idx) => {
                  const isSelected = activeSelectedPlayer?.player_code === p.player_code;
                  const slotLabel = idx === 0 ? 'GK Sub' : `Sub ${idx}`;
                  return (
                    <div
                      key={p.player_code || p.id || p.web_name}
                      className={`bench-item ${isSelected ? 'is-selected' : ''}`}
                      onClick={() => handlePlayerSelect(p)}
                      onDoubleClick={() => onInspectPlayer && onInspectPlayer(p)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handlePlayerSelect(p);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`Bench ${slotLabel}: ${p.web_name}, ${p.position}, £${Number(p.cost || 0).toFixed(1)}M, ${Number(p.expected_points || 0).toFixed(1)} expected points`}
                      title="Click to swap with starter · Double-click for DNA stats"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                        <span className="bench-slot-tag font-mono">
                          {slotLabel}
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
          )}
        </div>
      </div>
    </div>
  );
}

