import React from 'react';
import { formatFplPrice } from '../constants/copyTokens';
import { getClubShortCode } from '../utils/playerMetadataHelper.js';

// One status word per player, most urgent first (Direction J: no badge stacks)
const getStatusWord = (player, isBgw, isDgw) => {
  if (isBgw) return { word: 'BLANK', title: 'Blank gameweek: no game scheduled' };
  if (isDgw) return { word: 'DGW', title: 'Double gameweek: 2 games scheduled' };
  if (player.cameo_risk != null && player.cameo_risk >= 0.25) {
    return { word: 'CAMEO', title: `${Math.round(player.cameo_risk * 100)}% chance of only a late cameo` };
  }
  if (player.hook_hazard > 0.15) {
    return { word: 'RISK', title: `${Math.round(player.hook_hazard * 100)}% chance of an early sub` };
  }
  return null;
};

export default function PlayerCard({
  player,
  onInspect,
  onOpenMatchup,
  onSelectSub,
  isSubTarget,
  isCaptain,
  isViceCaptain,
  isTripleCaptain,
  onToggleCaptain
}) {
  if (!player) return null;

  const xp = Number(player.dynamicXp || player.expected_points || 4.5);
  const pos = (player.position || 'MID').toUpperCase();
  const cost = formatFplPrice(player.cost ?? player.now_cost ?? player.selling_price ?? 0);

  // Matchup info: derive opponent correctly for both home and away players
  const fd = player.fixture_details;
  let opponent = player.fixture_opponent || null;
  let venue = player.fixture_venue || '';
  if (!opponent && fd) {
    const isHome = fd.home_team === player.team;
    venue = isHome ? 'H' : 'A';
    opponent = isHome ? fd.away_team : fd.home_team;
  }
  const fixtureLabel = opponent
    ? `${venue === 'H' ? 'vs' : '@'} ${getClubShortCode(opponent)}`
    : getClubShortCode(player.team);

  const fixtureCount = player.fixture_count !== undefined
    ? Number(player.fixture_count)
    : (opponent && (opponent.includes(',') || opponent.includes('/')) ? 2 : 1);
  const status = getStatusWord(player, fixtureCount === 0, fixtureCount >= 2);

  // Actual match points once the gameweek is played, forward xP before
  const hasActualPoints = player.actual_points !== undefined;
  const mult = isTripleCaptain ? 3 : (isCaptain ? 2 : 1);
  const displayPts = hasActualPoints
    ? Number(player.actual_points) * mult
    : (xp * mult).toFixed(1);
  const unit = hasActualPoints ? 'pts' : 'xP';

  const armband = isTripleCaptain ? '3×' : isCaptain ? 'C' : isViceCaptain ? 'VC' : 'C';
  const armbandLabel = isTripleCaptain
    ? `${player.web_name} is triple captain`
    : isCaptain
    ? `${player.web_name} is captain. Make vice-captain captain instead`
    : isViceCaptain
    ? `${player.web_name} is vice-captain. Make captain`
    : `Make ${player.web_name} captain`;

  const openMatchup = () => {
    if (onOpenMatchup) {
      onOpenMatchup(fd || { home_team: player.team, away_team: opponent || 'Opponent' });
    }
  };

  return (
    <div
      className={`wire-token ${isSubTarget ? 'is-target' : ''} ${isCaptain ? 'is-captain' : ''} ${isViceCaptain ? 'is-vice' : ''}`}
    >
      <button
        type="button"
        className="wire-token-main"
        aria-pressed={isSubTarget || undefined}
        aria-label={`${player.web_name}, ${pos}, £${cost}m, ${displayPts} ${unit}${mult > 1 ? ` (${mult}x)` : ''}`}
        onClick={() => (onSelectSub ? onSelectSub(player) : onInspect?.(player))}
        onDoubleClick={() => onInspect?.(player)}
        title="Click to swap or inspect · Double-click for match stats"
      >
        <span className="wire-token-name">{player.web_name}</span>
        <span className="wire-token-pts font-mono">
          {displayPts}
          <span className="wire-token-unit">{unit}</span>
          {hasActualPoints && Number(player.actual_bonus) > 0 && (
            <span className="wire-token-unit" title={`${player.actual_bonus} bonus points`}> +{player.actual_bonus}</span>
          )}
        </span>
      </button>

      <div className="wire-token-meta">
        <button
          type="button"
          className="wire-token-fixture font-mono"
          onClick={openMatchup}
          title="Match preview, win odds and clean sheet chances"
        >
          {pos} · {fixtureLabel}
        </button>
        {onToggleCaptain ? (
          <button
            type="button"
            className="wire-token-armband font-mono"
            aria-label={armbandLabel}
            aria-pressed={isCaptain || isTripleCaptain}
            title={armbandLabel}
            onClick={() => onToggleCaptain(player)}
          >
            {armband}
          </button>
        ) : (isCaptain || isViceCaptain) && (
          <span className="wire-token-armband font-mono" title={isCaptain ? 'Captain' : 'Vice-captain'}>{armband}</span>
        )}
      </div>

      {status && (
        <span className="wire-token-status font-mono" title={status.title}>{status.word}</span>
      )}
    </div>
  );
}
