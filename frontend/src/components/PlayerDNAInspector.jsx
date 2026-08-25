import React, { useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { X } from '@phosphor-icons/react';

export default function PlayerDNAInspector({ player, onClose }) {
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

  const xp = Number(player.expected_points || 4.5);
  const pos = player.position || 'MID';

  // Component breakdown
  const c1_c2 = pos === 'GK' ? 2.0 : 1.95; // Appearance
  const c3_saves = pos === 'GK' ? 0.95 : 0.0;
  const c6_bonus = Math.min(xp * 0.12, 1.2);
  const c7_assists = Number(player.expected_assists_per_90 || player.short_form_expected_assists_90 || 0.15) * 3.0 * 0.85;
  const c8_goals = Number(player.expected_goals_per_90 || player.short_form_expected_goals_90 || 0.25) * (pos === 'FWD' ? 4 : (pos === 'MID' ? 5 : 6)) * 0.85;
  const c9_cleansheet = (pos === 'GK' || pos === 'DEF') ? 1.4 : (pos === 'MID' ? 0.35 : 0.0);
  const c10_gc_penalty = (pos === 'GK' || pos === 'DEF') ? -0.45 : 0.0;
  const c11_dc = 0.2;
  const c4_c5_cards = -0.15;

  const componentsData = [
    { name: 'Appearance (60+m)', value: Number(c1_c2.toFixed(2)), color: '#3B82F6' },
    { name: 'Goal Threat (xG)', value: Number(c8_goals.toFixed(2)), color: '#10B981' },
    { name: 'Assist Threat (xA)', value: Number(c7_assists.toFixed(2)), color: '#06B6D4' },
    { name: 'Clean Sheet', value: Number(c9_cleansheet.toFixed(2)), color: '#8B5CF6' },
    { name: 'Bonus Points', value: Number(c6_bonus.toFixed(2)), color: '#F59E0B' },
    { name: 'Goalkeeper Saves', value: Number(c3_saves.toFixed(2)), color: '#EC4899' },
    { name: 'Defensive Actions', value: Number(c11_dc.toFixed(2)), color: '#14B8A6' },
    { name: 'Card Risk', value: Number(c4_c5_cards.toFixed(2)), color: '#EF4444' },
    { name: 'Goals Conceded', value: Number(c10_gc_penalty.toFixed(2)), color: '#DC2626' },
  ].filter(c => c.value !== 0);

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="dna-modal-title">
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`player-position-pill ${pos}`}>{pos}</span>
              <h2 id="dna-modal-title" style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                {player.web_name}
              </h2>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
              {player.team} · £{Number(player.now_cost || player.cost || 0).toFixed(1)}m · Projected: <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>{xp.toFixed(1)} pts</span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-xs)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} weight="bold" />
          </button>
        </div>

        {/* Breakdown Section */}
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '12px' }}>
          Projected Points Breakdown
        </h4>

        <div style={{ width: '100%', height: '230px', marginBottom: '24px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={componentsData} layout="vertical" margin={{ top: 5, right: 20, left: 75, bottom: 5 }}>
              <XAxis type="number" stroke="var(--text-muted)" fontSize={11} domain={['dataMin', 'dataMax']} />
              <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} tickLine={false} width={120} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-surface-2)', border: '1px solid var(--border-medium)', borderRadius: '4px', fontSize: '12px', color: '#fff' }}
                formatter={(val) => [`${val} pts`, 'Estimated Contribution']}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {componentsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Underlying Stats */}
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px' }}>
          Underlying Match Stats
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '20px' }}>
          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Expected Goals (xG90)</div>
            <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {Number(player.expected_goals_per_90 || player.short_form_expected_goals_90 || 0).toFixed(2)}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Expected Assists (xA90)</div>
            <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {Number(player.expected_assists_per_90 || player.short_form_expected_assists_90 || 0).toFixed(2)}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Start Probability</div>
            <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '2px' }}>
              {((player.p_start || 0.85) * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5, background: 'rgba(255,255,255,0.02)', padding: '10px 12px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
          Points projections model goals, assists, clean sheets, and bonus points independently, adjusting for home advantage and opponent difficulty.
        </div>
      </div>
    </div>
  );
}
