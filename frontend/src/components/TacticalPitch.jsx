import React, { useMemo, useState } from 'react';
import PlayerCard from './PlayerCard';
import MatchdayHandoverModal from './MatchdayHandoverModal';
import TransferBreakdownModal from './TransferBreakdownModal';
import { formatFplPrice, AUTO_SUB_LABELS } from '../constants/copyTokens';

// Helper to extract numeric expected points from player
const getPlayerXp = (p) => {
  if (!p) return 0;
  const val = p.dynamicXp ?? p.expected_points ?? p.xp ?? p.xP ?? 0;
  return Number(val) || 0;
};

const summaryText = (summary) =>
  typeof summary === 'string' ? summary : (summary?.headline || summary?.action || '');

const ROLL_PHRASES = ['roll transfer', 'save free transfer', 'bank'];
const STAND_PAT_PHRASES = ['no immediate transfers', 'stand pat', 'lineup locked'];
const includesAny = (str, phrases) => phrases.some(ph => str.toLowerCase().includes(ph));
const isStandPat = (str) => includesAny(str, STAND_PAT_PHRASES) || str.includes('LOCKED') || str.includes('INITIAL');

/**
 * Resolve [{in, out}] transfer pairs from the solver summary.
 * Order of preference: structured pairwise_transfers, structured transfers,
 * the "[IN] a, b | [OUT] c, d" string format, then the first roadmap step.
 */
const parseTransferPairs = (summary, liveData) => {
  if (!summary) return [];
  if (typeof summary === 'object') {
    const list = Array.isArray(summary.pairwise_transfers) && summary.pairwise_transfers.length > 0
      ? summary.pairwise_transfers
      : (Array.isArray(summary.transfers) ? summary.transfers : []);
    if (list.length > 0) {
      return list.map(t => ({
        in: t.in || t.in_player || t.in_name || 'Target In',
        out: t.out || t.out_player || t.out_name || 'Target Out'
      }));
    }
  }

  const str = summaryText(summary);
  const inMatch = str.match(/\[IN\]\s*([^|\]]+)/i);
  const outMatch = str.match(/\[OUT\]\s*([^|[]+)/i);
  if (inMatch && outMatch) {
    const outList = outMatch[1].split(',').map(s => s.trim()).filter(Boolean);
    return inMatch[1].split(',').map(s => s.trim()).filter(Boolean)
      .map((name, idx) => ({ in: name, out: outList[idx] || 'Target Out' }));
  }

  const roadmapItem = liveData?.multi_horizon_roadmap?.[0];
  if (roadmapItem?.transfers_in?.length > 0) {
    return roadmapItem.transfers_in.map((name, idx) => ({
      in: name,
      out: roadmapItem.transfers_out?.[idx] || 'Target Out'
    }));
  }
  return [];
};

const parseNetGain = (summary) => {
  if (typeof summary === 'object' && summary?.net_gain != null) return Number(summary.net_gain);
  const match = summaryText(summary).match(/\+(\d+\.?\d*)\s*pts/i);
  return match ? parseFloat(match[1]) : null;
};

const CHIP_OPTIONS = [
  { id: 'none', label: 'No Chip', desc: 'Regular matchday XI' },
  { id: 'wildcard', label: 'Wildcard', desc: 'Unlimited permanent transfers with no point hits' },
  { id: 'freehit', label: 'Free Hit', desc: 'Unlimited transfers for this gameweek only' },
  { id: 'bboost', label: 'Bench Boost', desc: 'All 15 players score' },
  { id: '3xc', label: 'Triple Captain', desc: 'Captain scores 3x points' }
];

const STRATEGY_OPTIONS = [
  { id: 'pure_xp', label: 'Max Points', desc: 'Pick the best possible starting XI for maximum points' },
  { id: 'rank_protect', label: 'Protect Lead', desc: 'Back popular picks to defend your rank' },
  { id: 'differential_chase', label: 'Climb Rank', desc: 'Back low-ownership picks to gain ground on rivals' }
];

