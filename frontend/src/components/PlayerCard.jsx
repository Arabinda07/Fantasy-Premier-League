import React from 'react';
import { getPenaltyTierForTeam, AUTO_SUB_LABELS } from '../constants/copyTokens';

// Map Premier League team names to kit stripe identifiers
const getTeamKitClass = (teamName) => {
  const t = (teamName || '').toLowerCase().replace(/[^a-z]/g, '');
  if (t.includes('arsenal')) return 'kit-arsenal';
  if (t.includes('aston') || t.includes('villa')) return 'kit-aston-villa';
  if (t.includes('bournemouth')) return 'kit-bournemouth';
  if (t.includes('brentford')) return 'kit-brentford';
  if (t.includes('brighton')) return 'kit-brighton';
  if (t.includes('chelsea')) return 'kit-chelsea';
  if (t.includes('palace')) return 'kit-crystal-palace';
  if (t.includes('everton')) return 'kit-everton';
  if (t.includes('fulham')) return 'kit-fulham';
  if (t.includes('ipswich')) return 'kit-ipswich';
  if (t.includes('leicester')) return 'kit-leicester';
  if (t.includes('liverpool')) return 'kit-liverpool';
  if (t.includes('city') || t.includes('mancity')) return 'kit-man-city';
  if (t.includes('utd') || t.includes('united') || t.includes('manutd')) return 'kit-man-utd';
  if (t.includes('newcastle')) return 'kit-newcastle';
  if (t.includes('nottingham') || t.includes('forest')) return 'kit-nottingham-forest';
  if (t.includes('southampton')) return 'kit-southampton';
  if (t.includes('tottenham') || t.includes('spurs')) return 'kit-tottenham';
  if (t.includes('westham')) return 'kit-west-ham';
  if (t.includes('wolves')) return 'kit-wolves';
  return 'kit-generic';
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

  // Set-Piece & Penalty Hierarchy Detection
  const isPenaltyTaker = player.sp_pk_order === 1 || player.penalties_order === 1 || player.is_penalty_taker || (player.web_name === 'B.Fernandes' || player.web_name === 'Haaland' || player.web_name === 'Palmer' || player.web_name === 'Salah' || player.web_name === 'Saka' || player.web_name === 'Mbeumo');
  const penaltyTier = isPenaltyTaker ? getPenaltyTierForTeam(player.team) : null;

  // Determine whether to display actual match points or forward expected points
  const hasActualPoints = player.actual_points !== undefined;
  const basePts = hasActualPoints ? Number(player.actual_points) : xp;
  const mult = isTripleCaptain ? 3 : (isCaptain ? 2 : 1);
  const displayPts = hasActualPoints
    ? (basePts * mult)
    : (mult > 1 ? (xp * mult).toFixed(1) : xp.toFixed(1));
  const unit = hasActualPoints
    ? (mult > 1 ? `pts (${mult}x)` : 'pts')
    : (mult > 1 ? `pts (${mult}x)` : 'xP');

  const kitClass = getTeamKitClass(player.team);

  return (
    <div
      className={`player-pitch-card ${kitClass} ${isSubTarget ? 'sub-target' : ''} ${isBoosted ? 'bench-boosted' : ''} ${isBgw ? 'is-bgw' : ''} ${isDgw ? 'is-dgw' : ''} ${hasActualPoints ? 'has-actuals' : ''}`}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
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
          {/* M-02: Rotation/Hook Risk Indicator */}
          {player.hook_hazard > 0.15 && (
            <span style={{ color: 'var(--accent-amber, #F59E0B)', fontSize: '10px', fontWeight: 800, lineHeight: 1 }} title={`${Math.round(player.hook_hazard * 100)}% early sub risk`}>⚠</span>
          )}
          {isBgw && <span className="bgw-badge" title="Blank Gameweek: No game scheduled">BLANK</span>}
          {isDgw && <span className="dgw-badge" title="Double Gameweek: 2 games scheduled">DGW</span>}
          {/* M-06: Auto-Sub Priority Label for bench players */}
          {player.auto_sub_label && AUTO_SUB_LABELS[player.auto_sub_label] && (
            <span
              style={{
                fontSize: '8px',
                fontWeight: 800,
                padding: '0 3px',
                borderRadius: '2px',
                lineHeight: '1.3',
                background: player.auto_sub_label === 'HIGH' ? 'rgba(16, 185, 129, 0.2)' : player.auto_sub_label === 'MEDIUM' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                color: player.auto_sub_label === 'HIGH' ? 'var(--accent-emerald, #10B981)' : player.auto_sub_label === 'MEDIUM' ? 'var(--accent-amber, #F59E0B)' : 'var(--text-muted)',
                border: `1px solid ${player.auto_sub_label === 'HIGH' ? 'rgba(16, 185, 129, 0.4)' : player.auto_sub_label === 'MEDIUM' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(100, 116, 139, 0.3)'}`,
              }}
              title={AUTO_SUB_LABELS[player.auto_sub_label].tooltip}
            >
              {AUTO_SUB_LABELS[player.auto_sub_label].badge}
            </span>
          )}
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

      {/* Tactical Spot-Kick Hierarchy (if primary taker) */}
      {penaltyTier && (
        <div className="player-tactical-badges-strip" style={{ display: 'flex', justifyContent: 'center', margin: '3px 0 2px 0' }}>
          <span
            className="pk-tier-badge font-mono"
            style={{
              background: 'rgba(239, 68, 68, 0.18)',
              color: '#F87171',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '3px',
              padding: '0 3px',
              fontSize: '8px',
              fontWeight: 800,
              letterSpacing: '0.02em',
              lineHeight: '1.2'
            }}
            title={penaltyTier.tooltip}
          >
            {penaltyTier.badge}
          </span>
        </div>
      )}

      {/* Points Banner (Actual Points for Completed GWs / Expected Points for Upcoming) */}
      <div className="player-stats-bar" style={{ justifyContent: 'center', gap: '6px' }}>
        <span className="player-xp font-mono" style={hasActualPoints ? { color: 'var(--accent-emerald, #10B981)', fontWeight: 800 } : {}}>
          {displayPts} <span className="xp-unit">{unit}</span>
        </span>
        {hasActualPoints && Number(player.actual_bonus) > 0 && (
          <span
            className="font-mono"
            style={{
              fontSize: '9px',
              background: 'rgba(245, 158, 11, 0.2)',
              color: 'var(--accent-amber, #F59E0B)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              borderRadius: '2px',
              padding: '0 3px',
              fontWeight: 700
            }}
            title={`${player.actual_bonus} Bonus Points Awarded`}
          >
            +{player.actual_bonus}
          </span>
        )}
      </div>
    </div>
  );
}


