import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend
} from 'recharts';
import {
  X,
  ChartBar,
  Polygon
} from '@phosphor-icons/react';
import { getPenaltyTierForTeam, DEFCON_BADGES } from '../constants/copyTokens';

export default function PlayerDNAInspector({ player, onClose }) {
  const [activeView, setActiveView] = useState('chart'); // 'chart' | 'radar'

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!player) return null;

  const xp = Number(player.dynamicXp || player.expected_points || 4.5);
  const pos = (player.position || 'MID').toUpperCase();

  // Extract or estimate granular component weights
  const xG90 = Number(
    player.bayesXg != null ? player.bayesXg :
    player.short_form_expected_goals_90 ??
    player.expected_goals_per_90 ??
    (pos === 'FWD' ? 0.45 : pos === 'MID' ? 0.22 : 0.05)
  );

  const xA90 = Number(
    player.bayesXa != null ? player.bayesXa :
    player.short_form_expected_assists_90 ??
    player.expected_assists_per_90 ??
    (pos === 'MID' ? 0.25 : pos === 'FWD' ? 0.15 : 0.08)
  );

  // Exact component extraction from model
  const c1_c2 = (player.c1_app_1_60 != null && player.c2_app_60_plus != null)
    ? Number((player.c1_app_1_60 + player.c2_app_60_plus).toFixed(2))
    : (pos === 'GK' ? 2.0 : 1.95);

  const c8_goals = player.c8_goals != null
    ? Number(player.c8_goals.toFixed(2))
    : Number((xG90 * (pos === 'FWD' ? 4 : (pos === 'MID' ? 5 : 6)) * 0.85).toFixed(2));

  const c7_assists = player.c7_assists != null
    ? Number(player.c7_assists.toFixed(2))
    : Number((xA90 * 3.0 * 0.85).toFixed(2));

  const c9_cleansheet = player.c9_clean_sheets != null
    ? Number(player.c9_clean_sheets.toFixed(2))
    : Number(((pos === 'GK' || pos === 'DEF') ? 1.45 : (pos === 'MID' ? 0.35 : 0.0)).toFixed(2));

  const c6_bonus = player.c6_bonus != null
    ? Number(player.c6_bonus.toFixed(2))
    : Number((Math.min(xp * 0.14, 1.25)).toFixed(2));

  const c3_saves = player.c3_saves != null
    ? Number(player.c3_saves.toFixed(2))
    : (pos === 'GK' ? 0.95 : 0.0);

  const c11_dc = player.c11_defensive_contributions != null
    ? Number(player.c11_defensive_contributions.toFixed(2))
    : 0.20;

  const c4_c5_cards = (player.c4_yellow_cards != null && player.c5_red_cards != null)
    ? Number((player.c4_yellow_cards + player.c5_red_cards).toFixed(2))
    : -0.10;

  const c10_gc_penalty = player.c10_goals_conceded != null
    ? Number(player.c10_goals_conceded.toFixed(2))
    : ((pos === 'GK' || pos === 'DEF') ? -0.45 : 0.0);

  const componentsData = [
    { name: 'Appearance (60+m)', value: Number(c1_c2.toFixed(2)), color: '#3B82F6', desc: 'Guaranteed 2 pts for 60+ minutes' },
    { name: 'Goal Threat (xG)', value: c8_goals, color: '#10B981', desc: `Based on ${xG90.toFixed(2)} xG/90` },
    { name: 'Assist Threat (xA)', value: c7_assists, color: '#06B6D4', desc: `Based on ${xA90.toFixed(2)} xA/90` },
    { name: 'Clean Sheet', value: c9_cleansheet, color: '#8B5CF6', desc: 'Defensive shutout probability' },
    { name: 'Bonus Points (BPS)', value: c6_bonus, color: '#F59E0B', desc: 'Simulated 3, 2, 1 BPS equity' },
    ...(pos === 'GK' || c3_saves > 0 ? [{ name: 'Goalkeeper Saves', value: c3_saves, color: '#EC4899', desc: 'Save point baseline' }] : []),
    { name: 'Defensive Actions', value: c11_dc, color: '#14B8A6', desc: 'Ball recoveries & tackles' },
    { name: 'Discipline Risk', value: c4_c5_cards, color: '#EF4444', desc: 'Yellow / red card deductions' },
    ...(c10_gc_penalty !== 0 ? [{ name: 'Goals Conceded', value: c10_gc_penalty, color: '#DC2626', desc: 'Deductions for 2+ goals conceded' }] : [])
  ];

  const pMins60 = player.p_mins_60 != null ? Math.round(player.p_mins_60 * 100) : 92;

  // 5-Axis Attribute Radar Data (Normalized 0-100 scale)
  const radarData = [
    {
      subject: 'Goal Threat',
      Player: Math.min(100, Math.round((xG90 / 0.60) * 100)),
      Baseline: pos === 'FWD' ? 70 : pos === 'MID' ? 40 : 15,
      fullMark: 100
    },
    {
      subject: 'Creativity',
      Player: Math.min(100, Math.round((xA90 / 0.40) * 100)),
      Baseline: pos === 'MID' ? 60 : pos === 'FWD' ? 40 : 20,
      fullMark: 100
    },
    {
      subject: 'Minutes Security',
      Player: Math.min(100, pMins60),
      Baseline: 75,
      fullMark: 100
    },
    {
      subject: 'Set-Pieces',
      Player: (player.sp_pk_order === 1 ? 50 : 0) + (player.sp_ck_order === 1 ? 30 : 0) + (player.sp_fk_order === 1 ? 20 : 0) || 15,
      Baseline: 25,
      fullMark: 100
    },
    {
      subject: 'Fixture Ease',
      Player: Math.min(100, Math.max(20, Math.round((5 - (player.fixture_fdr || 3)) * 25 + 25))),
      Baseline: 50,
      fullMark: 100
    }
  ];

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="dna-modal-title">
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '680px' }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '14px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`player-position-pill ${pos}`}>{pos}</span>
              <h2 id="dna-modal-title" style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                {player.web_name}
              </h2>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
              {player.team} · £{Number(player.now_cost || player.cost || 0).toFixed(1)}m · Projected: <span style={{ color: 'var(--accent-emerald)', fontWeight: 800 }}>{xp.toFixed(1)} pts</span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="modal-close-btn"
          >
            <X size={20} weight="bold" />
          </button>
        </div>

        {/* View Mode Segmented Switcher */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {activeView === 'chart' ? 'Expected Points Breakdown' : 'Player Strengths vs League Average'}
          </span>
          <div className="segmented-chip-rail">
            <button
              type="button"
              className={`segmented-chip-btn ${activeView === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveView('chart')}
            >
              <ChartBar size={12} weight="bold" />
              <span>Points Breakdown</span>
            </button>
            <button
              type="button"
              className={`segmented-chip-btn ${activeView === 'radar' ? 'active' : ''}`}
              onClick={() => setActiveView('radar')}
            >
              <Polygon size={12} weight="bold" />
              <span>Attribute Radar</span>
            </button>
          </div>
        </div>

        {/* Chart View: Diverging Horizontal Bar Chart */}
        {activeView === 'chart' ? (
          <div style={{ width: '100%', height: '240px', background: 'rgba(0,0,0,0.2)', padding: '12px 10px 6px 0', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={componentsData}
                layout="vertical"
                margin={{ top: 0, right: 30, left: 20, bottom: 0 }}
              >
                <XAxis
                  type="number"
                  stroke="var(--text-muted)"
                  fontSize={11}
                  domain={['dataMin', 'dataMax']}
                  tickLine={false}
                  axisLine={{ stroke: 'var(--border-subtle)' }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="var(--text-secondary)"
                  fontSize={11}
                  tickLine={false}
                  width={140}
                  axisLine={{ stroke: 'var(--border-subtle)' }}
                />
                <ReferenceLine x={0} stroke="rgba(255,255,255,0.25)" />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: 'var(--text-primary)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                  }}
                  formatter={(val) => [`${Number(val).toFixed(2)} pts`, 'Point Contribution']}
                />
                <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                  {componentsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          /* Radar View: 5-Axis Attribute Radar Polygon */
          <div style={{ width: '100%', height: '240px', background: 'rgba(0,0,0,0.2)', padding: '6px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                <PolarGrid stroke="rgba(255,255,255,0.12)" />
                <PolarAngleAxis dataKey="subject" stroke="var(--text-secondary)" fontSize={11} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-muted)" fontSize={9} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Radar name={player.web_name} dataKey="Player" stroke="#10B981" fill="#10B981" fillOpacity={0.4} />
                <Radar name="Positional Benchmark" dataKey="Baseline" stroke="#64748B" fill="#64748B" fillOpacity={0.15} strokeDasharray="3 3" />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Underlying Match Stats Grid */}
        <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
          Underlying Match Stats & Roles
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Goal Threat (xG per 90)</div>
            <div className="font-mono" style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
              {xG90.toFixed(2)}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Assist Threat (xA per 90)</div>
            <div className="font-mono" style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
              {xA90.toFixed(2)}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Starts & Plays 60+ Mins</div>
            <div className="font-mono" style={{ fontSize: '15px', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '2px' }}>
              {pMins60}%
            </div>
          </div>
        </div>

        {/* Tactical Hierarchy: Penalty Taker & Defcon Indicators */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Penalties & Set-Pieces</span>
              <span
                className="font-mono"
                style={{
                  fontSize: '9px',
                  fontWeight: 800,
                  background: 'rgba(239, 68, 68, 0.18)',
                  color: '#F87171',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '3px',
                  padding: '1px 5px'
                }}
              >
                {getPenaltyTierForTeam(player.team).badge}
              </span>
            </div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
              {player.sp_pk_order === 1 || player.penalties_order === 1 || player.web_name === 'B.Fernandes' || player.web_name === 'Haaland' || player.web_name === 'Palmer' || player.web_name === 'Salah'
                ? `First-choice penalty taker (${getPenaltyTierForTeam(player.team).desc})`
                : (player.sp_ck_order === 1 ? 'Takes corners and direct free-kicks' : 'Scores and creates from open play')}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Tackles & Recoveries (Defcon)</span>
              {(pos === 'DEF' || pos === 'GK') && (
                <span
                  className="font-mono"
                  style={{
                    fontSize: '9px',
                    fontWeight: 800,
                    background: 'rgba(59, 130, 246, 0.18)',
                    color: '#60A5FA',
                    border: '1px solid rgba(59, 130, 246, 0.4)',
                    borderRadius: '3px',
                    padding: '1px 5px'
                  }}
                >
                  DEFCON +5%
                </span>
              )}
            </div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
              {(pos === 'DEF' || pos === 'GK')
                ? 'Away match bonus: extra points from clearances, tackles, and ball recoveries.'
                : 'Wins balls high up the pitch to start attacks.'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '14px' }}>
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