export default function TacticalPitch({
  liveData,
  starters = [],
  bench = [],
  allPlayersData = [],
  selectedPlayer,
  selectedSwapPlayer,
  setSelectedSwapPlayer,
  onSelectPlayer,
  onSwapPlayers,
  onInspectPlayer,
  onOpenMatchup,
  onOpenFixture,
  actionSummary,
  activeChip = 'none',
  onSelectChip = () => {},
  strategy = 'pure_xp',
  onSelectStrategy = () => {},
  onNavigateTab,
  onOpenSyncModal,
  onToggleCaptain,
  isSimulating = false,
  onToggleSimulate = () => {},
  onResetToSuggested = () => {},
  isLineupLocked = false,
  onConfirmLockLineup = () => {},
  freeTransfers = 1,
  swapNotice = null
}) {
  const effectiveChipSimulations = liveData?.chip_simulations;
  const effectiveStrategies = liveData?.strategies || {};
  const effectiveActionSummary = liveData?.action_summary || actionSummary;
  const activeSelectedPlayer = selectedSwapPlayer || selectedPlayer;

  const [isHandoverOpen, setIsHandoverOpen] = useState(false);
  const [isBreakdownOpen, setIsBreakdownOpen] = useState(false);

  const handlePlayerSelect = (p) => {
    if (activeChip !== 'none' || !isSimulating) {
      if (onInspectPlayer) onInspectPlayer(p);
      return;
    }

    if (onSwapPlayers && activeSelectedPlayer) {
      if ((activeSelectedPlayer.player_code || activeSelectedPlayer.code) !== (p.player_code || p.code)) {
        onSwapPlayers(activeSelectedPlayer, p);
      } else if (setSelectedSwapPlayer) {
        setSelectedSwapPlayer(null);
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

  // Compute chip simulations from the current squad when the payload has none
  const resolvedChipData = useMemo(() => {
    const capt = starters.find(p => p.is_captain) || starters[0];
    const captXp = getPlayerXp(capt);
    const baseStartersSum = starters.reduce((acc, p) => acc + getPlayerXp(p), 0);
    const benchXp = bench.reduce((acc, p) => acc + getPlayerXp(p), 0);
    const tripleCaptainXp = baseStartersSum + (captXp * 2);
    const benchBoostXp = baseStartersSum + captXp + benchXp;

    return {
      '3xc': {
        starters,
        bench,
        starting_xp: Number(tripleCaptainXp.toFixed(1)),
        label: `Triple Captain on ${capt?.web_name || 'your captain'}`
      },
      bboost: {
        starters,
        bench: bench.map(p => ({ ...p, is_boosted: true })),
        starting_xp: Number(benchBoostXp.toFixed(1)),
        label: `Bench Boost · +${benchXp.toFixed(1)} pts from the bench`
      },
      ...(effectiveChipSimulations || {})
    };
  }, [starters, bench, effectiveChipSimulations]);

  const currentStrategyData = strategy !== 'pure_xp' ? effectiveStrategies[strategy] || null : null;

  // Active display data priority: chip > non-default strategy > base squad
  const currentChipData = activeChip !== 'none' ? resolvedChipData[activeChip] || null : null;
  const isChipActive = currentChipData != null;
  const isBenchBoost = activeChip === 'bboost';

  const displayStarters = isChipActive
    ? (currentChipData.starters || starters)
    : (currentStrategyData ? currentStrategyData.starters : starters);

  const displayBench = isChipActive
    ? (currentChipData.bench || bench)
    : (currentStrategyData ? currentStrategyData.bench : bench);

  const benchXp = displayBench.reduce((acc, p) => acc + getPlayerXp(p), 0);

  // Starting XI xP including the captain bonus (2x, or 3x with Triple Captain)
  const startersXp = useMemo(() => {
    if (!displayStarters || displayStarters.length === 0) return 0;
    const base = displayStarters.reduce((acc, p) => acc + getPlayerXp(p), 0);
    const capt = displayStarters.find(p => p.is_captain) || displayStarters[0];
    const captainBonus = getPlayerXp(capt) * (activeChip === '3xc' ? 2 : 1);
    return base + captainBonus;
  }, [displayStarters, activeChip]);

  const calculatedTotalXp = Number((startersXp + (isBenchBoost ? benchXp : 0)).toFixed(1));
  const displayTotalXp = (isChipActive ? currentChipData.starting_xp : currentStrategyData?.starting_xp) ?? calculatedTotalXp;

  // Bench Boost puts all 15 on the pitch
  const allPitchPlayers = useMemo(() => {
    if (!isBenchBoost) return displayStarters;
    if (currentChipData?.starters?.length === 15) return currentChipData.starters;
    return [...displayStarters, ...displayBench];
  }, [isBenchBoost, currentChipData, displayStarters, displayBench]);

  const rows = ['GK', 'DEF', 'MID', 'FWD'].map(pos => allPitchPlayers.filter(p => p.position === pos));
  const [, defs, mids, fwds] = rows;

  const formation = isBenchBoost
    ? 'All 15 scoring'
    : (currentChipData?.formation || currentStrategyData?.formation || `${defs.length}-${mids.length}-${fwds.length}`);

  const transferPairs = useMemo(
    () => parseTransferPairs(effectiveActionSummary, liveData),
    [effectiveActionSummary, liveData]
  );

  // Structured recommendation for the breakdown and handover modals
  const resolvedTransferRecommendation = useMemo(() => {
    if (!effectiveActionSummary) return null;
    const str = summaryText(effectiveActionSummary);

    if (transferPairs.length > 0) {
      const topPair = transferPairs[0];
      const allKnown = [
        ...(allPlayersData || []),
        ...displayStarters,
        ...displayBench,
        ...(liveData?.all_players || [])
      ];
      const findP = (name) => {
        const target = (name || '').toLowerCase().trim();
        if (!target) return null;
        return allKnown.find(p =>
          [p.web_name, p.name, p.player_name].some(n => n && n.toLowerCase() === target)
        );
      };

      const foundIn = findP(topPair.in);
      const foundOut = findP(topPair.out);

      const fixtureOf = (player) => {
        if (!player) return { fixture: '', fdr: null };
        if (player.next_opponent || player.fixture) {
          return { fixture: player.next_opponent || player.fixture, fdr: player.fdr || player.next_fdr || null };
        }
        if (player.fixture_opponent) {
          return {
            fixture: `${player.fixture_venue === 'A' ? '@' : 'vs'} ${player.fixture_opponent}`,
            fdr: player.fixture_fdr || null
          };
        }
        return { fixture: '', fdr: null };
      };

      const toSide = (found, fallbackName, costOf) => ({
        name: found?.web_name || fallbackName,
        team: found?.team || found?.team_name || '',
        position: found?.position || '',
        expected_points: getPlayerXp(found),
        cost: found ? Number(costOf(found) || 0) : 0,
        ...fixtureOf(found)
      });

      const playerIn = toSide(foundIn, topPair.in, p => p.now_cost || p.cost);
      const playerOut = toSide(foundOut, topPair.out, p => p.selling_price || p.now_cost || p.cost);

      let netGain = parseNetGain(effectiveActionSummary);
      if (netGain == null && foundIn && foundOut) {
        netGain = Math.max(0.1, Number((playerIn.expected_points - playerOut.expected_points).toFixed(2)));
      }

      return {
        isRollFt: false,
        playerIn,
        playerOut,
        netGain,
        costDelta: Number((playerIn.cost - playerOut.cost).toFixed(1))
      };
    }

    if (includesAny(str, ROLL_PHRASES) || isStandPat(str)) {
      return { isRollFt: true, playerIn: null, playerOut: null, netGain: 0, costDelta: 0 };
    }
    return null;
  }, [effectiveActionSummary, transferPairs, liveData, allPlayersData, displayStarters, displayBench]);

  // Plain-language directive for the recommended move
  const directive = useMemo(() => {
    const str = summaryText(effectiveActionSummary);
    if (transferPairs.length > 0) {
      const gain = parseNetGain(effectiveActionSummary);
      let priceAlert = null;
      const alertMatch = str.match(/(?:Price Risk|Price Alert):\s*([^()|]+)/i);
      if (alertMatch && alertMatch[1].trim()) {
        priceAlert = `Price alert: ${alertMatch[1].trim()}`;
      } else if (!str && liveData?.falling_price_risks?.length > 0) {
        priceAlert = `Price alert: ${liveData.falling_price_risks.join(', ')}`;
      }
      return {
        pairs: transferPairs,
        detail: [gain != null ? `+${gain.toFixed(1)} pts projected gain` : null, priceAlert].filter(Boolean).join(' · ')
      };
    }
    if (str.toLowerCase().includes('wildcard')) {
      return { action: 'Play your Wildcard', detail: 'A full squad rebuild beats piecemeal transfers this week' };
    }
    if (includesAny(str, ROLL_PHRASES)) {
      return { action: 'Save your free transfer', detail: 'Roll it to have more free transfers in coming gameweeks' };
    }
    if (isStandPat(str)) {
      return { action: 'Stand pat', detail: 'No transfers needed this gameweek' };
    }
    const cleanMsg = str
      .replace(/EXECUTE\s*\d*\s*FREE\s*TRANSFER\(S\):\s*/i, '')
      .replace(/\[Squad holds[^\]]*\]/gi, '')
      .replace(/\|\s*\[!\]\s*Nightly Price Risk:[^|]+/gi, '')
      .replace(/Option Hurdle:[^)]+\)/gi, '')
      .trim();
    return { action: cleanMsg || 'Review transfers in the Planner', detail: '' };
  }, [effectiveActionSummary, transferPairs, liveData]);

  // Gameweek status
  const gameweek = liveData?.gameweek || 1;
  const isNonParticipating = liveData?.participated === false || (starters.length === 0 && bench.length === 0);
  const isCompletedGw = Boolean(liveData?.is_completed);
  const canAct = !isCompletedGw && !isNonParticipating;

  const manager = liveData?.manager_profile;
  const isSynced = Boolean(
    manager?.entry_id ||
    (typeof window !== 'undefined' && localStorage.getItem('fpl_synced_entry_id'))
  );
  const bank = liveData?.bank ?? manager?.bank;
  const playedChip = manager?.active_chip;

  const completedScore = liveData?.event_points ?? displayStarters.reduce(
    (acc, p) => acc + Number(p.actual_points || 0) * (p.is_captain ? 2 : 1), 0
  );

  const heroValue = isNonParticipating ? '0' : isCompletedGw ? completedScore : Number(displayTotalXp).toFixed(1);
  const heroUnit = isCompletedGw || isNonParticipating ? 'PTS' : 'XP';
  const heroSlug = isNonParticipating
    ? `Gameweek ${gameweek} · No squad entered`
    : isCompletedGw
    ? `Gameweek ${gameweek} · Final score`
    : `Gameweek ${gameweek} · Projected`;

  const benchBanner = isBenchBoost
    ? 'Bench Boost · all 15 score'
    : isCompletedGw
    ? 'Matchday bench'
    : 'Bench';

  return (
    <div className="wire">
      <h1 className="sr-only">Gameweek {gameweek} lineup</h1>

      {/* Level 1: Status Hero & Level 2: Horizontal Squad Controls Strip */}
      <header className="wire-header">
        <div className="wire-hero">
          <span className="wire-slug">{heroSlug}</span>
          <span className="wire-hero-num font-mono">
            {heroValue}
            <span className="wire-hero-unit">{heroUnit}</span>
          </span>
          <span className="wire-hero-sub font-mono">
            {isNonParticipating ? 'No squad' : isCompletedGw ? `${formation} · completed` : formation}
          </span>
        </div>

        {/* Level 2: Horizontal Gameweek Controls Strip */}
        <div className="wire-controls-strip" role="region" aria-label="Gameweek Controls">
          {bank != null && (
            <div className="wire-control-item">
              <span className="wire-control-label">Bank</span>
              <span className="wire-control-value font-mono">£{formatFplPrice(bank)}m</span>
            </div>
          )}
          {canAct && (
            <div className="wire-control-item">
              <span className="wire-control-label">Free transfers</span>
              <span className="wire-control-value font-mono">{freeTransfers}</span>
            </div>
          )}
          <div className="wire-control-item">
            <label htmlFor="wire-chip-select" className="wire-control-label">
              {isCompletedGw ? 'Chip played' : 'Chip'}
            </label>
            <div className="wire-control-value">
              {canAct ? (
                <div className="wire-select-wrapper">
                  <select
                    id="wire-chip-select"
                    value={activeChip}
                    onChange={(e) => onSelectChip(e.target.value)}
                    className="wire-select"
                    aria-label="Matchday chip"
                    title={CHIP_OPTIONS.find(c => c.id === activeChip)?.desc}
                  >
                    {CHIP_OPTIONS.map(chip => (
                      <option key={chip.id} value={chip.id}>{chip.label}</option>
                    ))}
                  </select>
                  <span className="wire-select-caret" aria-hidden="true">▾</span>
                </div>
              ) : (
                <span className="wire-control-text">
                  {CHIP_OPTIONS.find(c => c.id === playedChip)?.label || (playedChip ? playedChip.toUpperCase() : 'None')}
                </span>
              )}
            </div>
          </div>
          {canAct && (
            <div className="wire-control-item wire-control-item-strategy">
              <span className="wire-control-label">Goal</span>
              <div className="wire-segments" role="group" aria-label="Tactical goal">
                {STRATEGY_OPTIONS.map(opt => (
                  <button
                    key={opt.id}
                    type="button"
                    className="wire-segment"
                    aria-pressed={strategy === opt.id}
                    onClick={() => onSelectStrategy(opt.id)}
                    title={opt.desc}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}
          {isCompletedGw && liveData?.event_rank && (
            <div className="wire-control-item">
              <span className="wire-control-label">Gameweek rank</span>
              <span className="wire-control-value font-mono">#{Number(liveData.event_rank).toLocaleString()}</span>
            </div>
          )}
        </div>
      </header>

      {swapNotice && (
        <p className="wire-notice" role="status">{swapNotice}</p>
      )}

      <div className="wire-split">
        {/* Primary tactical surface */}
        <section className="wire-pitch-col" aria-labelledby="wire-xi-banner">
          <h2 id="wire-xi-banner" className="wire-banner">
            {isBenchBoost ? 'Full squad' : 'Starting XI'}
            {isSimulating && canAct && <span className="zinc"> · tap two players to swap</span>}
          </h2>

          {isNonParticipating ? (
            <div className="wire-empty">
              <p className="wire-empty-title">No squad for Gameweek {gameweek}</p>
              <p className="zinc">
                {manager?.manager_name || 'This manager'} had no registered squad this gameweek, so the score is 0.
              </p>
            </div>
          ) : (
            <div className={`wire-pitch ${isBenchBoost ? 'is-full-squad' : ''}`}>
              {rows.map((row, idx) => (
                <div key={idx} className={`wire-pitch-row pitch-row-count-${row.length}`}>
                  {row.map(p => (
                    <PlayerCard
                      key={p.player_code || p.id || p.web_name}
                      player={p}
                      isCaptain={Boolean(p.is_captain)}
                      isViceCaptain={Boolean(p.is_vice_captain)}
                      isTripleCaptain={activeChip === '3xc' && Boolean(p.is_captain)}
                      isSubTarget={activeSelectedPlayer?.player_code === p.player_code}
                      onSelectSub={handlePlayerSelect}
                      onInspect={onInspectPlayer}
                      onOpenMatchup={handleMatchupClick}
                      onToggleCaptain={canAct ? onToggleCaptain : undefined}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Situational context */}
        <aside className="wire-context">
          <section className="wire-decision-module" aria-labelledby="wire-move-banner">
            <div className="wire-decision-header">
              <div className="wire-decision-info">
                <h2 id="wire-move-banner" className="wire-banner">
                  {isCompletedGw ? 'Matchday summary' : isChipActive ? 'Chip preview' : currentStrategyData ? 'Goal override' : 'Recommended move'}
                </h2>
                {isNonParticipating ? (
                  <p className="zinc">Did not take part in Gameweek {gameweek}.</p>
                ) : isCompletedGw ? (
                  <p className="wire-directive-action">{completedScore} points scored</p>
                ) : isChipActive ? (
                  <p className="wire-directive-action">{currentChipData.label || 'Chip active'}</p>
                ) : currentStrategyData ? (
                  <>
                    <p className="wire-directive-action">{currentStrategyData.label}</p>
                    {currentStrategyData.subtitle && <p className="zinc">{currentStrategyData.subtitle}</p>}
                  </>
                ) : (
                  <div className="wire-directive-body">
                    {directive.pairs ? (
                      <ul className="wire-moves">
                        {directive.pairs.map((pair, idx) => (
                          <li key={idx}>
                            <span className="wire-move-tag">In</span> {pair.in}
                            <span className="zinc"> for </span>
                            <span className="wire-move-tag">Out</span> {pair.out}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="wire-directive-action">{directive.action}</p>
                    )}
                    {directive.detail && <p className="wire-directive-detail font-mono">{directive.detail}</p>}
                    <div className="wire-directive-links">
                      <button
                        type="button"
                        className="wire-link"
                        onClick={() => setIsBreakdownOpen(true)}
                        title="See why this move is recommended"
                      >
                        See the reasoning →
                      </button>
                      {canAct && onNavigateTab && (
                        <button
                          type="button"
                          className="wire-link"
                          onClick={() => onNavigateTab('transfers')}
                        >
                          Open the Planner →
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action buttons stacked and aligned with top third */}
              {!isCompletedGw && !isNonParticipating && (
                <div className="wire-decision-actions">
                  {canAct && (
                    <button
                      type="button"
                      className="wire-action"
                      aria-pressed={isSimulating}
                      onClick={onToggleSimulate}
                      title={isSimulating ? 'Stop testing swaps' : 'Test bench swaps before you commit'}
                    >
                      {isSimulating ? 'Done swapping' : 'Try swaps'}
                    </button>
                  )}
                  {canAct && isSimulating && (
                    <button type="button" className="wire-action" onClick={onResetToSuggested}>
                      Reset to suggested
                    </button>
                  )}
                  <button
                    type="button"
                    className="wire-action is-primary"
                    onClick={() => {
                      if (!isSynced && onOpenSyncModal) {
                        onOpenSyncModal();
                        return;
                      }
                      setIsHandoverOpen(true);
                    }}
                    disabled={isLineupLocked}
                  >
                    {isLineupLocked ? 'Lineup locked' : isSynced ? 'Lock lineup' : 'Connect FPL squad'}
                  </button>
                </div>
              )}
            </div>
          </section>

          {!isNonParticipating && (
            <section aria-labelledby="wire-bench-banner">
              <h2 id="wire-bench-banner" className="wire-banner">{benchBanner}</h2>

              {isBenchBoost && (
                <dl className="wire-status wire-status-tight">
                  <div className="wire-status-row">
                    <dt>Starting XI</dt>
                    <dd className="font-mono">{startersXp.toFixed(1)}</dd>
                  </div>
                  <div className="wire-status-row">
                    <dt>Bench ({displayBench.length})</dt>
                    <dd className="font-mono">+{benchXp.toFixed(1)}</dd>
                  </div>
                </dl>
              )}

              <ol className="wire-bench">
                {displayBench.map((p, idx) => {
                  const isSelected = activeSelectedPlayer?.player_code === p.player_code;
                  const hasActualPoints = p.actual_points !== undefined;
                  const pts = hasActualPoints ? Number(p.actual_points) : getPlayerXp(p).toFixed(1);
                  const subOdds = !hasActualPoints && AUTO_SUB_LABELS[p.auto_sub_label];
                  const slot = idx === 0 ? 'GK' : String(idx);
                  return (
                    <li key={p.player_code || p.id || p.web_name}>
                      <button
                        type="button"
                        className="wire-bench-line"
                        aria-pressed={isSelected || undefined}
                        aria-label={`Bench ${slot}: ${p.web_name}, ${p.position}, £${formatFplPrice(p.cost ?? p.now_cost ?? p.selling_price ?? 0)}m, ${pts} ${hasActualPoints ? 'points' : 'expected points'}`}
                        onClick={() => (isBenchBoost ? onInspectPlayer?.(p) : handlePlayerSelect(p))}
                        onDoubleClick={() => onInspectPlayer?.(p)}
                      >
                        <span className="wire-bench-slot font-mono">{slot}</span>
                        <span className="wire-bench-name">{p.web_name}</span>
                        <span className="wire-bench-meta font-mono">
                          {p.position}
                          {subOdds && <span title={subOdds.tooltip}> · {subOdds.badge}</span>}
                        </span>
                        <span className="wire-bench-pts font-mono">{isBenchBoost ? `+${pts}` : pts}</span>
                      </button>
                    </li>
                  );
                })}
              </ol>

              <p className="wire-footnote">
                {isCompletedGw
                  ? 'Official bench scores for this gameweek.'
                  : isSimulating
                  ? 'Tap a starter, then a bench player, to swap them. Press Done swapping when finished.'
                  : 'Tap any player for their scouting report. Press Try swaps to test bench changes.'}
              </p>
            </section>
          )}
        </aside>
      </div>

      <MatchdayHandoverModal
        isOpen={isHandoverOpen}
        onClose={() => setIsHandoverOpen(false)}
        onConfirmLock={() => {
          if (onConfirmLockLineup) onConfirmLockLineup();
        }}
        liveData={liveData}
        starters={displayStarters}
        bench={displayBench}
        managerId={manager?.entry_id}
        managerName={manager?.manager_name}
        teamName={manager?.team_name}
        freeTransfers={freeTransfers}
        isLocked={isLineupLocked}
        recommendedTransfer={resolvedTransferRecommendation}
      />

      <TransferBreakdownModal
        isOpen={isBreakdownOpen}
        onClose={() => setIsBreakdownOpen(false)}
        managerId={manager?.entry_id}
        gameweek={gameweek}
        recommendedTransfer={resolvedTransferRecommendation}
        bank={bank}
      />
    </div>
  );
}
