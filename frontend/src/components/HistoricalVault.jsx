import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Trophy,
  Crown,
  SoccerBall,
  Calendar,
  CaretLeft,
  CaretRight,
  CaretUp,
  CaretDown,
  Medal,
  Terminal,
  ArrowUpRight,
  X
} from '@phosphor-icons/react';
import vaultData from '../data/historical_vault.json';

export default function HistoricalVault({ onInspectPlayer }) {
  const seasonsList = vaultData.seasons || [];
  const [selectedSeason, setSelectedSeason] = useState(seasonsList[0]?.season || '2025-26');
  const [activeTab, setActiveTab] = useState('pitch'); // 'pitch' | 'records' | 'comparison' | 'lab'
  const [inspectedHistoricalPlayer, setInspectedHistoricalPlayer] = useState(null);
  const [recordsFilter, setRecordsFilter] = useState('all'); // 'all' | 'points' | 'goals'

  // Sorting state for the 10-season comparative table
  const [sortKey, setSortKey] = useState('season');
  const [sortDir, setSortDir] = useState('desc');

  // Timeline scrubber references for automatic smooth alignment
  const trackRef = useRef(null);
  const nodeRefs = useRef({});

  // Current season metadata
  const currentSeasonMeta = useMemo(() => {
    return seasonsList.find(s => s.season === selectedSeason) || seasonsList[0];
  }, [seasonsList, selectedSeason]);

  // Current season dream team players
  const currentDreamTeam = useMemo(() => {
    const players = (vaultData.dream_teams && vaultData.dream_teams[selectedSeason]) || [];
    const starters = players.filter(p => p.is_starter === 1);
    const bench = players.filter(p => p.is_starter === 0);

    // Identify highest scoring starter for captaincy badge
    let maxPts = -1;
    let captainCode = null;
    starters.forEach(p => {
      if (p.total_points > maxPts) {
        maxPts = p.total_points;
        captainCode = p.player_code;
      }
    });

    return {
      starters,
      bench,
      captainCode,
      totalStarterPts: starters.reduce((acc, p) => acc + (p.total_points || 0), 0),
      totalBenchPts: bench.reduce((acc, p) => acc + (p.total_points || 0), 0),
      formation: `${starters.filter(p => p.position === 'DEF').length}-${starters.filter(p => p.position === 'MID').length}-${starters.filter(p => p.position === 'FWD').length}`
    };
  }, [selectedSeason]);

  // Group starters by pitch lines
  const gks = currentDreamTeam.starters.filter(p => p.position === 'GK');
  const defs = currentDreamTeam.starters.filter(p => p.position === 'DEF');
  const mids = currentDreamTeam.starters.filter(p => p.position === 'MID');
  const fwds = currentDreamTeam.starters.filter(p => p.position === 'FWD');

  // Season Navigation Helpers
  const currentSeasonIndex = seasonsList.findIndex(s => s.season === selectedSeason);
  const handleNewerSeason = () => {
    if (currentSeasonIndex > 0) {
      setSelectedSeason(seasonsList[currentSeasonIndex - 1].season);
    }
  };
  const handleOlderSeason = () => {
    if (currentSeasonIndex < seasonsList.length - 1) {
      setSelectedSeason(seasonsList[currentSeasonIndex + 1].season);
    }
  };

  // Auto-scroll the active season node into view whenever selection changes
  useEffect(() => {
    const activeEl = nodeRefs.current[selectedSeason];
    if (activeEl && trackRef.current) {
      activeEl.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center'
      });
    }
  }, [selectedSeason]);

  // Keyboard navigation for Escape key on player modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && inspectedHistoricalPlayer) {
        setInspectedHistoricalPlayer(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [inspectedHistoricalPlayer]);

  // Sorted list for 10-season table
  const sortedSeasons = useMemo(() => {
    const list = [...seasonsList];
    list.sort((a, b) => {
      let valA = a[sortKey];
      let valB = b[sortKey];

      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }

      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [seasonsList, sortKey, sortDir]);

  const handleHeaderSort = (key) => {
    if (sortKey === key) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const handlePlayerClick = (player) => {
    setInspectedHistoricalPlayer(player);
    if (onInspectPlayer) {
      onInspectPlayer(player);
    }
  };

  return (
    <div className="historical-vault-view surface-scope-vault" style={{ padding: '0 0 40px 0' }}>
      {/* 1. Header Banner & View Mode Switcher with Direction J Wire Segments */}
      <div className="vault-hero-bar">
        <div className="vault-hero-inner">
          <div>
            <h1 className="vault-hero-title">
              Premier League Time Machine
            </h1>
            <p className="vault-hero-subtitle zinc">
              Official season-by-season Dream Teams on the tactical pitch, all-time record hauls, and league trends.
            </p>
          </div>

          {/* Wire Segments Navigation Rail */}
          <div
            className="wire-segments font-mono"
            role="tablist"
            aria-label="Historical Vault Views"
          >
            <button
              type="button"
              role="tab"
              id="vault-tab-pitch"
              aria-selected={activeTab === 'pitch'}
              aria-controls="vault-panel-pitch"
              tabIndex={activeTab === 'pitch' ? 0 : -1}
              className="wire-segment"
              aria-pressed={activeTab === 'pitch'}
              onClick={() => setActiveTab('pitch')}
            >
              <Trophy size={13} weight={activeTab === 'pitch' ? 'fill' : 'bold'} />
              <span>Dream Team Pitch</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-records"
              aria-selected={activeTab === 'records'}
              aria-controls="vault-panel-records"
              tabIndex={activeTab === 'records' ? 0 : -1}
              className="wire-segment"
              aria-pressed={activeTab === 'records'}
              onClick={() => setActiveTab('records')}
            >
              <Medal size={13} weight={activeTab === 'records' ? 'fill' : 'bold'} />
              <span>All-Time Records</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-comparison"
              aria-selected={activeTab === 'comparison'}
              aria-controls="vault-panel-comparison"
              tabIndex={activeTab === 'comparison' ? 0 : -1}
              className="wire-segment"
              aria-pressed={activeTab === 'comparison'}
              onClick={() => setActiveTab('comparison')}
            >
              <Calendar size={13} weight={activeTab === 'comparison' ? 'fill' : 'bold'} />
              <span>10-Season Overview</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-lab"
              aria-selected={activeTab === 'lab'}
              aria-controls="vault-panel-lab"
              tabIndex={activeTab === 'lab' ? 0 : -1}
              className="wire-segment"
              aria-pressed={activeTab === 'lab'}
              onClick={() => setActiveTab('lab')}
            >
              <Terminal size={13} weight={activeTab === 'lab' ? 'fill' : 'bold'} />
              <span>SQL Lab</span>
            </button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 clamp(12px, 2vw, 20px)' }}>
        {/* 2 & 3. Season Timeline Scrubber & 48px Telemetry Deck (Pitch View) */}
        {activeTab === 'pitch' && (
          <>
            {/* Borderless Season Timeline Scrubber */}
            <div className="vault-timeline-scrubber font-mono" role="region" aria-label="Season Timeline">
              <button
                type="button"
                className="timeline-nav-btn font-mono"
                onClick={handleNewerSeason}
                disabled={currentSeasonIndex <= 0}
                title="Newer Season"
                aria-label="Navigate to newer season"
              >
                <CaretLeft size={13} weight="bold" />
                <span>NEWER</span>
              </button>

              <div className="timeline-track" ref={trackRef}>
                {seasonsList.map(s => {
                  const isSelected = s.season === selectedSeason;
                  return (
                    <button
                      key={s.season}
                      ref={el => { nodeRefs.current[s.season] = el; }}
                      type="button"
                      onClick={() => setSelectedSeason(s.season)}
                      className={`timeline-node font-mono ${isSelected ? 'is-active' : ''}`}
                      aria-pressed={isSelected}
                      aria-label={`Select season ${s.season}`}
                    >
                      <span className="timeline-year">{s.season}</span>
                      {isSelected && <span className="timeline-indicator" />}
                    </button>
                  );
                })}
              </div>

              <button
                type="button"
                className="timeline-nav-btn font-mono"
                onClick={handleOlderSeason}
                disabled={currentSeasonIndex >= seasonsList.length - 1}
                title="Older Season"
                aria-label="Navigate to older season"
              >
                <span>OLDER</span>
                <CaretRight size={13} weight="bold" />
              </button>
            </div>

            {/* 48px Direction J Telemetry Deck */}
            <div className="vault-telemetry-deck font-mono" role="region" aria-label="Season Telemetry">
              <div className="telemetry-cell">
                <span className="cell-label zinc">CAMPAIGN:</span>
                <span className="cell-val cream">{selectedSeason}</span>
                <span className="cell-sub zinc">(38 GWs · {currentSeasonMeta?.total_players?.toLocaleString() || '0'} players)</span>
              </div>

              <div className="telemetry-divider" aria-hidden="true" />

              <div className="telemetry-cell">
                <span className="cell-label zinc">FIREPOWER:</span>
                <span className="cell-val cream">{currentSeasonMeta?.total_goals?.toLocaleString() || '0'} G</span>
                <span className="cell-sub zinc">· {currentSeasonMeta?.total_assists?.toLocaleString() || '0'} A</span>
              </div>

              <div className="telemetry-divider" aria-hidden="true" />

              <div className="telemetry-cell">
                <span className="cell-label zinc">GOLDEN BOOT:</span>
                <span className="cell-val cream">{currentSeasonMeta?.top_scorer_name || '-'}</span>
                <span className="cell-sub zinc">({currentSeasonMeta?.top_scorer_goals} G)</span>
              </div>

              <div className="telemetry-divider" aria-hidden="true" />

              <div className="telemetry-cell">
                <span className="cell-label zinc">SEASON MVP:</span>
                <span className="cell-val cream">{currentSeasonMeta?.top_points_name || '-'}</span>
                <span className="cell-sub zinc">({currentSeasonMeta?.top_points || 0} pts)</span>
              </div>
            </div>
          </>
        )}

        {/* 4. Tab View 1: Tactical Pitch (Dream Team) */}
        {activeTab === 'pitch' && (
          <div
            role="tabpanel"
            id="vault-panel-pitch"
            aria-labelledby="vault-tab-pitch"
            tabIndex={0}
            className="vault-pitch-workspace"
          >
            {/* Tactical Pitch Column */}
            <div className="vault-pitch-col">
              {/* Pitch Telemetry Strip */}
              <div className="vault-pitch-header font-mono">
                <span className="zinc">OFFICIAL DREAM TEAM:</span>
                <span className="cream font-bold">{selectedSeason}</span>
                <span className="zinc">·</span>
                <span className="cream">{currentDreamTeam.formation} FORMATION</span>
                <span className="zinc">·</span>
                <span className="cream font-bold">{currentDreamTeam.totalStarterPts.toLocaleString()} STARTER PTS</span>
              </div>

              {/* Direction J Wire Pitch */}
              <div className="wire-pitch vault-wire-pitch">
                {/* Row 1: Goalkeepers */}
                <div className={`wire-pitch-row pitch-row-count-${gks.length}`}>
                  {gks.map(p => (
                    <HistoricalPlayerCard
                      key={`${selectedSeason}-${p.player_code}`}
                      player={p}
                      isCaptain={p.player_code === currentDreamTeam.captainCode}
                      onInspect={handlePlayerClick}
                    />
                  ))}
                </div>

                {/* Row 2: Defenders */}
                <div className={`wire-pitch-row pitch-row-count-${defs.length}`}>
                  {defs.map(p => (
                    <HistoricalPlayerCard
                      key={`${selectedSeason}-${p.player_code}`}
                      player={p}
                      isCaptain={p.player_code === currentDreamTeam.captainCode}
                      onInspect={handlePlayerClick}
                    />
                  ))}
                </div>

                {/* Row 3: Midfielders */}
                <div className={`wire-pitch-row pitch-row-count-${mids.length}`}>
                  {mids.map(p => (
                    <HistoricalPlayerCard
                      key={`${selectedSeason}-${p.player_code}`}
                      player={p}
                      isCaptain={p.player_code === currentDreamTeam.captainCode}
                      onInspect={handlePlayerClick}
                    />
                  ))}
                </div>

                {/* Row 4: Forwards */}
                <div className={`wire-pitch-row pitch-row-count-${fwds.length}`}>
                  {fwds.map(p => (
                    <HistoricalPlayerCard
                      key={`${selectedSeason}-${p.player_code}`}
                      player={p}
                      isCaptain={p.player_code === currentDreamTeam.captainCode}
                      onInspect={handlePlayerClick}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Right Sidebar: Dream Team Bench & Squad Breakdown */}
            <div className="vault-bench-totals-container">
              {/* Bench Container */}
              <div className="vault-sidebar-card">
                <div className="vault-sidebar-header font-mono">
                  <span className="zinc">DREAM TEAM BENCH</span>
                  <span className="cream font-bold">+{currentDreamTeam.totalBenchPts} pts</span>
                </div>

                <div className="vault-bench-list">
                  {currentDreamTeam.bench.map((sub) => (
                    <button
                      key={`${selectedSeason}-sub-${sub.player_code}`}
                      type="button"
                      onClick={() => handlePlayerClick(sub)}
                      className="vault-bench-row font-mono"
                      aria-label={`${sub.web_name}, ${sub.position}, ${sub.total_points} pts`}
                    >
                      <div className="bench-row-left">
                        <span className="bench-pos zinc">[{sub.position}]</span>
                        <span className="bench-name cream font-bold">{sub.web_name}</span>
                        <span className="bench-meta zinc">{sub.team_name} · £{Number(sub.now_cost).toFixed(1)}m</span>
                      </div>
                      <div className="bench-row-right">
                        <span className="bench-pts cream font-bold">{sub.total_points}</span>
                        <span className="bench-unit zinc">pts</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Season Dream Team Summary Card */}
              <div className="vault-sidebar-card font-mono">
                <div className="vault-sidebar-header">
                  <span className="zinc">CAMPAIGN TOTALS</span>
                </div>
                <div className="vault-totals-rows">
                  <div className="vault-totals-row">
                    <span className="zinc">Starters Points</span>
                    <span className="cream font-bold">{currentDreamTeam.totalStarterPts} pts</span>
                  </div>
                  <div className="vault-totals-row">
                    <span className="zinc">Full 15-Man Total</span>
                    <span className="cream font-bold">{currentDreamTeam.totalStarterPts + currentDreamTeam.totalBenchPts} pts</span>
                  </div>
                  <div className="vault-totals-row">
                    <span className="zinc">Armband Pick [C]</span>
                    <span className="cream font-bold">{currentSeasonMeta?.top_points_name} ({currentSeasonMeta?.top_points} pts)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 5. Tab View 2: All-Time Records (Hall of Fame) with Wire Segments */}
        {activeTab === 'records' && (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Premier League Hall of Fame
                </h2>
                <p className="zinc" style={{ fontSize: '12px', margin: '3px 0 0 0' }}>
                  The 15 greatest individual seasons in modern Premier League fantasy history.
                </p>
              </div>

              {/* Wire Segments Filter */}
              <div className="wire-segments font-mono" role="group" aria-label="Records Filter">
                <button
                  type="button"
                  onClick={() => setRecordsFilter('all')}
                  className="wire-segment"
                  aria-pressed={recordsFilter === 'all'}
                >
                  All Records
                </button>
                <button
                  type="button"
                  onClick={() => setRecordsFilter('points')}
                  className="wire-segment"
                  aria-pressed={recordsFilter === 'points'}
                >
                  <Crown size={13} weight="bold" />
                  <span>Points</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRecordsFilter('goals')}
                  className="wire-segment"
                  aria-pressed={recordsFilter === 'goals'}
                >
                  <SoccerBall size={13} weight="bold" />
                  <span>Goals</span>
                </button>
              </div>
            </div>

            <div
              role="tabpanel"
              id="vault-panel-records"
              aria-labelledby="vault-tab-records"
              tabIndex={0}
              className="vault-records-grid"
            >
              {/* Hall of Fame: Points */}
              {(recordsFilter === 'all' || recordsFilter === 'points') && (
                <div className="vault-sidebar-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <Crown size={16} weight="bold" style={{ color: 'var(--accent-amber)' }} />
                    <div>
                      <h3 style={{ fontSize: '13px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                        All-Time Highest Scoring Seasons
                      </h3>
                      <p className="zinc" style={{ fontSize: '11px', margin: '2px 0 0 0' }}>
                        Top individual player campaigns across 10 seasons
                      </p>
                    </div>
                  </div>

                  <div className="vault-records-scrollable" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {(vaultData.hall_of_fame_points || []).map((record, index) => (
                      <div
                        key={`hof-pts-${index}`}
                        onClick={() => handlePlayerClick(record)}
                        className={`vault-record-row font-mono ${index === 0 ? 'is-leader' : ''}`}
                        title={`Click to inspect ${record.web_name}'s full ${record.season} season haul`}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handlePlayerClick(record);
                          }
                        }}
                      >
                        <div className="record-left">
                          <span className="record-rank zinc">#{index + 1}</span>
                          <span className="record-pos zinc">[{record.position}]</span>
                          <span className="record-name cream font-bold">{record.web_name}</span>
                          <span className="record-meta zinc">{record.team_name} · <span className="cream">{record.season}</span> · {record.goals_scored}G / {record.assists}A</span>
                        </div>

                        <div className="record-right font-mono">
                          <span className="record-val cream font-bold">{record.total_points}</span>
                          <span className="record-unit zinc">pts</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Hall of Fame: Goals (Golden Boots) */}
              {(recordsFilter === 'all' || recordsFilter === 'goals') && (
                <div className="vault-sidebar-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <SoccerBall size={16} weight="bold" style={{ color: 'var(--text-primary)' }} />
                    <div>
                      <h3 style={{ fontSize: '13px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                        All-Time Most Prolific Goal Seasons
                      </h3>
                      <p className="zinc" style={{ fontSize: '11px', margin: '2px 0 0 0' }}>
                        Most clinical individual finishing campaigns since 2016
                      </p>
                    </div>
                  </div>

                  <div className="vault-records-scrollable" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {(vaultData.hall_of_fame_goals || []).map((record, index) => (
                      <div
                        key={`hof-goals-${index}`}
                        onClick={() => handlePlayerClick(record)}
                        className={`vault-record-row font-mono ${index === 0 ? 'is-leader' : ''}`}
                        title={`Click to inspect ${record.web_name}'s full ${record.season} campaign stats`}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handlePlayerClick(record);
                          }
                        }}
                      >
                        <div className="record-left">
                          <span className="record-rank zinc">#{index + 1}</span>
                          <span className="record-pos zinc">[{record.position}]</span>
                          <span className="record-name cream font-bold">{record.web_name}</span>
                          <span className="record-meta zinc">{record.team_name} · <span className="cream">{record.season}</span> · {record.assists} assists</span>
                        </div>

                        <div className="record-right font-mono">
                          <span className="record-val cream font-bold">{record.goals_scored}</span>
                          <span className="record-unit zinc">goals</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. Tab View 3: 10-Season Overview Table with Sticky Season Column */}
        {activeTab === 'comparison' && (
          <div
            role="tabpanel"
            id="vault-panel-comparison"
            aria-labelledby="vault-tab-comparison"
            tabIndex={0}
            className="data-table-container vault-table-container"
          >
            <div style={{ marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  10-Season Premier League Comparative Matrix
                </h3>
                <p className="zinc" style={{ fontSize: '12px', margin: '3px 0 0 0' }}>
                  Click column headers to sort by total goals, assists, top point haulers, or Golden Boot tallies.
                </p>
              </div>
              <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Sorted by: <strong className="cream">{sortKey.replace('_', ' ').toUpperCase()} ({sortDir.toUpperCase()})</strong>
              </span>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '650px' }}>
              <thead>
                <tr style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                  fontSize: '11px',
                  position: 'sticky',
                  top: 0,
                  backgroundColor: 'var(--bg-surface-1)',
                  zIndex: 4
                }}>
                  <th
                    scope="col"
                    className="font-mono sortable-th vault-table-sticky-col"
                    onClick={() => handleHeaderSort('season')}
                    style={{ padding: '10px 12px', cursor: 'pointer', userSelect: 'none', minWidth: '90px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span>SEASON</span>
                      {sortKey === 'season' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('top_points')}
                    style={{ padding: '10px 12px', cursor: 'pointer', userSelect: 'none', minWidth: '180px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span>TOP POINTS HAULER</span>
                      {sortKey === 'top_points' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('top_scorer_goals')}
                    style={{ padding: '10px 12px', cursor: 'pointer', userSelect: 'none', minWidth: '170px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span>GOLDEN BOOT</span>
                      {sortKey === 'top_scorer_goals' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('total_goals')}
                    style={{ padding: '10px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none', minWidth: '110px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', width: '100%' }}>
                      <span>TOTAL GOALS</span>
                      {sortKey === 'total_goals' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('total_assists')}
                    style={{ padding: '10px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none', minWidth: '110px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', width: '100%' }}>
                      <span>TOTAL ASSISTS</span>
                      {sortKey === 'total_assists' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('total_players')}
                    style={{ padding: '10px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none', minWidth: '90px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', width: '100%' }}>
                      <span>PLAYERS</span>
                      {sortKey === 'total_players' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th scope="col" className="font-mono" style={{ padding: '10px 12px', textAlign: 'center', minWidth: '100px' }}>
                    ACTION
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedSeasons.map(s => {
                  const isCurrent = s.season === selectedSeason;
                  return (
                    <tr
                      key={`comp-row-${s.season}`}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isCurrent ? 'var(--bg-surface-2)' : 'transparent',
                        fontSize: '12px'
                      }}
                    >
                      <th scope="row" className="font-mono vault-table-sticky-col" style={{
                        padding: '10px 12px',
                        fontWeight: 700,
                        textAlign: 'left',
                        color: isCurrent ? 'var(--text-primary)' : 'var(--text-secondary)',
                        borderLeft: isCurrent ? '2px solid var(--text-primary)' : '2px solid transparent'
                      }}>
                        {s.season}
                      </th>
                      <td style={{ padding: '10px 12px' }}>
                        <span className="cream font-bold">{s.top_points_name}</span>{' '}
                        <span className="font-mono zinc" style={{ fontSize: '11px' }}>({s.top_points} pts)</span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className="cream font-bold">{s.top_scorer_name}</span>{' '}
                        <span className="font-mono zinc" style={{ fontSize: '11px' }}>({s.top_scorer_goals} goals)</span>
                      </td>
                      <td className="font-mono cream font-bold" style={{ padding: '10px 12px', textAlign: 'right' }}>
                        {s.total_goals?.toLocaleString()}
                      </td>
                      <td className="font-mono zinc" style={{ padding: '10px 12px', textAlign: 'right' }}>
                        {s.total_assists?.toLocaleString()}
                      </td>
                      <td className="font-mono zinc" style={{ padding: '10px 12px', textAlign: 'right' }}>
                        {s.total_players}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <button
                          type="button"
                          className="wire-btn font-mono"
                          onClick={() => {
                            setSelectedSeason(s.season);
                            setActiveTab('pitch');
                          }}
                          aria-label={`View tactical pitch for ${s.season}`}
                        >
                          View Pitch
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 7. Tab View 4: In-Browser SQL WASM Laboratory */}
        {activeTab === 'lab' && (
          <div
            role="tabpanel"
            id="vault-panel-lab"
            aria-labelledby="vault-tab-lab"
            tabIndex={0}
            className="vault-sidebar-card"
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={16} weight="bold" style={{ color: 'var(--text-primary)' }} />
                  <h3 style={{ fontSize: '14px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    Client-Side Python & SQL Sandbox (WebAssembly / Pyodide)
                  </h3>
                </div>
                <p className="zinc" style={{ fontSize: '12px', margin: '4px 0 0 0' }}>
                  Runs completely inside your browser via WebAssembly with zero server dependencies.
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <a
                  href="/lab.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="wire-btn font-mono"
                  style={{
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <ArrowUpRight size={13} weight="bold" />
                  <span>Open Full Lab in New Tab</span>
                </a>
              </div>
            </div>

            <div style={{
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              border: '1px solid var(--border-subtle)',
              height: '700px',
              backgroundColor: 'var(--bg-surface-0)'
            }}>
              <iframe
                src="/lab.html"
                title="Marimo WebAssembly Laboratory"
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  display: 'block'
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 8. Dedicated Historical Player Detail Modal */}
      {inspectedHistoricalPlayer && (
        <HistoricalPlayerDetailModal
          player={inspectedHistoricalPlayer}
          onClose={() => setInspectedHistoricalPlayer(null)}
        />
      )}
    </div>
  );
}

// Subcomponent: Direction J Historical Player Token
function HistoricalPlayerCard({ player, isCaptain, onInspect }) {
  if (!player) return null;

  const pos = (player.position || 'MID').toUpperCase();
  const cost = Number(player.now_cost || 0).toFixed(1);

  return (
    <div
      className={`wire-token vault-token ${isCaptain ? 'is-captain' : ''}`}
    >
      <button
        type="button"
        className="wire-token-main"
        aria-label={`${player.web_name}, ${pos}, £${cost}m, ${player.total_points} pts`}
        onClick={() => onInspect && onInspect(player)}
        title={`Inspect ${player.web_name} (${player.season})`}
      >
        <span className="wire-token-name">{player.web_name}</span>
        <span className="wire-token-pts font-mono">
          {player.total_points}
          <span className="wire-token-unit">pts</span>
        </span>
      </button>

      <div className="wire-token-meta">
        <span className="wire-token-fixture font-mono">
          [{pos}] · {player.team_name} · £{cost}m
        </span>
        {isCaptain && (
          <span className="wire-token-armband font-mono" title="Armband pick (Season Top Scorer)">
            [C]
          </span>
        )}
      </div>
    </div>
  );
}

// Subcomponent: Dedicated Historical Player Inspection Modal (Direction J)
function HistoricalPlayerDetailModal({ player, onClose }) {
  if (!player) return null;

  const pos = (player.position || 'MID').toUpperCase();
  const cost = Number(player.now_cost || 0).toFixed(1);

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="historical-player-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        className="modal-container"
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: 'var(--bg-surface-1)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-sm)',
          maxWidth: '520px',
          width: '100%',
          overflow: 'hidden'
        }}
      >
        {/* Header Strip */}
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--bg-surface-2)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="font-mono zinc" style={{ fontSize: '11px', letterSpacing: '0.04em' }}>
              [{player.season} RETROSPECTIVE]
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="wire-btn font-mono"
            style={{ padding: '2px 6px' }}
            aria-label="Close modal"
          >
            <X size={14} weight="bold" />
          </button>
        </div>

        {/* Player Profile Hero */}
        <div style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <div className="font-mono zinc" style={{ fontSize: '12px', marginBottom: '4px' }}>
                [{pos}] · {player.team_name}
              </div>
              <h2 id="historical-player-title" className="cream font-bold" style={{ fontSize: '20px', margin: 0, letterSpacing: '-0.02em' }}>
                {player.first_name ? `${player.first_name} ${player.second_name}` : player.web_name}
              </h2>
            </div>

            <div className="font-mono" style={{ textAlign: 'right' }}>
              <div className="cream font-bold" style={{ fontSize: '26px', lineHeight: 1 }}>
                {player.total_points}
              </div>
              <div className="zinc" style={{ fontSize: '10px', marginTop: '2px' }}>
                TOTAL POINTS
              </div>
            </div>
          </div>

          {/* Key Campaign Stats Bento Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '8px',
            marginBottom: '16px'
          }}>
            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>CAMPAIGN PRICE</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                £{cost}m
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>GOALS SCORED</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                {player.goals_scored || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>ASSISTS LOGGED</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                {player.assists || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>CLEAN SHEETS</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                {player.clean_sheets || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>BONUS POINTS</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                {player.bonus || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xs)', padding: '8px 10px' }}>
              <div className="zinc font-mono" style={{ fontSize: '10px' }}>MINUTES PLAYED</div>
              <div className="font-mono cream font-bold" style={{ fontSize: '15px', marginTop: '2px' }}>
                {player.minutes ? Number(player.minutes).toLocaleString() : '-'}
              </div>
            </div>
          </div>

          {/* Squad Status Strip */}
          <div style={{
            backgroundColor: 'var(--bg-surface-2)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xs)',
            padding: '8px 12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Trophy size={14} weight="bold" style={{ color: 'var(--text-primary)' }} />
              <span className="cream" style={{ fontSize: '11px', fontWeight: 600 }}>
                {player.is_starter === 1 ? 'Official Dream Team XI Starter' : 'Dream Team Squad Bench'}
              </span>
            </div>
            <span className="font-mono zinc" style={{ fontSize: '11px' }}>
              {player.season} Campaign
            </span>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '10px 16px',
          backgroundColor: 'var(--bg-surface-2)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            type="button"
            className="wire-btn font-mono"
            onClick={onClose}
          >
            Close Retrospective
          </button>
        </div>
      </div>
    </div>
  );
}
