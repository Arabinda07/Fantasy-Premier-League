import React, { useState, useMemo } from 'react';
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
  Sparkle,
  HouseLine,
  CornersOut,
  TrendUp,
  CaretDown,
  CaretUp,
  UsersThree,
  CheckCircle,
  WarningCircle,
  XCircle
} from '@phosphor-icons/react';
import { CAPTAINCY_DECISION_BRIEF, STRUCTURAL_BUILDS } from '../constants/copyTokens';
import { solveStructuralSquad } from '../utils/clientOptimizer';

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
  const [isBriefExpanded, setIsBriefExpanded] = useState(true);
  const [squadBuild, setSquadBuild] = useState('spread'); // 'spread' (Big in the Middle) | 'anchor' (Mega-Forward Anchor)

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

  // Structural Squad Preset Solver (Spread vs Anchor)
  const structuralBuildData = useMemo(() => {
    if (liveData?.structural_builds && liveData.structural_builds[squadBuild]) {
      return liveData.structural_builds[squadBuild];
    }
    return solveStructuralSquad(allPlayersData, starters.length ? [...starters, ...bench] : [], squadBuild, 100.0);
  }, [liveData, allPlayersData, starters, bench, squadBuild]);

  // Compute Dynamic Chip Simulations
  const resolvedChipData = useMemo(() => {
    const activeBaseStarters = structuralBuildData?.starters || starters;
    const activeBaseBench = structuralBuildData?.bench || bench;
    const capt = activeBaseStarters.find(p => p.is_captain) || activeBaseStarters[0];
    const captXp = capt ? Number(capt.expected_points || 0) : 0;
    const baseStartingXp = structuralBuildData?.starting_xp || effectiveStartingXp;
    const tripleCaptainXp = baseStartingXp + captXp;

    const benchXp = activeBaseBench.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
    const benchBoostXp = baseStartingXp + benchXp;

    const result = {
      '3xc': {
        starters: activeBaseStarters,
        bench: activeBaseBench,
        starting_xp: Number(tripleCaptainXp.toFixed(1)),
        total_xp: Number(tripleCaptainXp.toFixed(1)),
        formation: `${activeBaseStarters.filter(p => p.position === 'DEF').length}-${activeBaseStarters.filter(p => p.position === 'MID').length}-${activeBaseStarters.filter(p => p.position === 'FWD').length}`,
        label: `Triple Captain Active · 3x points on ${capt?.web_name || 'Captain'}`
      },
      'bboost': {
        starters: activeBaseStarters,
        bench: activeBaseBench.map(p => ({ ...p, is_boosted: true })),
        starting_xp: Number(benchBoostXp.toFixed(1)),
        total_xp: Number(benchBoostXp.toFixed(1)),
        formation: '15 Active (2-5-5-3)',
        label: `Bench Boost Active · All 15 players scoring (+${benchXp.toFixed(1)} pts from bench)`
      },
    };

    if (effectiveChipSimulations.wildcard) result.wildcard = effectiveChipSimulations.wildcard;
    if (effectiveChipSimulations.freehit) result.freehit = effectiveChipSimulations.freehit;
    if (effectiveChipSimulations.bboost) result.bboost = effectiveChipSimulations.bboost;
    if (effectiveChipSimulations['3xc']) result['3xc'] = effectiveChipSimulations['3xc'];

    return result;
  }, [starters, bench, effectiveStartingXp, structuralBuildData, effectiveChipSimulations]);

  // Determine active strategy squad if chip is none
  const currentStrategyData = effectiveStrategies && effectiveStrategies[strategy] ? effectiveStrategies[strategy] : null;

  // Determine active display data: Priority: Active Chip > Active Strategy (if not pure_xp) > Structural Build > Base Squad
  const currentChipData = activeChip !== 'none' ? (effectiveChipSimulations[activeChip] || resolvedChipData[activeChip]) : null;
  const isChipActive = activeChip !== 'none' && currentChipData != null;
  const isBenchBoost = activeChip === 'bboost';

  const displayStarters = isChipActive
    ? (currentChipData.starters || starters)
    : (strategy !== 'pure_xp' && currentStrategyData
      ? currentStrategyData.starters
      : (structuralBuildData?.starters || starters));

  const displayBench = isChipActive
    ? (currentChipData.bench || (isBenchBoost ? [] : bench))
    : (strategy !== 'pure_xp' && currentStrategyData
      ? currentStrategyData.bench
      : (structuralBuildData?.bench || bench));

  const displayStartingXp = isChipActive
    ? (currentChipData.starting_xp != null ? currentChipData.starting_xp : currentChipData.total_xp)
    : (strategy !== 'pure_xp' && currentStrategyData
      ? currentStrategyData.starting_xp
      : (structuralBuildData?.starting_xp || effectiveStartingXp));

  // Group players for pitch rendering
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
      ...displayBench.map(p => ({ ...p, is_boosted: true, is_bench_asset: true }))
    ];
  }, [isBenchBoost, currentChipData, displayStarters, displayBench]);

  const gks = allPitchPlayers.filter(p => p.position === 'GK');
  const defs = allPitchPlayers.filter(p => p.position === 'DEF');
  const mids = allPitchPlayers.filter(p => p.position === 'MID');
  const fwds = allPitchPlayers.filter(p => p.position === 'FWD');

  const formation = isBenchBoost
    ? '15 Active (2-5-5-3)'
    : isChipActive
    ? (currentChipData.formation || `${defs.length}-${mids.length}-${fwds.length}`)
    : (strategy !== 'pure_xp' && currentStrategyData
      ? currentStrategyData.formation
      : (structuralBuildData?.formation || `${defs.length}-${mids.length}-${fwds.length}`));

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
    { id: 'none', label: 'No Chip', icon: ShieldCheck, desc: 'Regular matchday XI (No chip active)' },
    { id: 'wildcard', label: 'Wildcard', icon: Cards, desc: 'Unlimited permanent transfers with no point hits' },
    { id: 'freehit', label: 'Free Hit', icon: Lightning, desc: 'Make unlimited transfers for this gameweek only' },
    { id: 'bboost', label: 'Bench Boost', icon: RocketLaunch, desc: 'Activate Bench Boost (All 15 players score)' },
    { id: '3xc', label: 'Triple Captain', icon: Crown, desc: 'Triple Captain Active (Captain scores 3x points)' }
  ];

  const strategyOptions = [
    { id: 'pure_xp', label: 'Max Points', icon: Target, desc: 'Pick the best possible starting XI for maximum points' },
    { id: 'rank_protect', label: 'Protect Lead', icon: ShieldCheck, desc: 'Back popular picks to defend your rank and protect your lead' },
    { id: 'differential_chase', label: 'Climb Rank', icon: Lightning, desc: 'Back low-ownership punts to gain ground on your mini-league rivals' }
  ];

  const buildOptions = [
    { id: 'spread', label: 'Big in the Middle', shortLabel: '3-5-2 Spread', icon: UsersThree, desc: STRUCTURAL_BUILDS.spread.tooltip },
    { id: 'anchor', label: 'Haaland Mega-Anchor', shortLabel: 'Haaland Anchor', icon: Crown, desc: STRUCTURAL_BUILDS.anchor.tooltip }
  ];

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
            <span className="rec-tag font-mono">BUY</span>
            <span className="rec-player-name">{inName}</span>
          </div>
          <CaretRight size={13} className="rec-arrow" />
          <div className="rec-transfer-pill out">
            <ArrowDownRight size={13} weight="bold" />
            <span className="rec-tag font-mono">SELL</span>
            <span className="rec-player-name">{outName}</span>
          </div>
        </div>
      );
    }

    if (summaryStr.toLowerCase().includes('roll transfer') || summaryStr.toLowerCase().includes('save free transfer') || summaryStr.includes('LOCKED') || summaryStr.includes('INITIAL')) {
      return (
        <div className="directive-structured-text">
          <span className="directive-action">Save Free Transfer (Roll FT)</span>
          <span className="directive-separator font-mono">·</span>
          <span className="directive-detail">Bank 1 FT to have 2 free transfers available next week</span>
        </div>
      );
    }

    const cleanMsg = summaryStr.replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '');
    return (
      <div className="directive-structured-text">
        <span className="directive-action">{cleanMsg}</span>
      </div>
    );
  };

  const boostedBenchList = useMemo(() => {
    return displayBench.map((p, idx) => ({
      ...p,
      is_boosted: true,
      slotLabel: idx === 0 ? 'GK Sub' : `Sub ${idx}`
    }));
  }, [displayBench]);

  const benchUpliftTotal = useMemo(() => {
    return displayBench.reduce((acc, p) => acc + Number(p.expected_points || 0), 0).toFixed(1);
  }, [displayBench]);

  // Dynamic Captain Profile for Decision Brief
  const activeCaptain = displayStarters.find(p => p.is_captain) || displayStarters[0] || CAPTAINCY_DECISION_BRIEF.selectedCaptain;

  return (
    <div>
      {/* 1. Tactical Captaincy Decision Brief (Expandable Institutional Card) */}
      <div className="decision-brief-container">
        <div className="decision-brief-card">
          <div
            className="decision-brief-header"
            onClick={() => setIsBriefExpanded(prev => !prev)}
            role="button"
            tabIndex={0}
            aria-expanded={isBriefExpanded}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setIsBriefExpanded(prev => !prev);
              }
            }}
          >
            <div className="brief-header-left">
              <span className="brief-badge font-mono">
                <Crown size={12} weight="fill" />
                <span>CAPTAINCY BRIEF</span>
              </span>
              <span className="brief-title">Manager's Decision Brief</span>
              <span className="brief-subtitle">
                · {squadBuild === 'spread' ? 'Why Bruno Fernandes (C) is your best captain pick this week' : 'Haaland (C) Mega-Anchor Setup'}
              </span>
            </div>

            <div className="brief-header-right">
              <div className="brief-captain-pill font-mono">
                <span className="brief-captain-name">{activeCaptain.web_name || 'Bruno Fernandes'} (C)</span>
                <span className="brief-captain-xp">
                  {(Number(activeCaptain.expected_points || 5.6) * 2).toFixed(1)} Exp Pts
                </span>
              </div>
              <button
                type="button"
                className={`brief-chevron-btn ${isBriefExpanded ? 'expanded' : ''}`}
                aria-label={isBriefExpanded ? 'Collapse brief' : 'Expand brief'}
              >
                {isBriefExpanded ? <CaretUp size={16} weight="bold" /> : <CaretDown size={16} weight="bold" />}
              </button>
            </div>
          </div>

          {isBriefExpanded && (
            <div className="decision-brief-body">
              {/* Left Column: 4 Core Tactical Rationales */}
              <div>
                <div className="brief-section-title font-mono">
                  <Sparkle size={13} weight="fill" color="var(--accent-amber)" />
                  <span>Why Bruno (C)?</span>
                </div>
                <div className="brief-rationales-grid">
                  {CAPTAINCY_DECISION_BRIEF.rationales.map((r) => {
                    const Icon = r.id === 'fixture_mult' ? HouseLine : (r.id === 'penalty_order' ? Target : (r.id === 'set_piece_monopoly' ? CornersOut : TrendUp));
                    return (
                      <div key={r.id} className="brief-rationale-card">
                        <div className="rationale-card-header">
                          <div className="rationale-card-title">
                            <Icon size={14} weight="bold" color="var(--accent-amber)" />
                            <span>{r.title}</span>
                          </div>
                          <span className="rationale-card-badge font-mono">{r.badge}</span>
                        </div>
                        <div className="rationale-card-text">{r.summary}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Head-to-Head Alternative Comparison Matrix */}
              <div>
                <div className="brief-section-title font-mono">
                  <Target size={13} weight="fill" color="var(--accent-cyan)" />
                  <span>Other Captain Options</span>
                </div>
                <div className="brief-alternatives-card">
                  <div className="alternatives-list">
                    {CAPTAINCY_DECISION_BRIEF.alternatives.map((alt) => (
                      <div key={alt.name} className="alternative-item">
                        <div className="alt-player-info">
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                              <span className="alt-player-name">{alt.name}</span>
                              <span className="alt-fixture-tag font-mono">{alt.team} · {alt.fixture}</span>
                            </div>
                            <div className="alt-comparison-text" title={alt.comparison}>
                              {alt.comparison}
                            </div>
                          </div>
                        </div>
                        <div className="alt-stats-block font-mono">
                          <div className="alt-xp-val">{alt.captainXp.toFixed(1)} pts (2x)</div>
                          <div className="alt-verdict-tag">{alt.verdict}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>


      {/* 2. Streamlined Matchday Control Deck with Structural Squad Toggle */}
      <div className="matchday-control-deck">
        <div className="deck-group deck-group-build">
          <span className="deck-label font-mono">Build</span>
          <div className="segmented-chip-rail chip-rail-scrollable" role="group" aria-label="Structural Build Selection">
            {buildOptions.map(b => {
              const Icon = b.icon;
              const isSelected = squadBuild === b.id;
              return (
                <button
                  key={b.id}
                  type="button"
                  className={`segmented-chip-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => setSquadBuild(b.id)}
                  title={b.desc}
                >
                  <Icon size={13} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{b.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="deck-group deck-group-scenario">
          <span className="deck-label font-mono">Chips</span>
          <div className="segmented-chip-rail chip-rail-scrollable" role="group" aria-label="Chip Selection">
            {chipOptions.map(chip => {
              const Icon = chip.icon;
              const isSelected = activeChip === chip.id;
              return (
                <button
                  key={chip.id}
                  type="button"
                  className={`segmented-chip-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectChip(chip.id)}
                  title={`Play ${chip.label}`}
                >
                  <Icon size={13} weight={isSelected ? 'fill' : 'bold'} />
                  <span>{chip.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="deck-group deck-group-strategy">
          <span className="deck-label font-mono">Goal</span>
          <div className="segmented-chip-rail chip-rail-scrollable" role="group" aria-label="Goal Selection">
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
            <span className="telemetry-label">Lineup</span>
            <span className="telemetry-value">{formation}</span>
          </div>
          <div className="deck-telemetry-divider" />
          <div className="deck-telemetry-item font-mono">
            <span className="telemetry-label">Starting</span>
            <span className="telemetry-value xp-highlight">{displayStartingXp} <span className="telemetry-unit">pts</span></span>
          </div>
        </div>
      </div>


      {/* Streamlined Contextual Directive Strip */}
      <div className={`matchday-directive-strip ${isChipActive ? 'chip-mode' : strategy !== 'pure_xp' ? 'strategy-mode' : 'move-mode'}`}>
        <div className="directive-tag-box font-mono">
          {isChipActive ? (
            <>
              <RocketLaunch size={13} weight="fill" />
              <span>ACTIVE CHIP</span>
            </>
          ) : strategy !== 'pure_xp' ? (
            <>
              <Target size={13} weight="fill" />
              <span>TACTIC</span>
            </>
          ) : (
            <>
              <Lightning size={13} weight="fill" />
              <span>NEXT MOVE</span>
            </>
          )}
        </div>
        <div className="directive-body">
          {isChipActive ? (
            <div className="directive-structured-text">
              <span className="directive-action chip-action-text">
                {currentChipData.label || 'Chip Active'}
              </span>
              <span className="directive-separator font-mono">·</span>
              <span className="directive-detail">
                {currentChipData.description || 'Active matchday chip projection'}
              </span>
            </div>
          ) : currentStrategyData && strategy !== 'pure_xp' ? (
            <div className="directive-structured-text">
              <span className="directive-action strategy-action-text">
                {currentStrategyData.label}
              </span>
              <span className="directive-separator font-mono">·</span>
              <span className="directive-detail">
                {currentStrategyData.subtitle || 'Tactical Goal Active'} · Formation {currentStrategyData.formation}
              </span>
            </div>
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
                  <RocketLaunch size={15} weight="fill" color="var(--accent-emerald)" />
                  <span className="panel-title">BENCH BOOST</span>
                </div>
                <span className="panel-badge font-mono" style={{ whiteSpace: 'nowrap' }}>
                  15 SCORING
                </span>
              </div>

              {/* Bench Boost Metric Grid */}
              <div className="bb-telemetry-grid">
                <div className="bb-telemetry-stat">
                  <span className="bb-stat-label">STARTING XI</span>
                  <span className="bb-stat-val font-mono">{Number(startingXp || 64.7).toFixed(1)} <span className="bb-stat-unit">pts</span></span>
                </div>
                <div className="bb-telemetry-stat highlight">
                  <span className="bb-stat-label">BENCH CONTRIBUTION</span>
                  <span className="bb-stat-val font-mono emerald">+{benchUpliftTotal} <span className="bb-stat-unit">pts</span></span>
                </div>
                <div className="bb-telemetry-stat full-width">
                  <div>
                    <span className="bb-stat-label">TOTAL SQUAD PROJECTION</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>All 15 players scoring</span>
                  </div>
                  <span className="bb-stat-val font-mono emerald" style={{ fontSize: '16px' }}>
                    {displayStartingXp} <span className="bb-stat-unit">pts</span>
                  </span>
                </div>
              </div>

              <div className="bb-sub-header font-mono">
                <span>BENCH PLAYERS SCORING THIS WEEK</span>
                <span className="bb-count-pill">4 ACTIVE</span>
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
                    title="Click to view scouting report & stats"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                      <span className="bench-slot-tag font-mono boost-tag">
                        {p.slotLabel || 'SUB'}
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
                        bench pts
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bench-help-text">
                All 15 players are active on the pitch. Double-click any player card to view their scouting report & match stats.
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
                      title="Click to swap with starter · Double-click for player stats"
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
                          exp pts
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="bench-help-text">
                Click any starter and bench player to swap them. Double-click any player card to view their scouting report.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

