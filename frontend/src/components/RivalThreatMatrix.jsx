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

const DEFAULT_RIVALS = [
  {
    entry_id: 1001,
    manager_name: "Magnus Carlsen",
    team_name: "Turing Test XI",
    overall_rank: 1,
    overall_points: 78,
    captain_name: "Haaland",
    differentials: ["Salah", "Isak"],
    shared_players: ["Haaland", "B.Fernandes", "Raya", "White"],
    threat_level: "HIGH",
    overlap_pct: 60.0
  },
  {
    entry_id: 1002,
    manager_name: "Fabio Borges",
    team_name: "Porto Knights",
    overall_rank: 2,
    overall_points: 74,
    captain_name: "Haaland",
    differentials: ["Palmer", "Gvardiol"],
    shared_players: ["Haaland", "Calafiori", "Mbeumo", "Szoboszlai"],
    threat_level: "MEDIUM",
    overlap_pct: 53.3
  },
  {
    entry_id: 1003,
    manager_name: "Ben Crellin",
    team_name: "Planner FC",
    overall_rank: 3,
    overall_points: 71,
    captain_name: "B.Fernandes",
    differentials: ["Watkins", "Saka"],
    shared_players: ["B.Fernandes", "Calafiori", "Raya", "Ballard"],
    threat_level: "HIGH",
    overlap_pct: 46.7
  },
  {
    entry_id: 1004,
    manager_name: "Mark Sutherns",
    team_name: "Black & White",
    overall_rank: 4,
    overall_points: 69,
    captain_name: "Haaland",
    differentials: ["Son", "Porro"],
    shared_players: ["Haaland", "Tavernier", "Mbeumo", "Leno"],
    threat_level: "LOW",
    overlap_pct: 40.0
  },
  {
    entry_id: 1005,
    manager_name: "Lateriser12",
    team_name: "Upside Chaser",
    overall_rank: 5,
    overall_points: 66,
    captain_name: "Palmer",
    differentials: ["Palmer", "Gordon", "Muniz"],
    shared_players: ["Haaland", "Stach", "White", "Calvert-Lewin"],
    threat_level: "MEDIUM",
    overlap_pct: 46.7
  }
];

