import React, { useState } from 'react';
import {
  UsersThree,
  ShieldCheck,
  ShieldWarning,
  Crown,
  TrendUp,
  CaretRight,
  ArrowsLeftRight,
  Sparkle
} from '@phosphor-icons/react';

export default function RivalThreatMatrix({
  managerProfile,
  starters = [],
  bench = []
}) {
  const rivals = managerProfile?.rivals || [];
  const [selectedRival, setSelectedRival] = useState(rivals[0] || null);

  const myCaptain = starters.find(p => p.is_captain)?.web_name || 'Haaland';

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
                        background: isSelected ? 'rgba(16, 185, 129, 0.08)' : 'transparent'
                      }}
                    >
                      <td className="font-mono" style={{ fontWeight: 700 }}>
                        #{r.overall_rank}
                      </td>
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.manager_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.team_name}</div>
                      </td>
                      <td className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        {r.overall_points} pts
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span style={{ fontWeight: 600 }}>{r.captain_name}</span>
                          {isSameCaptain ? (
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>(Neutralized)</span>
                          ) : (
                            <span style={{ fontSize: '10px', color: 'var(--accent-crimson)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>⚡ Swing Risk</span>
                          )}
                        </div>
                      </td>
                      <td className="font-mono">
                        {r.overlap_pct}%
                      </td>
                      <td>
                        <span
                          className="status-pill"
                          style={{
                            background: r.threat_level === 'HIGH' ? 'rgba(239, 68, 68, 0.15)' : r.threat_level === 'MEDIUM' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: r.threat_level === 'HIGH' ? 'var(--accent-crimson)' : r.threat_level === 'MEDIUM' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                            fontSize: '10px',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: 'var(--radius-xs)'
                          }}
                        >
                          {r.threat_level}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn-select-rival"
                          style={{
                            background: isSelected ? 'var(--accent-emerald)' : 'var(--bg-surface-subtle)',
                            color: isSelected ? 'var(--text-inverse)' : 'var(--text-secondary)',
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
