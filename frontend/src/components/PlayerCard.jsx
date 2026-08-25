import React from 'react';

export default function PlayerCard({ player, isSelected, onClick, onInspect }) {
  if (!player) return null;

  const isCaptain = player.is_captain;
  const isVice = player.is_vice_captain;

  // Derive specialty tags
  const tags = [];
  if (player.sp_pk_order === 1) tags.push('PK1');
  if (player.sp_ck_order === 1) tags.push('CK1');
  if (player.sp_fk_order === 1) tags.push('FK1');

  return (
    <div
      className={`player-card ${isCaptain ? 'is-captain' : ''} ${isVice ? 'is-vice' : ''} ${isSelected ? 'is-selected' : ''}`}
      onClick={onClick}
      onDoubleClick={() => onInspect && onInspect(player)}
      title="Click to swap / Double-click for 11-Component breakdown"
    >
      {/* Role Badges */}
      {isCaptain && <span className="player-role-badge captain">C</span>}
      {isVice && !isCaptain && <span className="player-role-badge vice">V</span>}

      {/* Position Tag */}
      <span className={`player-position-pill ${player.position}`}>
        {player.position}
      </span>

      {/* Player Web Name */}
      <div className="player-name">
        {player.web_name}
      </div>

      {/* Team & Cost */}
      <div className="player-team-cost">
        <span>{player.team}</span>
        <span>·</span>
        <span>£{Number(player.cost || 0).toFixed(1)}M</span>
      </div>

      {/* Stats & xP Pill */}
      <div className="player-stats-bar">
        <span className="player-xp font-mono">
          {Number(player.expected_points || 0).toFixed(2)} xP
        </span>
        {tags.length > 0 && (
          <div className="player-tags">
            {tags.map(t => (
              <span key={t} className="tag-badge">{t}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
