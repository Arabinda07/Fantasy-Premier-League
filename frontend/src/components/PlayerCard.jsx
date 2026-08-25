import React from 'react';
import {
  ShieldCheck,
  Warning,
  Lightning,
  Sparkle,
  Target,
  ChartBar
} from '@phosphor-icons/react';

export default function PlayerCard({
  player,
  isSelected,
  onClick,
  onInspect,
  onOpenMatchup
}) {
  if (!player) return null;

  const isCaptain = player.is_captain;
  const isVice = player.is_vice_captain;

  // Set-piece badges
  const setPieceTags = [];
  if (player.sp_pk_order === 1) setPieceTags.push({ label: 'PK', title: 'Primary Penalty Taker' });
  if (player.sp_ck_order === 1) setPieceTags.push({ label: 'CK', title: 'Corner Delivery Specialist' });
  if (player.sp_fk_order === 1) setPieceTags.push({ label: 'FK', title: 'Direct Free-Kick Taker' });

  // Probability percentiles
  const p10 = player.floor_p10 != null ? player.floor_p10 : Math.max(1, (player.expected_points * 0.35)).toFixed(1);
  const p50 = player.median_p50 != null ? player.median_p50 : (player.expected_points * 0.95).toFixed(1);
  const p90 = player.ceiling_p90 != null ? player.ceiling_p90 : (player.expected_points * 1.8).toFixed(1);
  const haulProb = player.haul_prob != null ? Math.round(player.haul_prob * 100) : null;

  // Minutes security
  const pMins60 = player.p_mins_60 != null ? Math.round(player.p_mins_60 * 100) : 90;
  const hookHazard = player.hook_hazard != null ? player.hook_hazard : 0.02;

  const handleClick = (e) => {
    if (e.detail === 2 && onInspect) {
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
      title="Click to swap · Click 'Stats' for points breakdown"
    >
      {/* Role Badges */}
      {isCaptain && <span className="player-role-badge captain" title="Captain (2x Points)">C</span>}
      {isVice && !isCaptain && <span className="player-role-badge vice" title="Vice Captain">V</span>}

      {/* Position Header & Price */}
      <div className="player-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span className={`player-position-pill ${player.position}`}>
            {player.position}
          </span>
          {pMins60 >= 90 ? (
            <ShieldCheck size={11} weight="fill" color="var(--accent-emerald)" title="Nailed Starter (60+ mins safe)" />
          ) : hookHazard >= 0.12 ? (
            <Warning size={11} weight="fill" color="var(--accent-amber)" title="Early Hook Risk (sub-60 min substitution)" />
          ) : null}
        </div>
        <span className="player-cost-val">
          £{Number(player.cost || 0).toFixed(1)}m
        </span>
      </div>

      {/* Player Name */}
      <div className="player-name">
        {player.web_name}
      </div>

      {/* Team & Dead-Ball Tags */}
      <div className="player-team-row">
        <span
          className="player-team-tag"
          onClick={(e) => {
            if (onOpenMatchup && player.fixture_details) {
              e.stopPropagation();
              onOpenMatchup(player.fixture_details);
            }
          }}
          title="Click to view match preview & clean sheet odds"
        >
          {player.team}
        </span>

        {/* Set-Piece Badges */}
        <div className="set-piece-pills">
          {setPieceTags.map(tag => (
            <span key={tag.label} className="sp-pill" title={tag.title}>
              {tag.label}
            </span>
          ))}
        </div>
      </div>

      {/* Main Expected Points Banner with Direct Stats Button */}
      <div className="player-stats-bar">
        <span className="player-xp font-mono">
          {Number(player.expected_points || 0).toFixed(1)} <span className="xp-unit">xP</span>
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {haulProb && haulProb >= 20 && (
            <span className="haul-badge" title="Haul Potential: Chance of scoring 10+ points">
              <Lightning size={9} weight="fill" />
              <span>{haulProb}%</span>
            </span>
          )}
          {onInspect && (
            <button
              type="button"
              className="card-stats-btn"
              onClick={(e) => {
                e.stopPropagation();
                onInspect(player);
              }}
              title="Open full points breakdown"
            >
              Stats
            </button>
          )}
        </div>
      </div>

      {/* 3-Tier Probability Distribution Range Bar (Floor | Median | Ceiling) */}
      <div
        className="prob-range-container"
        onClick={(e) => {
          if (onInspect) {
            e.stopPropagation();
            onInspect(player);
          }
        }}
        title={`Click for breakdown · Floor (Worst Case): ${p10} pts | Median (Expected): ${p50} pts | Ceiling (Haul): ${p90} pts`}
      >
        <div className="prob-range-labels">
          <span className="prob-floor">{p10}</span>
          <span className="prob-median">{p50}</span>
          <span className="prob-ceiling">{p90}</span>
        </div>
        <div className="prob-range-track">
          <div
            className="prob-range-fill"
            style={{
              left: `${Math.min(30, (p10 / 18) * 100)}%`,
              right: `${Math.max(0, 100 - (p90 / 18) * 100)}%`
            }}
          />
          <div
            className="prob-median-dot"
            style={{
              left: `${Math.min(95, Math.max(5, (p50 / 18) * 100))}%`
            }}
          />
        </div>
      </div>
    </div>
  );
}
