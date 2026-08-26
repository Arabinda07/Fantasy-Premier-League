import React, { useState, useMemo } from 'react';
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
    entry_id: 1198015,
    manager_name: "Souptik Som",
    team_name: "The Corner Kings",
    overall_rank: 1,
    overall_points: 95,
    captain_name: "Ødegaard",
    differentials: ["Palmer", "Wirtz", "Gvardiol", "Tzolis", "João Pedro"],
    shared_players: ["Szoboszlai", "Calafiori", "Haaland"],
    threat_level: "HIGH",
    overlap_pct: 20.0
  },
  {
    entry_id: 1670132,
    manager_name: "Ishaan Agarwal",
    team_name: "Young Guns",
    overall_rank: 2,
    overall_points: 87,
    captain_name: "Haaland",
    differentials: ["Palmer", "Ødegaard", "Gvardiol", "Semenyo", "Maguire"],
    shared_players: ["Haaland", "Szoboszlai", "Ballard"],
    threat_level: "HIGH",
    overlap_pct: 20.0
  },
  {
    entry_id: 3400909,
    manager_name: "SOUMYADEEP MITRA",
    team_name: "Invincible04",
    overall_rank: 3,
    overall_points: 84,
    captain_name: "João Pedro",
    differentials: ["Palmer", "Virgil", "Wirtz", "Gvardiol", "Semenyo"],
    shared_players: ["Raya", "Calafiori"],
    threat_level: "HIGH",
    overlap_pct: 13.3
  },
  {
    entry_id: 2721839,
    manager_name: "Pratik Dutta",
    team_name: "Its not done yet",
    overall_rank: 4,
    overall_points: 78,
    captain_name: "Haaland",
    differentials: ["Tzolis", "Ndiaye", "Maguire", "Ajer"],
    shared_players: ["Raya", "Calafiori", "B.Fernandes", "Szoboszlai", "Haaland"],
    threat_level: "MEDIUM",
    overlap_pct: 33.3
  },
  {
    entry_id: 633687,
    manager_name: "Nikhil Sudheer",
    team_name: "BluxXI",
    overall_rank: 5,
    overall_points: 76,
    captain_name: "B.Fernandes",
    differentials: ["Palmer", "Wirtz", "Gvardiol", "Mosquera"],
    shared_players: ["Raya", "Calafiori", "B.Fernandes", "Mbeumo"],
    threat_level: "MEDIUM",
    overlap_pct: 26.7
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

  const [selectedRivalId, setSelectedRivalId] = useState(rivals[0]?.entry_id || 1198015);

  const selectedRival = rivals.find(r => r.entry_id === selectedRivalId) || rivals[0];

  const leagueName = managerProfile?.league_name || 'Arsenal Bengal FPL 2026-27';
  const leagueId = managerProfile?.league_id || '1305495';
  const myCaptain = starters.find(p => p.is_captain)?.web_name || 'Haaland';

  // Compute dynamic KPI metrics across all rivals
  const { captainBackingPct, captainBackingCount, topThreatPlayer, threatFrequency, userDiffNames } = useMemo(() => {
    let captCount = 0;
    const threatCounts = {};

    rivals.forEach(r => {
      const rCap = (r.captain_name || '').trim().toLowerCase();
      if (rCap && rCap === myCaptain.toLowerCase()) {
        captCount++;
      }

      const diffList = r.differentials || [];
      diffList.forEach(pName => {
        threatCounts[pName] = (threatCounts[pName] || 0) + 1;
      });
    });

    const captPct = Math.round((captCount / Math.max(1, rivals.length)) * 100);

    // Find highest frequency rival threat
    let topThreat = 'Palmer';
    let maxFreq = 0;
    Object.entries(threatCounts).forEach(([name, count]) => {
      if (count > maxFreq) {
        maxFreq = count;
        topThreat = name;
      }
    });

    // Extract user unique differentials from selected rival or starters
    const diffs = selectedRival?.user_differentials || [
      'White', 'B.Fernandes', 'Tavernier', 'Mbeumo', 'Stach', 'Calvert-Lewin'
    ];

    return {
      captainBackingPct: captPct,
      captainBackingCount: captCount,
      topThreatPlayer: topThreat,
      threatFrequency: maxFreq || 3,
      userDiffNames: diffs
    };
  }, [rivals, myCaptain, selectedRival]);

  // Compute swing potential for selected rival
  const userDiffCards = selectedRival?.user_differential_cards || [
    { name: 'B.Fernandes', pos: 'MID', cost: 8.5, xp: 6.2, team: 'MUN' },
    { name: 'Mbeumo', pos: 'MID', cost: 7.0, xp: 5.8, team: 'BRE' },
    { name: 'Tavernier', pos: 'MID', cost: 5.5, xp: 5.4, team: 'BOU' },
    { name: 'White', pos: 'DEF', cost: 6.5, xp: 4.8, team: 'ARS' },
    { name: 'Stach', pos: 'MID', cost: 5.5, xp: 4.6, team: 'LEE' },
  ];

  const rivalDiffCards = selectedRival?.rival_differential_cards || (
    (selectedRival?.differentials || ['Palmer', 'Wirtz', 'Gvardiol', 'Tzolis']).map(name => ({
      name,
      pos: 'MID',
      cost: 7.5,
      xp: 5.2,
      team: 'PL'
    }))
  );

  const yourUpside = selectedRival?.your_upside || Number(userDiffCards.reduce((acc, p) => acc + (Number(p.xp) || 4.5), 0).toFixed(1));
  const rivalUpside = selectedRival?.rival_upside || Number(rivalDiffCards.reduce((acc, p) => acc + (Number(p.xp) || 4.5), 0).toFixed(1));
  const netDelta = selectedRival?.net_delta !== undefined
    ? selectedRival.net_delta
    : Number((yourUpside - rivalUpside).toFixed(1));

  return (
    <div className="view-fluid">
      {/* Hero Header */}
      <div className="studio-hero-panel">
        <div className="studio-hero-header">
          <div className="studio-badge">
            <UsersThree size={14} weight="fill" />
            <span>{leagueName.toUpperCase()}</span>
          </div>
          <span className="studio-version font-mono">
            LEAGUE ID #{leagueId}
          </span>
        </div>
        <h1 className="studio-title">{leagueName} · Rival Radar & Differentials</h1>
        <p className="studio-description">
          Live head-to-head intelligence against top mini-league contenders. Spot key points weapons to gain rank and monitor dangerous differentials.
        </p>

        {/* Top Metric Strip */}
        <div className="kpi-strip">
          <div className="kpi-card">
            <div className="kpi-label">Your Captain Pick</div>
            <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
              {myCaptain}
              <Crown size={16} weight="fill" />
            </div>
            <div className="kpi-subtext">
              {captainBackingPct}% of rivals ({captainBackingCount}/{rivals.length}) backing the same pick
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Active Differentials</div>
            <div className="kpi-value font-mono" style={{ color: 'var(--accent-emerald)' }}>
              {userDiffNames.length} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Unique Weapons</span>
            </div>
            <div className="kpi-subtext">
              {userDiffNames.slice(0, 5).join(', ')}{userDiffNames.length > 5 ? '...' : ''}
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Biggest Rival Threat</div>
            <div className="kpi-value" style={{ color: 'var(--accent-crimson)' }}>
              {topThreatPlayer}
            </div>
            <div className="kpi-subtext">
              Owned by {threatFrequency} of your top {rivals.length} mini-league rivals
            </div>
          </div>
        </div>
      </div>

      {/* Main Competitor Table & Breakdown Grid */}
      <div className="rivals-grid">
        {/* Table Panel */}
        <div className="data-table-container">
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title">Mini-League Contenders</span>
              <span className="controls-count font-mono">{rivals.length} Rivals Tracked</span>
            </div>
          </div>

          <div className="table-scroll-wrapper">
            <table className="data-table rivals-table">
              <thead>
                <tr>
                  <th style={{ width: '8%' }}>Rank</th>
                  <th style={{ width: '28%' }}>Manager / Team</th>
                  <th style={{ width: '12%' }}>Points</th>
                  <th style={{ width: '18%' }}>Captain</th>
                  <th style={{ width: '14%' }}>Overlap</th>
                  <th style={{ width: '10%' }}>Threat</th>
                  <th style={{ width: '10%' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {rivals.map((r, idx) => {
                  const isSelected = selectedRival?.entry_id === r.entry_id;
                  const threatClass = r.threat_level === 'HIGH' ? 'threat-high' : r.threat_level === 'MEDIUM' ? 'threat-med' : 'threat-low';
                  const overlapCount = r.shared_players?.length || r.overlap_count || 3;
                  const overlapPctVal = r.overlap_pct !== undefined
                    ? (r.overlap_pct > 1 ? Math.round(r.overlap_pct) : Math.round(r.overlap_pct * 100))
                    : Math.round((overlapCount / 15) * 100);

                  return (
                    <tr
                      key={r.entry_id || idx}
                      className={isSelected ? 'selected-row' : ''}
                      onClick={() => setSelectedRivalId(r.entry_id)}
                      style={{ cursor: 'pointer' }}
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
                          <span style={{ fontWeight: 600 }}>{r.captain_name || 'Haaland'}</span>
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
                            setSelectedRivalId(r.entry_id);
                          }}
                        >
                          {isSelected ? 'Active' : 'Compare'}
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
                    left: netDelta >= 0 ? '50%' : `${Math.max(5, 50 + netDelta * 2.0)}%`,
                    width: `${Math.min(48, Math.abs(netDelta) * 2.0)}%`,
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
                {userDiffCards.map(p => (
                  <div key={p.name} className="diff-ledger-row green">
                    <div className="diff-player-left">
                      <span className={`player-pos-tag ${p.pos || 'MID'}`}>{p.pos || 'MID'}</span>
                      <span className="diff-player-name">{p.name}</span>
                      {p.team && <span className="diff-team-tag font-mono">{p.team}</span>}
                    </div>
                    <div className="diff-player-right font-mono">
                      <span className="diff-cost">£{Number(p.cost || 6.0).toFixed(1)}m</span>
                      <span className="diff-xp">+{Number(p.xp || 4.5).toFixed(1)} xP</span>
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
                {rivalDiffCards.map(p => (
                  <div key={p.name} className="diff-ledger-row red">
                    <div className="diff-player-left">
                      <span className={`player-pos-tag ${p.pos || 'MID'}`}>{p.pos || 'MID'}</span>
                      <span className="diff-player-name">{p.name}</span>
                      {p.team && <span className="diff-team-tag font-mono">{p.team}</span>}
                    </div>
                    <div className="diff-player-right font-mono">
                      <span className="diff-cost">£{Number(p.cost || 6.0).toFixed(1)}m</span>
                      <span className="diff-xp" style={{ color: 'var(--accent-crimson)' }}>+{Number(p.xp || 4.5).toFixed(1)} xP</span>
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

