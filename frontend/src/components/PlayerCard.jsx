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
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`Select ${player.web_name}, ${player.position}, cost £${Number(player.cost || 0).toFixed(1)}M, ${Number(player.expected_points || 0).toFixed(2)} expected points`}
      title="Click to select/swap · Click [DNA] to inspect"
    >
      {/* Role Badges */}
      {isCaptain && <span className="player-role-badge captain">C</span>}
      {isVice && !isCaptain && <span className="player-role-badge vice">V</span>}

      {/* Position & Inspect Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
        <span className={`player-position-pill ${player.position}`}>
          {player.position}
        </span>
        {onInspect && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onInspect(player);
            }}
            aria-label={`Inspect ${player.web_name} DNA statistics`}
            style={{
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--accent-emerald)',
              fontSize: '9px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '1px 4px',
              borderRadius: 'var(--radius-xs)',
              cursor: 'pointer'
            }}
            title="Inspect 11-Component DNA"
          >
            DNA
          </button>
        )}
      </div>

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
