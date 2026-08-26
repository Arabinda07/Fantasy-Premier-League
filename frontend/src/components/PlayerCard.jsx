import React from 'react';

export default function PlayerCard({
  player,
  onInspect,
  onOpenMatchup,
  onSelectSub,
  isSubTarget,
  isCaptain,
  isViceCaptain,
  isTripleCaptain,
  isBoosted
}) {
  if (!player) return null;

  const xp = Number(player.dynamicXp || player.expected_points || 4.5);
  const pos = (player.position || 'MID').toUpperCase();
  const cost = Number(player.cost || player.now_cost || 0).toFixed(1);

  // Matchup info
  const opponent = player.fixture_opponent || player.fixture_details?.away_team || player.fixture_details?.opponent;
  const venue = player.fixture_venue || (player.fixture_details ? (player.fixture_details.home_team === player.team ? 'H' : 'A') : '');
  const fixtureLabel = opponent
    ? `${venue === 'H' ? 'vs' : '@'} ${opponent.substring(0, 3).toUpperCase()}`
    : '';

  return (
    <div
      className={`player-pitch-card ${isSubTarget ? 'sub-target' : ''} ${isBoosted ? 'bench-boosted' : ''}`}
      onClick={() => {
        if (onInspect) onInspect(player);
      }}
      onDoubleClick={() => {
        if (onInspect) onInspect(player);
      }}
      title="Click or double-click to view complete player DNA & point breakdown"
    >
      {/* Top Header: Badge / Position + Price */}
      <div className="player-card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {isTripleCaptain ? (
            <span className="captain-badge triple" title="Triple Captain Active (3x Points)">3XC</span>
          ) : isCaptain ? (
            <span className="captain-badge" title="Team Captain (2x Points)">C</span>
          ) : isViceCaptain ? (
            <span className="vice-captain-badge" title="Vice Captain">V</span>
          ) : null}
          <span className={`player-pos-tag ${pos}`}>{pos}</span>
        </div>
        <span className="player-cost-val font-mono">£{cost}m</span>
      </div>

      {/* Player Web Name */}
      <div className="player-name">
        {player.web_name}
      </div>

      {/* Team / Opponent Subtitle */}
      <div className="player-team-row">
        <span
          className="player-team-tag"
          onClick={(e) => {
            e.stopPropagation();
            if (onOpenMatchup) {
              onOpenMatchup(player.fixture_details || { home_team: player.team, away_team: opponent || 'Opponent' });
            }
          }}
          title="Click to view match preview & clean sheet odds"
        >
          {player.team} {fixtureLabel && <span className="fixture-sub-tag font-mono">{fixtureLabel}</span>}
        </span>
      </div>

      {/* Minimalist Expected Points Score Banner */}
      <div className="player-stats-bar" style={{ justifyContent: 'center' }}>
        <span className="player-xp font-mono">
          {isTripleCaptain ? (xp * 3).toFixed(1) : isCaptain ? (xp * 2).toFixed(1) : xp.toFixed(1)} <span className="xp-unit">{isTripleCaptain ? '3xP' : isCaptain ? '2xP' : 'xP'}</span>
        </span>
      </div>
    </div>
  );
}
