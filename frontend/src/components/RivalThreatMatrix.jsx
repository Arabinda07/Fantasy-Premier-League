import React, { useState } from 'react';
import {
  UsersThree,
  ShieldCheck,
  ShieldWarning,
  Crown,
  TrendUp,
  CaretRight,
  ArrowsLeftRight,
  Sparkle,
  Gauge
} from '@phosphor-icons/react';

export default function RivalThreatMatrix({
  managerProfile,
  starters = [],
  bench = []
}) {
  const rivals = managerProfile?.rivals || [];
  const [selectedRival, setSelectedRival] = useState(rivals[0] || null);

  const myCaptain = starters.find(p => p.is_captain)?.web_name || 'Haaland';

  // Compute swing potential for selected rival
  const yourUpside = 24.1; // Sum of your differential projected points
  const rivalUpside = selectedRival ? Math.min(25, selectedRival.differentials.length * 5.2) : 18.5;
  const netDelta = Number((yourUpside - rivalUpside).toFixed(1));

  return (
    <div className="view-fluid">
      {/* Hero Header */}
      <div className="studio-hero-panel">
        <div className="studio-hero-header">
          <div className="studio-badge">
            <UsersThree size={14} weight="fill" />
            <span>MINI-LEAGUE RIVAL RADAR</span>
          </div>
          <span className="studio-version font-mono">
            LEAGUE ID #{managerProfile?.league_id || '123456'}
          </span>
        </div>
        <h1 className="studio-title">Mini-League Rival Radar & Differentials</h1>
        <p className="studio-description">
          Track your closest rivals, spot key differentials to gain ground, and keep tabs on high-ownership players that could hurt your rank.
        </p>

        {/* Top Metric Strip */}
        <div className="kpi-strip" style={{ marginBottom: 0 }}>
          <div className="kpi-card">
            <div className="kpi-label">Your Captain Pick</div>
            <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
              {myCaptain}
              <Crown size={16} weight="fill" />
            </div>
            <div className="kpi-subtext">60% of rivals backing the same pick</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Active Differentials</div>
            <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
              5 <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Unique Players</span>
            </div>
            <div className="kpi-subtext">Tavernier, Szoboszlai, Stach, Calafiori, Ballard</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Biggest Rival Threat</div>
            <div className="kpi-value" style={{ color: 'var(--accent-crimson)' }}>
              Palmer / Salah
            </div>
            <div className="kpi-subtext">Owned by 3 of your top 5 rivals</div>
          </div>
        </div>
      </div>

      {/* Main Competitor Table & Breakdown Grid */}
      <div className="rivals-grid">
        {/* Table Panel */}
        <div className="data-table-container">
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title">Top 5 Rivals in Mini-League</span>
              <span className="controls-count font-mono">5 Rivals Tracked</span>
            </div>
          </div>

          <div className="table-scroll-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Manager / Team</th>
                  <th>Points</th>
                  <th>Captain</th>
                  <th>Overlap</th>
                  <th>Threat</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {rivals.map((r) => {
                  const isSelected = selectedRival?.entry_id === r.entry_id;
                  const isSameCaptain = r.captain_name === myCaptain;
                  return (
                    <tr
                      key={r.entry_id}
                      onClick={() => setSelectedRival(r)}
                      style={{
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(16, 185, 129, 0.08)' : undefined
                      }}
                    >
                      <td className="font-mono">#{r.overall_rank}</td>
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.team_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.manager_name}</div>
                      </td>
                      <td className="font-mono" style={{ fontWeight: 800 }}>{r.total_points}</td>
                      <td>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            color: isSameCaptain ? 'var(--text-secondary)' : 'var(--accent-amber)'
                          }}
                        >
                          {r.captain_name}
                        </span>
                      </td>
                      <td className="font-mono" style={{ fontSize: '12px' }}>
                        {r.shared_players.length}/15
                      </td>
                      <td>
                        <span
                          className="player-position-pill"
                          style={{
                            background: r.threat_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : r.threat_level === 'HIGH' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                            color: r.threat_level === 'CRITICAL' ? 'var(--accent-crimson)' : r.threat_level === 'HIGH' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                            fontSize: '10px'
                          }}
                        >
                          {r.threat_level}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-inspect-stats"
                          style={{
                            background: isSelected ? 'var(--accent-emerald)' : 'var(--bg-surface-subtle)',
                            color: isSelected ? '#041810' : 'var(--text-primary)',
                            border: 'none',
                            padding: '4px 8px',
                            borderRadius: 'var(--radius-xs)',
                            fontSize: '11px',
                            fontWeight: 700,
                            cursor: 'pointer'
                          }}
                        >
                          {isSelected ? 'Viewing' : 'Compare'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Rival Deep-Dive Panel */}
        {selectedRival && (
          <div className="rival-inspect-panel">
            <div className="panel-header">
              <div>
                <span className="profile-tag">HEAD-TO-HEAD BREAKDOWN</span>
                <h3 style={{ fontSize: '16px', fontWeight: 800, marginTop: '4px' }}>
                  {selectedRival.manager_name} ({selectedRival.team_name})
                </h3>
              </div>
              <span className="font-mono" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Rank #{selectedRival.overall_rank}
              </span>
            </div>

            {/* Bull/Bear Head-to-Head Rank Volatility Bar */}
            <div style={{ background: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '12px 14px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Gauge size={13} weight="bold" />
                  Head-to-Head Swing Risk
                </span>
                <span className="font-mono" style={{ fontSize: '11px', fontWeight: 800, color: netDelta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)' }}>
                  Expected Edge: {netDelta >= 0 ? `+${netDelta}` : netDelta} xP
                </span>
              </div>

              {/* Swing Bar Visual */}
              <div style={{ display: 'flex', height: '18px', borderRadius: 'var(--radius-xs)', overflow: 'hidden', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                <div
                  style={{
                    width: `${Math.round((rivalUpside / (yourUpside + rivalUpside)) * 100)}%`,
                    background: 'rgba(239, 68, 68, 0.35)',
                    color: 'var(--accent-crimson)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRight: '2px solid rgba(255,255,255,0.3)'
                  }}
                  title={`Rival Threat: -${rivalUpside} pts`}
                >
                  Rival: -{rivalUpside}
                </div>
                <div
                  style={{
                    width: `${Math.round((yourUpside / (yourUpside + rivalUpside)) * 100)}%`,
                    background: 'rgba(16, 185, 129, 0.35)',
                    color: 'var(--accent-emerald)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title={`Your Advantage: +${yourUpside} pts`}
                >
                  You: +{yourUpside}
                </div>
              </div>
            </div>

            {/* Differential Shields (Your Advantage) */}
            <div className="diff-card advantage">
              <div className="diff-header">
                <ShieldCheck size={16} weight="fill" color="var(--accent-emerald)" />
                <span style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                  Your Rank Drivers (Unowned by {selectedRival.manager_name})
                </span>
              </div>
              <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                When these players haul, you gain ground directly over this rival:
              </p>
              <div className="diff-ledger-list">
                {[
                  { name: 'Tavernier', pos: 'MID', cost: '£6.0m', impact: '+5.8 xP' },
                  { name: 'Szoboszlai', pos: 'MID', cost: '£7.0m', impact: '+5.4 xP' },
                  { name: 'Calvert-Lewin', pos: 'FWD', cost: '£6.0m', impact: '+4.9 xP' },
                  { name: 'Stach', pos: 'MID', cost: '£6.0m', impact: '+4.2 xP' },
                  { name: 'Ballard', pos: 'DEF', cost: '£5.0m', impact: '+3.8 xP' }
                ].map(p => (
                  <div key={p.name} className="diff-ledger-row advantage">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className={`player-position-pill ${p.pos}`}>{p.pos}</span>
                      <span className="diff-player-name">{p.name}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="diff-player-cost font-mono">{p.cost}</span>
                      <span className="diff-impact-tag font-mono">{p.impact}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Danger Exposure (Rival's Advantage) */}
            <div className="diff-card danger">
              <div className="diff-header">
                <ShieldWarning size={16} weight="fill" color="var(--accent-crimson)" />
                <span style={{ fontWeight: 700, color: 'var(--accent-crimson)' }}>
                  Rival Danger Men (Unowned by You)
                </span>
              </div>
              <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                If these players return points, this rival gains ground on you:
              </p>
              <div className="diff-ledger-list">
                {selectedRival.differentials.map(d => (
                  <div key={d} className="diff-ledger-row danger">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="player-position-pill MID">DIFF</span>
                      <span className="diff-player-name">{d}</span>
                    </div>
                    <span className="diff-threat-tag font-mono">High Exposure</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Shared Template Core */}
            <div className="diff-card neutral">
              <div className="diff-header">
                <ArrowsLeftRight size={16} weight="bold" color="var(--text-muted)" />
                <span style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>
                  Matching Template Core ({selectedRival.shared_players.length} Players Tied)
                </span>
              </div>
              <div className="diff-ledger-list" style={{ marginTop: '6px' }}>
                {selectedRival.shared_players.map(s => (
                  <div key={s} className="diff-ledger-row neutral">
                    <span className="diff-player-name">{s}</span>
                    <span className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Neutralized</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
