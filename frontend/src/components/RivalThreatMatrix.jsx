import React, { useState, useMemo, useRef, useEffect } from 'react';
import { formatFplPrice } from '../constants/copyTokens';
import {
  UsersThree,
  ShieldCheck,
  ShieldWarning,
  Crown,
  Gauge,
  Info
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
  _bench = [],
  bench = [],
  allPlayers = [],
  allPlayersData = [],
  liveData,
  onInspectPlayer
}) {
  const profile = managerProfile || liveData?.manager_profile || liveData?.manager;
  const rivals = (profile?.rivals && profile.rivals.length > 0)
    ? profile.rivals
    : (liveData?.rival_radar?.competitors && liveData.rival_radar.competitors.length > 0)
      ? liveData.rival_radar.competitors
      : DEFAULT_RIVALS;

  const activeStarters = (starters && starters.length > 0)
    ? starters
    : (liveData?.starters || []);

  const activeAllPlayers = (allPlayers && allPlayers.length > 0)
    ? allPlayers
    : (allPlayersData && allPlayersData.length > 0)
      ? allPlayersData
      : (liveData?.players || []);

  const [selectedRivalId, setSelectedRivalId] = useState(rivals[0]?.entry_id || 1198015);
  const [h2hView, setH2hView] = useState('split'); // 'split' | 'yours' | 'danger'
  const [showNotes, setShowNotes] = useState(false);
  const notesRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (notesRef.current && !notesRef.current.contains(event.target)) {
        setShowNotes(false);
      }
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setShowNotes(false);
      }
    }
    if (showNotes) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showNotes]);

  const selectedRival = rivals.find(r => r.entry_id === selectedRivalId) || rivals[0];

  const leagueName = profile?.league_name || liveData?.league_name || 'Arsenal Bengal FPL 2026-27';
  const leagueId = profile?.league_id || liveData?.league_id || '1305495';
  const myCaptain = activeStarters.find(p => p.is_captain)?.web_name || 'Haaland';

  const handleInspect = (playerName, fallback = {}) => {
    if (!onInspectPlayer) return;
    const clean = (playerName || '').toLowerCase().trim();
    const matched = activeAllPlayers?.find(
      p => (p.web_name || '').toLowerCase() === clean ||
           (p.name || '').toLowerCase() === clean ||
           (p.second_name || '').toLowerCase() === clean
    );
    if (matched) {
      onInspectPlayer(matched);
    } else {
      onInspectPlayer({
        web_name: playerName,
        team: fallback.team || 'PL',
        position: fallback.pos || 'MID',
        cost: fallback.cost || 6.0,
        expected_points: fallback.xp || 4.5
      });
    }
  };

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
      {/* Mini-League Tactical Telemetry Deck */}
      <div className="rivals-telemetry-deck" role="region" aria-label="Mini-League Tactical Telemetry">
        <div className="rivals-telemetry-left">
          <div className="rivals-league-badge">
            <UsersThree size={14} weight="fill" />
            <span className="rivals-league-name">{leagueName}</span>
          </div>
          <span className="rivals-id-pill font-mono">ID #{leagueId}</span>
          <span className="rivals-count-pill font-mono">{rivals.length} Rivals Tracked</span>
        </div>

        <div className="rivals-telemetry-right">
          {/* Captain Consensus Chip */}
          <div
            className="telemetry-chip chip-captain"
            title={`${captainBackingPct}% of rivals in your league (${captainBackingCount}/${rivals.length}) picked ${myCaptain}`}
          >
            <Crown size={14} weight="fill" className="telemetry-chip-icon" />
            <span className="telemetry-chip-label">Captain</span>
            <span className="telemetry-chip-val font-mono">{myCaptain}</span>
            <span className="telemetry-chip-meta font-mono">{captainBackingPct}% backing</span>
          </div>

          {/* Differential Edge Chip */}
          <div
            className="telemetry-chip chip-diff"
            title={`${userDiffNames.length} unique differentials generating +${yourUpside.toFixed(1)} xP potential`}
          >
            <ShieldCheck size={14} weight="bold" className="telemetry-chip-icon" />
            <span className="telemetry-chip-label">Differentials</span>
            <span className="telemetry-chip-val font-mono">{userDiffNames.length} Unique</span>
            <span className="telemetry-chip-meta font-mono">+{yourUpside.toFixed(1)} xP</span>
          </div>

          {/* Danger Threat Chip */}
          <div
            className="telemetry-chip chip-danger"
            title={`Biggest threat to your rank: ${topThreatPlayer} owned by ${threatFrequency} of ${rivals.length} rivals`}
          >
            <ShieldWarning size={14} weight="bold" className="telemetry-chip-icon" />
            <span className="telemetry-chip-label">Danger Pick</span>
            <span className="telemetry-chip-val font-mono">{topThreatPlayer}</span>
            <span className="telemetry-chip-meta font-mono">{threatFrequency}/{rivals.length} rivals</span>
          </div>

          {/* On-Demand Tactical Notes Popover */}
          <div className="telemetry-notes-group" ref={notesRef}>
            <button
              type="button"
              className={`telemetry-notes-btn font-mono ${showNotes ? 'active' : ''}`}
              onClick={() => setShowNotes(prev => !prev)}
              title="Click to view tactical telemetry notes"
              aria-expanded={showNotes}
            >
              <Info size={13} weight="bold" />
              <span>Notes</span>
            </button>
            {showNotes && (
              <div className="telemetry-popover-card font-mono" role="tooltip">
                <h3 className="telemetry-popover-title">
                  Tactical Duel Telemetry &amp; Swing Analysis
                </h3>
                <div className="telemetry-popover-body">
                  <p><strong>Differential Edge:</strong> Starting XI players unique to your squad vs this rival. Net delta reflects projected point swing.</p>
                  <p><strong>Danger Pick:</strong> The highest-frequency player owned across mini-league competitors that is absent from your squad.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Competitor Table & Breakdown Grid */}
      <div className="rivals-grid">
        {/* Table Panel */}
        <div className="data-table-container">
          <div className="studio-table-controls">
            <div className="controls-left">
              <span className="controls-title">Mini-League Table</span>
              <span className="controls-count font-mono">{rivals.length} Rivals Tracked</span>
            </div>
          </div>

          <div className="table-mobile-hint font-mono">
            <span>Swipe table to view squad overlap &amp; compare rivals →</span>
          </div>

          <div className="table-scroll-wrapper rivals-scroll-wrapper">
            <table className="data-table rivals-table">
              <thead>
                <tr>
                  <th scope="col" className="col-rank">Rank</th>
                  <th scope="col" className="col-manager">Manager &amp; Team</th>
                  <th scope="col" className="col-points">Points</th>
                  <th scope="col" className="col-captain">Captain</th>
                  <th scope="col" className="col-overlap">Squad Overlap</th>
                  <th scope="col" className="col-threat">Threat</th>
                  <th scope="col" className="col-action">Action</th>
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
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedRivalId(r.entry_id);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`Rival ${r.manager_name}, ${r.team_name}, Rank ${r.overall_rank || idx + 1}. Click to compare.`}
                      style={{ cursor: 'pointer' }}
                    >
                      <th scope="row" className="font-mono col-rank" style={{ fontWeight: 700, textAlign: 'left' }}>#{r.overall_rank || r.rank || (idx + 1)}</th>
                      <td className="col-manager">
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.manager_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.team_name}</div>
                      </td>
                      <td className="font-mono col-points" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        {r.overall_points || r.total_points || 70}
                      </td>
                      <td className="col-captain">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ fontWeight: 600 }}>{r.captain_name || 'Haaland'}</span>
                          <Crown size={12} weight="fill" color="var(--accent-amber)" />
                        </div>
                      </td>
                      <td className="font-mono col-overlap">{overlapCount}/15 shared ({overlapPctVal}%)</td>
                      <td className="col-threat">
                        <span className={`threat-badge ${threatClass}`}>{r.threat_level === 'HIGH' ? 'HIGH' : r.threat_level === 'LOW' ? 'LOW' : 'MEDIUM'}</span>
                      </td>
                      <td className="col-action">
                        <button
                          type="button"
                          className="table-action-btn"
                          aria-label={isSelected ? `Currently comparing with ${r.manager_name}` : `Compare squad with ${r.manager_name}`}
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
          <div className="h2h-comparison-panel">
            <div className="panel-header">
              <div className="panel-title-group">
                <span className="panel-title">Head-to-Head Tactical Duel</span>
                <span className="panel-subtitle">Differential edge analysis &amp; swing risk</span>
              </div>
              <span className="panel-badge font-mono">vs {selectedRival.manager_name}</span>
            </div>

            {/* Swing Risk Range Gauge */}
            <div className="h2h-swing-container">
              <div className="h2h-swing-header">
                <span className="h2h-swing-title">
                  <Gauge size={14} weight="bold" />
                  <span>Projected Matchup Swing</span>
                </span>
                <span className="h2h-swing-val font-mono" style={{ color: netDelta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)' }}>
                  {netDelta >= 0 ? `+${netDelta.toFixed(1)} pts projected lead` : `${netDelta.toFixed(1)} pts projected deficit`}
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
                <span>Rival Threats (+{rivalUpside.toFixed(1)})</span>
                <span>Even (0)</span>
                <span>Your Differentials (+{yourUpside.toFixed(1)})</span>
              </div>
            </div>

            {/* View Mode Switcher */}
            <div className="h2h-view-tabs" role="tablist">
              <button
                type="button"
                className={`h2h-tab-btn ${h2hView === 'split' ? 'active' : ''}`}
                onClick={() => setH2hView('split')}
              >
                <span>Split View</span>
              </button>
              <button
                type="button"
                className={`h2h-tab-btn ${h2hView === 'yours' ? 'active' : ''}`}
                onClick={() => setH2hView('yours')}
              >
                <span>Your Differentials ({userDiffCards.length})</span>
              </button>
              <button
                type="button"
                className={`h2h-tab-btn ${h2hView === 'danger' ? 'active' : ''}`}
                onClick={() => setH2hView('danger')}
              >
                <span>Danger Players ({rivalDiffCards.length})</span>
              </button>
            </div>

            {/* Content Container (Split or Single Column) */}
            <div className={`h2h-diff-layout ${h2hView}`}>
              {/* Your Unique Differentials */}
              {(h2hView === 'split' || h2hView === 'yours') && (
                <div className="h2h-diff-col green">
                  <div className="h2h-col-header green">
                    <div className="h2h-col-title">
                      <ShieldCheck size={14} weight="bold" />
                      <span>Your Differentials ({userDiffCards.length})</span>
                    </div>
                    <span className="h2h-upside-pill green font-mono">+{yourUpside.toFixed(1)} xP</span>
                  </div>
                  <div className="h2h-cards-scroll">
                    {userDiffCards.map(p => (
                      <div
                        key={p.name}
                        className="h2h-compact-row green"
                        onClick={() => handleInspect(p.name, p)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleInspect(p.name, p);
                          }
                        }}
                        style={{ cursor: 'pointer' }}
                        title={`Click to view ${p.name} scouting report`}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="h2h-player-meta">
                          <span className={`player-pos-tag pill-base pill-sm ${p.pos || 'MID'}`}>{p.pos || 'MID'}</span>
                          <span className="h2h-player-name">{p.name}</span>
                          {p.team && <span className="h2h-team-tag font-mono">{p.team}</span>}
                        </div>
                        <div className="h2h-player-stats font-mono">
                          <span className="h2h-cost">£{formatFplPrice(p.cost)}m</span>
                          <span className="h2h-xp green">+{Number(p.xp || 4.5).toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Rival's Danger Men */}
              {(h2hView === 'split' || h2hView === 'danger') && (
                <div className="h2h-diff-col red">
                  <div className="h2h-col-header red">
                    <div className="h2h-col-title">
                      <ShieldWarning size={14} weight="bold" />
                      <span>Danger Players ({rivalDiffCards.length})</span>
                    </div>
                    <span className="h2h-upside-pill red font-mono">+{rivalUpside.toFixed(1)} xP</span>
                  </div>
                  <div className="h2h-cards-scroll">
                    {rivalDiffCards.map(p => (
                      <div
                        key={p.name}
                        className="h2h-compact-row red"
                        onClick={() => handleInspect(p.name, p)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleInspect(p.name, p);
                          }
                        }}
                        style={{ cursor: 'pointer' }}
                        title={`Click to view ${p.name} scouting report`}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="h2h-player-meta">
                          <span className={`player-pos-tag pill-base pill-sm ${p.pos || 'MID'}`}>{p.pos || 'MID'}</span>
                          <span className="h2h-player-name">{p.name}</span>
                          {p.team && <span className="h2h-team-tag font-mono">{p.team}</span>}
                        </div>
                        <div className="h2h-player-stats font-mono">
                          <span className="h2h-cost">£{formatFplPrice(p.cost)}m</span>
                          <span className="h2h-xp red">+{Number(p.xp || 4.5).toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

