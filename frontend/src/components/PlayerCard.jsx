import React from 'react';
import {
  ShieldCheck,
  Warning,
  Lightning,
  Sparkle,
  TrendUp,
  Target
} from '@phosphor-icons/react';

export default function PlayerCard({
  player,
  onInspect,
  onOpenMatchup,
  onSelectSub,
  isSubTarget,
  isCaptain,
  isViceCaptain,
  compact = false
}) {
  if (!player) return null;

  // Extract quantitative risk / probability indicators
  const pMins60 = player.p_mins_60 != null ? Math.round(player.p_mins_60 * 100) : 92;
  const hookHazard = player.hook_hazard != null ? player.hook_hazard : 0.04;
  const haulProb = player.haul_prob != null ? Math.round(player.haul_prob * 100) : null;
  const p10 = player.floor_p10 != null ? Number(player.floor_p10).toFixed(1) : '1.5';
  const p50 = player.median_p50 != null ? Number(player.median_p50).toFixed(1) : Number(player.expected_points || 4.5).toFixed(1);
  const p90 = player.ceiling_p90 != null ? Number(player.ceiling_p90).toFixed(1) : (Number(player.expected_points || 4.5) * 2.2).toFixed(1);

  // Set-piece badges
  const setPieceTags = [];
  if (player.sp_pk_order === 1) setPieceTags.push({ label: 'PK1', title: '1st Choice Penalty Taker' });
  if (player.sp_ck_order === 1) setPieceTags.push({ label: 'CK1', title: '1st Choice Corner Taker' });
  if (player.sp_fk_order === 1) setPieceTags.push({ label: 'FK1', title: '1st Choice Direct Free-Kick Taker' });

  return (
    <div
      className={`player-pitch-card ${isSubTarget ? 'sub-target' : ''}`}
      onClick={() => onSelectSub && onSelectSub(player)}
      title="Click card to substitute or swap positions"
    >
      {/* Captain / Vice-Captain Flush Badge */}
      {isCaptain && (
        <div className="captain-badge" title="Active Team Captain (2x Points)">
          C
        </div>
      )}
      {isViceCaptain && !isCaptain && (
        <div className="vice-captain-badge" title="Vice Captain (backup if Captain DNPs)">
          V
        </div>
      )}

      {/* Card Header: Position Squircle Tag + Price */}
      <div className="player-card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span className={`player-pos-tag ${player.position}`}>
            {player.position}
          </span>
          {pMins60 >= 90 ? (
            <ShieldCheck size={11} weight="fill" color="var(--accent-emerald)" title="Nailed Starter (60+ mins safe)" />
          ) : hookHazard >= 0.12 ? (
            <Warning size={11} weight="fill" color="var(--accent-amber)" title="Early Hook Risk (sub-60 min substitution)" />
          ) : null}
        </div>
        <span className="player-cost-val font-mono">
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
        <div className="prob-range-labels font-mono">
          <span className="prob-floor" title="10th Percentile Floor (Worst Case)">FLR {p10}</span>
          <span className="prob-median" title="50th Percentile Median (Expected)">MED {p50}</span>
          <span className="prob-ceiling" title="90th Percentile Ceiling (Haul Outcome)">CEIL {p90}</span>
        </div>
        <div className="prob-range-track">
          <div
            className="prob-range-fill"
            style={{
              left: `${Math.min(30, (Number(p10) / 18) * 100)}%`,
              right: `${Math.max(0, 100 - (Number(p90) / 18) * 100)}%`
            }}
          />
          <div
            className="prob-median-dot"
            style={{
              left: `${Math.min(95, Math.max(5, (Number(p50) / 18) * 100))}%`
            }}
          />
        </div>
      </div>
    </div>
  );
}