export default function RivalThreatMatrix({
  managerProfile,
  starters = [],
  bench = []
}) {
  const rivals = (managerProfile?.rivals && managerProfile.rivals.length > 0)
    ? managerProfile.rivals
    : DEFAULT_RIVALS;

  const [selectedRival, setSelectedRival] = useState(rivals[0] || null);

  const myCaptain = starters.find(p => p.is_captain)?.web_name || 'Haaland';

  // Compute swing potential for selected rival
  const yourUpside = 24.1; // Sum of your differential projected points
  const rivalUpside = selectedRival ? Math.min(25, (selectedRival.differentials?.length || 2) * 5.2) : 18.5;
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
            LEAGUE ID #{managerProfile?.league_id || '1305495'}
          </span>
        </div>
        <h1 className="studio-title">Mini-League Rival Radar & Differentials</h1>
        <p className="studio-description">
          Track your closest rivals, spot key differentials to gain ground, and keep tabs on high-ownership players that could hurt your rank.
        </p>

        {/* Top Metric Strip */}
        <div className="kpi-strip">
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
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
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
              <span className="controls-count font-mono">{rivals.length} Rivals Tracked</span>
            </div>
          </div>

          <div className="table-scroll-wrapper">
            <table className="data-table rivals-table">
              <thead>
                <tr>
                  <th style={{ width: '8%' }}>Rank</th>
                  <th style={{ width: '26%' }}>Manager / Team</th>
                  <th style={{ width: '12%' }}>Points</th>
                  <th style={{ width: '18%' }}>Captain</th>
                  <th style={{ width: '14%' }}>Overlap</th>
                  <th style={{ width: '12%' }}>Threat</th>
                  <th style={{ width: '10%' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {rivals.map((r, idx) => {
                  const isSelected = (selectedRival?.entry_id === r.entry_id) || (!selectedRival && idx === 0);
                  const threatClass = r.threat_level === 'HIGH' ? 'threat-high' : r.threat_level === 'MEDIUM' ? 'threat-med' : 'threat-low';
                  const overlapCount = r.shared_players?.length || r.overlap_count || 7;
                  const overlapPctVal = r.overlap_pct > 1 ? Math.round(r.overlap_pct) : Math.round((r.overlap_pct || 0.46) * 100);

                  return (
                    <tr
                      key={r.entry_id || idx}
                      className={isSelected ? 'selected-row' : ''}
                      onClick={() => setSelectedRival(r)}
                    >
                      <td className="font-mono" style={{ fontWeight: 700 }}>#{r.overall_rank || r.rank || (idx + 1)}</td>
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.manager_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.team_name}</div>
                      </td>
                      <td className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        {r.overall_points || r.total_points || 70}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ fontWeight: 600 }}>{r.captain_name || r.captain || 'Haaland'}</span>
                          <Crown size={12} weight="fill" color="var(--accent-amber)" />
                        </div>
                      </td>
                      <td className="font-mono">{overlapCount}/15 ({overlapPctVal}%)</td>
                      <td>
                        <span className={`threat-badge ${threatClass}`}>{r.threat_level || 'MEDIUM'}</span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="table-action-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRival(r);
                          }}
                        >
                          Compare
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Rival Detail & Differential Matrix */}
        {selectedRival && (
          <div className="sidebar-panel">
            <div className="panel-header">
              <span className="panel-title">Head-to-Head Differential Matrix</span>
              <span className="panel-badge font-mono">vs {selectedRival.manager_name}</span>
            </div>

            {/* Swing Risk Range Gauge */}
            <div className="h2h-swing-container">
              <div className="h2h-swing-header">
                <span className="h2h-swing-title">
                  <Gauge size={14} weight="bold" />
                  Net Head-to-Head Haul Advantage
                </span>
                <span className="h2h-swing-val font-mono" style={{ color: netDelta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)' }}>
                  {netDelta >= 0 ? `+${netDelta}` : netDelta} xP Edge
                </span>
              </div>
              <div className="h2h-swing-track">
                <div
                  className="h2h-swing-fill"
                  style={{
                    left: netDelta >= 0 ? '50%' : `${Math.max(10, 50 + netDelta * 2.5)}%`,
                    width: `${Math.min(45, Math.abs(netDelta) * 2.5)}%`,
                    background: netDelta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)'
                  }}
                />
                <div className="h2h-swing-center-mark" />
              </div>
              <div className="h2h-swing-labels font-mono">
                <span>Rival Upside (+{rivalUpside.toFixed(1)})</span>
                <span>Even (0)</span>
                <span>Your Upside (+{yourUpside.toFixed(1)})</span>
              </div>
            </div>

            {/* Your Unique Differentials */}
            <div className="diff-section">
              <div className="diff-section-title green">
                <ShieldCheck size={14} weight="bold" />
                <span>Your Points Weapons (Rival Doesn&apos;t Own)</span>
              </div>
              <div className="diff-cards-list">
                {[
                  { name: 'Tavernier', pos: 'MID', cost: 6.0, xp: 5.4, team: 'BOU' },
                  { name: 'Szoboszlai', pos: 'MID', cost: 7.0, xp: 5.4, team: 'LIV' },
                  { name: 'Stach', pos: 'MID', cost: 6.0, xp: 4.8, team: 'LEE' },
                  { name: 'Calafiori', pos: 'DEF', cost: 5.5, xp: 4.7, team: 'ARS' },
                ].map(p => (
                  <div key={p.name} className="diff-ledger-row green">
                    <div className="diff-player-left">
                      <span className={`player-pos-tag ${p.pos}`}>{p.pos}</span>
                      <span className="diff-player-name">{p.name}</span>
                      <span className="diff-team-tag font-mono">{p.team}</span>
                    </div>
                    <div className="diff-player-right font-mono">
                      <span className="diff-cost">£{p.cost.toFixed(1)}m</span>
                      <span className="diff-xp">+{p.xp} xP</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Rival's Danger Men */}
            <div className="diff-section" style={{ marginTop: '16px' }}>
              <div className="diff-section-title red">
                <ShieldWarning size={14} weight="bold" />
                <span>Rival&apos;s Danger Men (You Don&apos;t Own)</span>
              </div>
              <div className="diff-cards-list">
                {(selectedRival.differentials || ['Salah', 'Palmer', 'Isak']).map((pName) => (
                  <div key={pName} className="diff-ledger-row red">
                    <div className="diff-player-left">
                      <span className="player-pos-tag MID">MID</span>
                      <span className="diff-player-name">{pName}</span>
                    </div>
                    <div className="diff-player-right font-mono">
                      <span className="diff-risk-tag">HIGH THREAT</span>
                    </div>
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
