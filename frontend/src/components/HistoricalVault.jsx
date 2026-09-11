import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Trophy,
  Crown,
  SoccerBall,
  Calendar,
  TrendUp,
  CaretLeft,
  CaretRight,
  CaretUp,
  CaretDown,
  Medal,
  Sparkle,
  Database,
  Terminal,
  ArrowsLeftRight,
  ArrowUpRight,
  X,
  Star,
  User,
  ShieldCheck,
  Flame,
  Funnel
} from '@phosphor-icons/react';
import vaultData from '../data/historical_vault.json';

// Premier League club kit stripe identifiers matching the terminal design system
const getClubKitClass = (teamName) => {
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

export default function HistoricalVault({ onInspectPlayer }) {
  const seasonsList = vaultData.seasons || [];
  const [selectedSeason, setSelectedSeason] = useState(seasonsList[0]?.season || '2025-26');
  const [activeTab, setActiveTab] = useState('pitch'); // 'pitch' | 'records' | 'comparison' | 'lab'
  const [inspectedHistoricalPlayer, setInspectedHistoricalPlayer] = useState(null);
  const [recordsFilter, setRecordsFilter] = useState('all'); // 'all' | 'points' | 'goals'

  // Sorting state for the 10-season comparative table
  const [sortKey, setSortKey] = useState('season');
  const [sortDir, setSortDir] = useState('desc');

  // Pill scroll track & element references for automatic smooth alignment
  const trackRef = useRef(null);
  const pillRefs = useRef({});

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
  // In seasonsList, index 0 is most recent (e.g. 2025-26), index 9 is oldest (2016-17)
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

  // Auto-scroll the active season pill into view whenever selection changes
  useEffect(() => {
    const activeEl = pillRefs.current[selectedSeason];
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
  };

  return (
    <div className="historical-vault-view surface-scope-vault" style={{ padding: '0 0 40px 0' }}>
      {/* 1. Header Banner & View Mode Switcher with Responsive Labels */}
      <div className="vault-hero-bar">
        <div className="vault-hero-inner">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="font-mono" style={{
                fontSize: '10px',
                fontWeight: 800,
                color: 'var(--accent-amber)',
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                padding: '3px 8px',
                borderRadius: 'var(--radius-xs)',
                letterSpacing: '0.06em'
              }}>
                HISTORICAL VAULT · 10 SEASONS ARCHIVE
              </span>
              <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                2016-17 to 2025-26
              </span>
            </div>
            <h1 style={{
              fontSize: 'clamp(18px, 2.2vw, 22px)',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              margin: 0
            }}>
              Premier League Time Machine
            </h1>
            <p style={{ fontSize: 'clamp(11.5px, 1.2vw, 12.5px)', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
              Explore official season-by-season Dream Teams on the tactical pitch, all-time record hauls, and league trends.
            </p>
          </div>

          {/* Segmented View Switcher with Full ARIA tablist Semantics & Adaptive Labels */}
          <div
            className="vault-tab-rail"
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
              className={`hud-segment-btn ${activeTab === 'pitch' ? 'active' : ''}`}
              onClick={() => setActiveTab('pitch')}
            >
              <Trophy size={14} weight={activeTab === 'pitch' ? 'fill' : 'bold'} />
              <span className="tab-label-full">Dream Team Pitch</span>
              <span className="tab-label-short">Pitch</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-records"
              aria-selected={activeTab === 'records'}
              aria-controls="vault-panel-records"
              tabIndex={activeTab === 'records' ? 0 : -1}
              className={`hud-segment-btn ${activeTab === 'records' ? 'active' : ''}`}
              onClick={() => setActiveTab('records')}
            >
              <Medal size={14} weight={activeTab === 'records' ? 'fill' : 'bold'} />
              <span className="tab-label-full">All-Time Records</span>
              <span className="tab-label-short">Records</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-comparison"
              aria-selected={activeTab === 'comparison'}
              aria-controls="vault-panel-comparison"
              tabIndex={activeTab === 'comparison' ? 0 : -1}
              className={`hud-segment-btn ${activeTab === 'comparison' ? 'active' : ''}`}
              onClick={() => setActiveTab('comparison')}
            >
              <Calendar size={14} weight={activeTab === 'comparison' ? 'fill' : 'bold'} />
              <span className="tab-label-full">10-Season Overview</span>
              <span className="tab-label-short">Overview</span>
            </button>
            <button
              type="button"
              role="tab"
              id="vault-tab-lab"
              aria-selected={activeTab === 'lab'}
              aria-controls="vault-panel-lab"
              tabIndex={activeTab === 'lab' ? 0 : -1}
              className={`hud-segment-btn ${activeTab === 'lab' ? 'active' : ''}`}
              onClick={() => setActiveTab('lab')}
            >
              <Terminal size={14} weight={activeTab === 'lab' ? 'fill' : 'bold'} />
              <span className="tab-label-full">Marimo & SQL Lab</span>
              <span className="tab-label-short">SQL Lab</span>
            </button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 clamp(12px, 2vw, 20px)' }}>
        {/* 2. Season Selector Rail (Auto-centering Pills & Responsive Buttons) */}
        <div className="vault-season-rail-container">
          {/* Left Arrow: Moves to Newer Seasons (left in the visual array) */}
          <button
            type="button"
            className="vault-season-nav-btn"
            onClick={handleNewerSeason}
            disabled={currentSeasonIndex <= 0}
            title="Newer Season"
            aria-label="Navigate to newer season"
          >
            <CaretLeft size={14} weight="bold" />
            <span>Newer</span>
          </button>

          {/* Season Pills Scroll Track */}
          <div className="vault-season-scroll-track" ref={trackRef}>
            {seasonsList.map(s => {
              const isSelected = s.season === selectedSeason;
              return (
                <button
                  key={s.season}
                  ref={el => { pillRefs.current[s.season] = el; }}
                  type="button"
                  onClick={() => setSelectedSeason(s.season)}
                  className={`vault-season-pill ${isSelected ? 'active' : ''}`}
                  aria-pressed={isSelected}
                  aria-label={`Select season ${s.season}`}
                >
                  {s.season}
                </button>
              );
            })}
          </div>

          {/* Right Arrow: Moves to Older Seasons (right in the visual array) */}
          <button
            type="button"
            className="vault-season-nav-btn"
            onClick={handleOlderSeason}
            disabled={currentSeasonIndex >= seasonsList.length - 1}
            title="Older Season"
            aria-label="Navigate to older season"
          >
            <span>Older</span>
            <CaretRight size={14} weight="bold" />
          </button>
        </div>

        {/* 3. Season KPI Deck (Adaptive HUD Ribbon: 4-col desktop, 2x2 tablet & mobile) */}
        <div className="vault-hud-ribbon">
          {/* Tile 1: Campaign Profile */}
          <div className="hud-tile hud-tile-strategy">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">CAMPAIGN PROFILE</span>
              <span className="hud-strategy-badge font-mono" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)' }}>
                {selectedSeason}
              </span>
            </div>
            <div className="hud-directive-text" style={{ padding: '2px 0' }}>
              <span className="hud-highlight-text font-mono" style={{ fontSize: '15px' }}>
                38 Gameweeks
              </span>
              <span className="hud-sub-text font-mono" style={{ fontSize: '11px', marginTop: '2px' }}>
                {currentSeasonMeta?.total_players?.toLocaleString() || '0'} Players
              </span>
            </div>
          </div>

          {/* Tile 2: League Firepower */}
          <div className="hud-tile hud-tile-chip">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">LEAGUE FIREPOWER</span>
              <span className="hud-chip-live-badge font-mono" style={{ backgroundColor: 'var(--accent-cyan)', color: 'var(--text-inverse)' }}>
                OFFICIAL
              </span>
            </div>
            <div className="hud-directive-text" style={{ padding: '2px 0' }}>
              <span className="hud-highlight-text font-mono" style={{ fontSize: '15px', color: 'var(--accent-cyan)' }}>
                {currentSeasonMeta?.total_goals?.toLocaleString() || '0'} Goals
              </span>
              <span className="hud-sub-text font-mono" style={{ fontSize: '11px', marginTop: '2px' }}>
                {currentSeasonMeta?.total_assists?.toLocaleString() || '0'} Assists logged
              </span>
            </div>
          </div>

          {/* Tile 3: Golden Boot Winner */}
          <div className="hud-tile hud-tile-directive">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">GOLDEN BOOT</span>
              <span className="hud-chip-idle-badge font-mono">
                {currentSeasonMeta?.top_scorer_goals} GOALS
              </span>
            </div>
            <div className="hud-directive-text" style={{ padding: '2px 0' }}>
              <span className="hud-highlight-text" style={{ fontSize: '15px', color: 'var(--accent-crimson)', fontWeight: 800 }}>
                {currentSeasonMeta?.top_scorer_name || '-'}
              </span>
              <span className="hud-sub-text font-mono" style={{ fontSize: '11px', marginTop: '2px' }}>
                Top goalscorer in Premier League
              </span>
            </div>
          </div>

          {/* Tile 4: Top Point Hauler / Season MVP */}
          <div className="hud-tile hud-tile-scorecard">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">SEASON MVP</span>
              <span className="hud-squad-status font-mono" style={{ color: 'var(--accent-amber)' }}>
                {currentSeasonMeta?.top_points_name || '-'}
              </span>
            </div>
            <div className="hud-scorecard-body">
              <div className="hud-score-main">
                <span className="hud-score-val font-mono" style={{ color: 'var(--accent-amber)', fontSize: '20px', fontWeight: 800 }}>
                  {currentSeasonMeta?.top_points || 0}
                </span>
                <span className="hud-score-unit font-mono">pts</span>
              </div>
              <div className="hud-score-meta font-mono" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
                <span className="hud-formation-pill">{currentDreamTeam.formation} Formation</span>
              </div>
            </div>
          </div>
        </div>

        {/* 4. Tab View 1: Tactical Pitch (Dream Team) */}
        {activeTab === 'pitch' && (
          <div
            role="tabpanel"
            id="vault-panel-pitch"
            aria-labelledby="vault-tab-pitch"
            tabIndex={0}
            className="vault-pitch-workspace"
          >
            {/* Tactical Pitch Surface */}
            <div className="pitch-container" style={{ minHeight: 'clamp(520px, 62vh, 640px)' }}>
              <div className="pitch-marking-center-line" />
              <div className="pitch-marking-center-circle" />
              <div className="pitch-marking-penalty-top" />
              <div className="pitch-marking-penalty-bottom" />

              {/* Pitch Banner */}
              <div style={{
                position: 'relative',
                zIndex: 10,
                textAlign: 'center',
                backgroundColor: 'rgba(9, 13, 22, 0.82)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 14px',
                margin: '0 auto 10px auto',
                maxWidth: 'fit-content',
                backdropFilter: 'blur(8px)',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)'
              }}>
                <span className="font-mono" style={{ fontSize: 'clamp(9.5px, 1.1vw, 11px)', fontWeight: 800, color: 'var(--accent-emerald)', letterSpacing: '0.04em' }}>
                  {selectedSeason} OFFICIAL DREAM TEAM ({currentDreamTeam.formation}) · {currentDreamTeam.totalStarterPts.toLocaleString()} STARTER PTS
                </span>
              </div>

              {/* Row 1: Goalkeepers */}
              <div className="pitch-row">
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
              <div className="pitch-row">
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
              <div className="pitch-row">
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
              <div className="pitch-row">
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

            {/* Right Sidebar: Dream Team Bench & Squad Breakdown */}
            <div className="vault-bench-totals-container">
              {/* Bench Container */}
              <div style={{
                backgroundColor: 'var(--bg-surface-1)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span className="font-mono" style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: '0.04em' }}>
                    DREAM TEAM BENCH
                  </span>
                  <span className="font-mono" style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 700 }}>
                    +{currentDreamTeam.totalBenchPts} pts
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {currentDreamTeam.bench.map((sub) => (
                    <button
                      key={`${selectedSeason}-sub-${sub.player_code}`}
                      type="button"
                      onClick={() => handlePlayerClick(sub)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        backgroundColor: 'var(--bg-surface-2)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: '9px 12px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.15s ease'
                      }}
                      className="historical-bench-item"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className="font-mono" style={{
                          fontSize: '9.5px',
                          fontWeight: 800,
                          backgroundColor: sub.position === 'GK' ? 'rgba(245, 158, 11, 0.2)' : sub.position === 'DEF' ? 'rgba(59, 130, 246, 0.2)' : sub.position === 'MID' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: sub.position === 'GK' ? 'var(--accent-amber)' : sub.position === 'DEF' ? 'var(--accent-blue)' : sub.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)',
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-xs)'
                        }}>
                          {sub.position}
                        </span>
                        <div>
                          <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {sub.web_name}
                          </div>
                          <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                            {sub.team_name} · £{Number(sub.now_cost).toFixed(1)}m
                          </div>
                        </div>
                      </div>
                      <div className="font-mono" style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>
                          {sub.total_points}
                        </div>
                        <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>pts</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Season Dream Team Summary Card */}
              <div style={{
                backgroundColor: 'var(--bg-surface-1)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '16px'
              }}>
                <span className="font-mono" style={{ fontSize: '10px', fontWeight: 800, color: 'var(--accent-amber)', letterSpacing: '0.04em' }}>
                  CAMPAIGN TOTALS
                </span>
                <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Starters Points</span>
                    <span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      {currentDreamTeam.totalStarterPts} pts
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Full 15-Man Total</span>
                    <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                      {currentDreamTeam.totalStarterPts + currentDreamTeam.totalBenchPts} pts
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Armband Pick (C)</span>
                    <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>
                      {currentSeasonMeta?.top_points_name} ({currentSeasonMeta?.top_points} pts)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 5. Tab View 2: All-Time Records (Hall of Fame) with Responsive Filter */}
        {activeTab === 'records' && (
          <div>
            {/* Filter Toggle on Narrow Screens */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div>
                <h2 style={{ fontSize: '17px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                  Premier League Hall of Fame
                </h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                  The 15 greatest individual seasons in modern Premier League fantasy history.
                </p>
              </div>

              {/* Segmented Filter */}
              <div className="hud-segmented-group" style={{ backgroundColor: 'var(--bg-surface-2)', padding: '3px' }}>
                <button
                  type="button"
                  onClick={() => setRecordsFilter('all')}
                  className={`hud-segment-btn ${recordsFilter === 'all' ? 'active' : ''}`}
                  style={{ padding: '5px 12px', fontSize: '11px', fontWeight: 700 }}
                >
                  All Records
                </button>
                <button
                  type="button"
                  onClick={() => setRecordsFilter('points')}
                  className={`hud-segment-btn ${recordsFilter === 'points' ? 'active' : ''}`}
                  style={{ padding: '5px 12px', fontSize: '11px', fontWeight: 700 }}
                >
                  <Crown size={13} weight="fill" style={{ color: 'var(--accent-amber)' }} />
                  Points
                </button>
                <button
                  type="button"
                  onClick={() => setRecordsFilter('goals')}
                  className={`hud-segment-btn ${recordsFilter === 'goals' ? 'active' : ''}`}
                  style={{ padding: '5px 12px', fontSize: '11px', fontWeight: 700 }}
                >
                  <SoccerBall size={13} weight="fill" style={{ color: 'var(--accent-crimson)' }} />
                  Goals
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
                <div style={{
                  backgroundColor: 'var(--bg-surface-1)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '18px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <div style={{
                      backgroundColor: 'rgba(245, 158, 11, 0.15)',
                      padding: '8px',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Crown size={20} weight="fill" style={{ color: 'var(--accent-amber)' }} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                        All-Time Highest Scoring Seasons
                      </h3>
                      <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                        Top individual player campaigns across 10 seasons
                      </p>
                    </div>
                  </div>

                  <div className="vault-records-scrollable" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {(vaultData.hall_of_fame_points || []).map((record, index) => (
                      <div
                        key={`hof-pts-${index}`}
                        onClick={() => handlePlayerClick(record)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          backgroundColor: index === 0 ? 'rgba(245, 158, 11, 0.09)' : 'var(--bg-surface-2)',
                          border: index === 0 ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                        className="historical-hof-row"
                        title={`Click to inspect ${record.web_name}'s full ${record.season} season haul`}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span className="font-mono" style={{
                            fontSize: '11px',
                            fontWeight: 800,
                            width: '22px',
                            color: index === 0 ? 'var(--accent-amber)' : index < 3 ? 'var(--text-primary)' : 'var(--text-muted)'
                          }}>
                            #{index + 1}
                          </span>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                {record.web_name}
                              </span>
                              <span className="font-mono" style={{
                                fontSize: '9.5px',
                                fontWeight: 800,
                                padding: '1px 5px',
                                borderRadius: 'var(--radius-xs)',
                                backgroundColor: record.position === 'MID' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                color: record.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)'
                              }}>
                                {record.position}
                              </span>
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                              {record.team_name} · <strong style={{ color: 'var(--text-secondary)' }}>{record.season}</strong> · {record.goals_scored}G / {record.assists}A
                            </div>
                          </div>
                        </div>

                        <div className="font-mono" style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '15px', fontWeight: 800, color: index === 0 ? 'var(--accent-amber)' : 'var(--text-primary)' }}>
                            {record.total_points}
                          </span>
                          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '3px' }}>pts</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Hall of Fame: Goals (Golden Boots) */}
              {(recordsFilter === 'all' || recordsFilter === 'goals') && (
                <div style={{
                  backgroundColor: 'var(--bg-surface-1)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '18px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <div style={{
                      backgroundColor: 'rgba(239, 68, 68, 0.15)',
                      padding: '8px',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <SoccerBall size={20} weight="fill" style={{ color: 'var(--accent-crimson)' }} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                        All-Time Most Prolific Goal Seasons
                      </h3>
                      <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                        Most clinical individual finishing campaigns since 2016
                      </p>
                    </div>
                  </div>

                  <div className="vault-records-scrollable" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {(vaultData.hall_of_fame_goals || []).map((record, index) => (
                      <div
                        key={`hof-goals-${index}`}
                        onClick={() => handlePlayerClick(record)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          backgroundColor: index === 0 ? 'rgba(239, 68, 68, 0.09)' : 'var(--bg-surface-2)',
                          border: index === 0 ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                        className="historical-hof-row"
                        title={`Click to inspect ${record.web_name}'s full ${record.season} campaign stats`}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span className="font-mono" style={{
                            fontSize: '11px',
                            fontWeight: 800,
                            width: '22px',
                            color: index === 0 ? 'var(--accent-crimson)' : index < 3 ? 'var(--text-primary)' : 'var(--text-muted)'
                          }}>
                            #{index + 1}
                          </span>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                {record.web_name}
                              </span>
                              <span className="font-mono" style={{
                                fontSize: '9.5px',
                                fontWeight: 800,
                                padding: '1px 5px',
                                borderRadius: 'var(--radius-xs)',
                                backgroundColor: record.position === 'MID' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                color: record.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)'
                              }}>
                                {record.position}
                              </span>
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                              {record.team_name} · <strong style={{ color: 'var(--text-secondary)' }}>{record.season}</strong> · {record.assists} assists
                            </div>
                          </div>
                        </div>

                        <div className="font-mono" style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '15px', fontWeight: 800, color: index === 0 ? 'var(--accent-crimson)' : 'var(--text-primary)' }}>
                            {record.goals_scored}
                          </span>
                          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '3px' }}>goals</span>
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
            className="vault-table-container"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                  10-Season Premier League Comparative Matrix
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                  Click column headers to sort by total goals, assists, top point haulers, or Golden Boot tallies.
                </p>
              </div>
              <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Sorted by: <strong style={{ color: 'var(--accent-amber)' }}>{sortKey.replace('_', ' ').toUpperCase()} ({sortDir.toUpperCase()})</strong>
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
                    className="font-mono sortable-th"
                    onClick={() => handleHeaderSort('total_players')}
                    style={{ padding: '10px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none', minWidth: '90px' }}
                  >
                    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', width: '100%' }}>
                      <span>PLAYERS</span>
                      {sortKey === 'total_players' && (sortDir === 'asc' ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />)}
                    </div>
                  </th>
                  <th className="font-mono" style={{ padding: '10px 12px', textAlign: 'center', minWidth: '100px' }}>
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
                        backgroundColor: isCurrent ? 'rgba(245, 158, 11, 0.08)' : 'transparent',
                        fontSize: '12.5px',
                        transition: 'background-color 0.15s ease'
                      }}
                    >
                      <td className="font-mono vault-table-sticky-col" style={{
                        padding: '12px',
                        fontWeight: 800,
                        color: isCurrent ? 'var(--accent-amber)' : 'var(--text-primary)',
                        borderLeft: isCurrent ? '3px solid var(--accent-amber)' : '3px solid transparent'
                      }}>
                        {s.season}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{s.top_points_name}</span>{' '}
                        <span className="font-mono" style={{ color: 'var(--accent-amber)', fontSize: '11px', fontWeight: 700 }}>({s.top_points} pts)</span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{s.top_scorer_name}</span>{' '}
                        <span className="font-mono" style={{ color: 'var(--accent-crimson)', fontSize: '11px', fontWeight: 700 }}>({s.top_scorer_goals} goals)</span>
                      </td>
                      <td className="font-mono" style={{ padding: '12px', textAlign: 'right', color: 'var(--text-primary)', fontWeight: 600 }}>
                        {s.total_goals?.toLocaleString()}
                      </td>
                      <td className="font-mono" style={{ padding: '12px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                        {s.total_assists?.toLocaleString()}
                      </td>
                      <td className="font-mono" style={{ padding: '12px', textAlign: 'right', color: 'var(--text-muted)' }}>
                        {s.total_players}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <button
                          type="button"
                          className="font-mono"
                          onClick={() => {
                            setSelectedSeason(s.season);
                            setActiveTab('pitch');
                          }}
                          style={{
                            backgroundColor: isCurrent ? 'var(--accent-amber)' : 'var(--bg-surface-2)',
                            color: isCurrent ? 'var(--text-inverse)' : 'var(--text-primary)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-xs)',
                            padding: '4px 10px',
                            fontSize: '10.5px',
                            fontWeight: 700,
                            cursor: 'pointer',
                            transition: 'all 0.15s ease'
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

        {/* 7. Tab View 4: In-Browser Marimo & SQL WASM Laboratory */}
        {activeTab === 'lab' && (
          <div
            role="tabpanel"
            id="vault-panel-lab"
            aria-labelledby="vault-tab-lab"
            tabIndex={0}
            style={{
              backgroundColor: 'var(--bg-surface-1)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={18} weight="bold" style={{ color: 'var(--accent-amber)' }} />
                  <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                    Client-Side Python & SQL Sandbox (WebAssembly / Pyodide)
                  </h3>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                  Runs completely inside your browser via WebAssembly with zero server dependencies. Adjust scoring parameters and execute live SQL queries.
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <a
                  href="/lab.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hud-segment-btn"
                  style={{
                    backgroundColor: 'var(--bg-surface-2)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: 'var(--radius-sm)'
                  }}
                >
                  <ArrowUpRight size={14} weight="bold" />
                  <span>Open Full Lab in New Tab</span>
                </a>
              </div>
            </div>

            <div style={{
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              border: '1px solid var(--border-subtle)',
              height: '700px',
              backgroundColor: '#090D16'
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

        {/* 8. Footer Architecture Integration Strip (Datasette & Marimo Guidance) */}
        <div style={{
          marginTop: '24px',
          backgroundColor: 'var(--bg-surface-1)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 20px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', color: 'var(--accent-cyan)' }}>
              <Database size={16} weight="bold" />
              <span className="font-mono" style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.04em' }}>
                DATASETTE PUBLIC SQL
              </span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              The client-side frontend delivers instantaneous visual exploration with zero server overhead. If you wish to enable arbitrary SQL queries for public analysts, deploy <code className="font-mono" style={{ color: 'var(--accent-emerald)' }}>data/pl_history.db</code> via Datasette on Vercel or Fly.io.
            </p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', color: 'var(--accent-amber)' }}>
              <Terminal size={16} weight="bold" />
              <span className="font-mono" style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.04em' }}>
                MARIMO INTERACTIVE LAB
              </span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Marimo reactive notebooks run Python simulations on <code className="font-mono" style={{ color: 'var(--accent-emerald)' }}>pl_history.db</code>. Export notebooks as client-side WebAssembly (<code className="font-mono">marimo export html-wasm</code>) to embed interactive what-if sliders directly in this dashboard.
            </p>
          </div>
        </div>
      </div>

      {/* 9. Dedicated Historical Player Detail Modal (Retrospective Achievements) */}
      {inspectedHistoricalPlayer && (
        <HistoricalPlayerDetailModal
          player={inspectedHistoricalPlayer}
          onClose={() => setInspectedHistoricalPlayer(null)}
        />
      )}
    </div>
  );
}

// Subcomponent: Historical Player Pitch Card
function HistoricalPlayerCard({ player, isCaptain, onInspect }) {
  if (!player) return null;

  const kitClass = getClubKitClass(player.team_name);
  const pos = (player.position || 'MID').toUpperCase();
  const cost = Number(player.now_cost || 0).toFixed(1);

  return (
    <div
      className={`player-pitch-card vault-player-card ${kitClass}`}
      style={{ cursor: 'pointer' }}
      onClick={() => onInspect && onInspect(player)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onInspect && onInspect(player);
        }
      }}
      title={`${player.web_name} (${player.team_name}) · ${player.total_points} pts in ${player.season}. Click to inspect full season haul.`}
      aria-label={`${player.web_name}, ${player.position}, ${player.team_name}, ${player.total_points} total points`}
    >
      {/* Top Row: Tag + Captain Badge + Cost */}
      <div className="player-card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {isCaptain && (
            <span className="captain-badge font-mono" style={{ fontSize: '9px', padding: '1px 4px' }}>
              [C]
            </span>
          )}
          <span className={`pos-tag pos-${pos.toLowerCase()} font-mono`}>
            {pos}
          </span>
        </div>
        <span className="player-cost font-mono">
          £{cost}m
        </span>
      </div>

      {/* Middle: Player Web Name */}
      <div className="player-web-name" style={{ fontWeight: 800, padding: '2px 0' }}>
        {player.web_name}
      </div>

      {/* Team Name */}
      <div style={{ fontSize: 'clamp(8.5px, 1vw, 10px)', color: 'var(--text-muted)', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {player.team_name}
      </div>

      {/* Season Total Points */}
      <div className="player-xp-banner" style={{ backgroundColor: 'var(--bg-surface-subtle)', borderRadius: 'var(--radius-xs)', padding: '2px 0' }}>
        <span className="xp-val font-mono" style={{ fontWeight: 800, color: 'var(--accent-amber)' }}>
          {player.total_points}
        </span>
        <span className="xp-unit font-mono" style={{ fontSize: '9px', marginLeft: '2px', color: 'var(--text-muted)' }}>
          pts
        </span>
      </div>
    </div>
  );
}

// Subcomponent: Dedicated Historical Player Inspection Modal
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
          borderRadius: 'var(--radius-lg)',
          maxWidth: '520px',
          width: '100%',
          overflow: 'hidden',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8)'
        }}
      >
        {/* Header Strip */}
        <div style={{
          padding: '16px 20px',
          backgroundColor: 'var(--bg-surface-2)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="font-mono" style={{
              fontSize: '10px',
              fontWeight: 800,
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--accent-amber)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
              letterSpacing: '0.04em'
            }}>
              {player.season} CAMPAIGN RETROSPECTIVE
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="hud-segment-btn"
            style={{ padding: '4px 8px', borderRadius: 'var(--radius-xs)', cursor: 'pointer' }}
            aria-label="Close modal"
          >
            <X size={16} weight="bold" />
          </button>
        </div>

        {/* Player Profile Hero */}
        <div style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span className={`pos-tag pos-${pos.toLowerCase()} font-mono`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                  {pos}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  {player.team_name}
                </span>
              </div>
              <h2 id="historical-player-title" style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
                {player.first_name ? `${player.first_name} ${player.second_name}` : player.web_name}
              </h2>
            </div>

            <div className="font-mono" style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '28px', fontWeight: 900, color: 'var(--accent-amber)', lineHeight: 1 }}>
                {player.total_points}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                TOTAL POINTS
              </div>
            </div>
          </div>

          {/* Key Campaign Stats Bento Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '10px',
            marginBottom: '16px'
          }}>
            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>CAMPAIGN PRICE</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
                £{cost}m
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>GOALS SCORED</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-crimson)', marginTop: '2px' }}>
                {player.goals_scored || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>ASSISTS LOGGED</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '2px' }}>
                {player.assists || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>CLEAN SHEETS</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '2px' }}>
                {player.clean_sheets || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>BONUS POINTS (BPS)</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-amber)', marginTop: '2px' }}>
                {player.bonus || 0}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-2)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>MINUTES PLAYED</div>
              <div className="font-mono" style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-secondary)', marginTop: '2px' }}>
                {player.minutes ? Number(player.minutes).toLocaleString() : '-'}
              </div>
            </div>
          </div>

          {/* Squad Status Pill */}
          <div style={{
            backgroundColor: 'var(--bg-surface-2)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Trophy size={16} weight="fill" style={{ color: 'var(--accent-amber)' }} />
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {player.is_starter === 1 ? 'Official Dream Team XI Starter' : 'Dream Team Squad Bench'}
              </span>
            </div>
            <span className="font-mono" style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 700 }}>
              {player.season} Campaign
            </span>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 20px',
          backgroundColor: 'var(--bg-surface-2)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            type="button"
            className="hud-segment-btn"
            onClick={onClose}
            style={{
              padding: '6px 16px',
              fontSize: '12px',
              fontWeight: 700,
              backgroundColor: 'var(--bg-surface-1)',
              color: 'var(--text-primary)',
              cursor: 'pointer'
            }}
          >
            Close Retrospective
          </button>
        </div>
      </div>
    </div>
  );
}
