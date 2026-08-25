import React from 'react';

export default function PlayerCard({ player, isSelected, onClick, onInspect }) {
  if (!player) return null;

  const isCaptain = player.is_captain;
  const isVice = player.is_vice_captain;

  // Set-piece duty tags
  const tags = [];
  if (player.sp_pk_order === 1) tags.push('Penalties');
  if (player.sp_ck_order === 1) tags.push('Corners');
  if (player.sp_fk_order === 1) tags.push('Free Kicks');

  const handleClick = (e) => {
    if (e.detail === 2 && onInspect) {
      // Double click directly opens player breakdown
      onInspect(player);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`player-card ${isCaptain ? 'is-captain' : ''} ${isVice ? 'is-vice' : ''} ${isSelected ? 'is-selected' : ''}`}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (onClick) onClick();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`${player.web_name}, ${player.position}, £${Number(player.cost || 0).toFixed(1)}M, ${Number(player.expected_points || 0).toFixed(1)} expected points`}
      title="Click to swap · Double-click for points breakdown"
    >
      {/* Role Badges */}
      {isCaptain && <span className="player-role-badge captain">C</span>}
      {isVice && !isCaptain && <span className="player-role-badge vice">V</span>}

      {/* Position Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
        <span className={`player-position-pill ${player.position}`}>
          {player.position}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          £{Number(player.cost || 0).toFixed(1)}m
        </span>
      </div>

      {/* Player Name */}
      <div className="player-name">
        {player.web_name}
      </div>

      {/* Team */}
      <div className="player-team-cost">
        <span>{player.team}</span>
        {tags.length > 0 && <span>· {tags[0]}</span>}
      </div>

      {/* Projected Points Bar */}
      <div className="player-stats-bar">
        <span className="player-xp font-mono">
          {Number(player.expected_points || 0).toFixed(1)} pts
        </span>
        {onInspect && (
          <span
            onClick={(e) => {
              e.stopPropagation();
              onInspect(player);
            }}
            style={{
              fontSize: '9px',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: '1px 3px'
            }}
            title="View breakdown"
          >
            Stats
          </span>
        )}
      </div>
    </div>
  );
}
