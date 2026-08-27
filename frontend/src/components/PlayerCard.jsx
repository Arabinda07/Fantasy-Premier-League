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
  isBoosted,
  strategyBadge
}) {
  if (!player) return null;

  const xp = Number(player.dynamicXp || player.expected_points || 4.5);
  const pos = (player.position || 'MID').toUpperCase();
  const cost = Number(player.cost || player.now_cost || 0).toFixed(1);

  // Matchup info — derive opponent correctly for both home and away players
  const fd = player.fixture_details;
  let opponent = player.fixture_opponent || null;
  let venue = player.fixture_venue || '';
  if (!opponent && fd) {
    const isHome = fd.home_team === player.team;
    venue = isHome ? 'H' : 'A';
    opponent = isHome ? fd.away_team : fd.home_team;
  }
  const fixtureLabel = opponent
    ? `${venue === 'H' ? 'vs' : '@'} ${opponent.substring(0, 3).toUpperCase()}`
    : '';

  // Determine Blank (BGW) or Double Gameweek (DGW) status
  const fixtureCount = player.fixture_count !== undefined ? Number(player.fixture_count) : (opponent ? (opponent.includes(',') || opponent.includes('/') ? 2 : 1) : 1);
  const isBgw = fixtureCount === 0;
  const isDgw = fixtureCount >= 2;

  return (
    <div
      className={`player-pitch-card ${isSubTarget ? 'sub-target' : ''} ${isBoosted ? 'bench-boosted' : ''} ${isBgw ? 'is-bgw' : ''} ${isDgw ? 'is-dgw' : ''}`}
      onClick={() => {
        if (onSelectSub) {
          onSelectSub(player);
        } else if (onInspect) {
          onInspect(player);
        }
      }}
      onDoubleClick={() => {
        if (onInspect) onInspect(player);
      }}
      title="Click to swap player · Double-click for match stats & points breakdown"
    >
      {/* Top Header: Badge / Position + BGW/DGW Indicator + Price */}
      <div className="player-card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {isTripleCaptain ? (
            <span className="captain-badge triple" title="Triple Captain Active (3x Points)">3XC</span>
          ) : isCaptain ? (
            <span className="captain-badge" title="Team Captain (2x Points)">C</span>
          ) : isViceCaptain ? (
            <span className="vice-captain-badge" title="Vice Captain">V</span>
          ) : null}
          {strategyBadge === 'DIFF' && (
            <span className="diff-badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--accent-amber, #F59E0B)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '3px', padding: '0 4px', fontSize: '9px', fontWeight: 800 }} title="Differential pick — owned by under 20% of managers">⚡ DIFF</span>
          )}
          {strategyBadge === 'SHIELD' && (
            <span className="shield-badge" style={{ background: 'rgba(6, 182, 212, 0.2)', color: 'var(--accent-cyan, #06B6D4)', border: '1px solid rgba(6, 182, 212, 0.4)', borderRadius: '3px', padding: '0 4px', fontSize: '9px', fontWeight: 800 }} title="Popular pick — high ownership to protect your rank">🛡️ TEMPLATE</span>
          )}
          {isBoosted && player.is_bench_asset && (
            <span className="boost-badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald, #10B981)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '3px', padding: '0 4px', fontSize: '9px', fontWeight: 800 }} title="Bench Boost Active · Scoring points this gameweek">🚀 BB</span>
          )}
          <span className={`player-pos-tag ${pos}`}>{pos}</span>
          {isBgw && <span className="bgw-badge" title="Blank Gameweek: No game scheduled">BLANK</span>}
          {isDgw && <span className="dgw-badge" title="Double Gameweek: 2 games scheduled">DGW</span>}
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
          title="Click for match preview, win odds & clean sheet chances"
        >
          {player.team} {fixtureLabel && <span className="fixture-sub-tag font-mono">{fixtureLabel}</span>}
        </span>
      </div>

      {/* Minimalist Expected Points Score Banner */}
      <div className="player-stats-bar" style={{ justifyContent: 'center' }}>
        <span className="player-xp font-mono">
          {isTripleCaptain ? (xp * 3).toFixed(1) : isCaptain ? (xp * 2).toFixed(1) : xp.toFixed(1)} <span className="xp-unit">{isTripleCaptain ? 'pts (3x)' : isCaptain ? 'pts (2x)' : 'xP'}</span>
        </span>
      </div>
    </div>
  );
}
