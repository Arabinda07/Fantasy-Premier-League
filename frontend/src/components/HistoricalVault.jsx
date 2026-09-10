import React, { useState, useMemo } from 'react';
import {
  Trophy,
  Crown,
  SoccerBall,
  Calendar,
  TrendUp,
  CaretLeft,
  CaretRight,
  Medal,
  Sparkle,
  Database,
  Terminal,
  ArrowsLeftRight
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
  const [selectedSeason, setSelectedSeason] = useState(seasonsList[0]?.season || '2024-25');
  const [activeTab, setActiveTab] = useState('pitch'); // 'pitch' | 'records' | 'comparison'

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
  const handlePrevSeason = () => {
    if (currentSeasonIndex < seasonsList.length - 1) {
      setSelectedSeason(seasonsList[currentSeasonIndex + 1].season);
    }
  };
  const handleNextSeason = () => {
    if (currentSeasonIndex > 0) {
      setSelectedSeason(seasonsList[currentSeasonIndex - 1].season);
    }
  };

  return (
    <div className="historical-vault-view surface-scope-vault" style={{ padding: '0 0 32px 0' }}>
      {/* 1. Header Banner & View Mode Switcher */}
      <div className="vault-hero-bar" style={{
        backgroundColor: 'var(--bg-surface-1)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '16px 20px',
        marginBottom: '20px'
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="font-mono" style={{
                fontSize: '10px',
                fontWeight: 800,
                color: 'var(--accent-amber)',
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-xs)',
                letterSpacing: '0.05em'
              }}>
                HISTORICAL VAULT · 10 SEASONS ARCHIVE
              </span>
              <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                2016-17 to 2025-26
              </span>
            </div>
            <h1 style={{
              fontSize: '20px',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              margin: 0
            }}>
              Premier League Time Machine
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
              Explore official season-by-season Dream Teams on the tactical pitch, all-time record hauls, and league trends.
            </p>
          </div>

          {/* Segmented View Switcher */}
          <div className="hud-segmented-group" role="group" aria-label="Vault View Modes" style={{ backgroundColor: 'var(--bg-surface-2)' }}>
            <button
              type="button"
              className={`hud-segment-btn ${activeTab === 'pitch' ? 'active' : ''}`}
              onClick={() => setActiveTab('pitch')}
            >
              <Trophy size={13} weight={activeTab === 'pitch' ? 'fill' : 'bold'} />
              <span>Dream Team Pitch</span>
            </button>
            <button
              type="button"
              className={`hud-segment-btn ${activeTab === 'records' ? 'active' : ''}`}
              onClick={() => setActiveTab('records')}
            >
              <Medal size={13} weight={activeTab === 'records' ? 'fill' : 'bold'} />
              <span>All-Time Records</span>
            </button>
            <button
              type="button"
              className={`hud-segment-btn ${activeTab === 'comparison' ? 'active' : ''}`}
              onClick={() => setActiveTab('comparison')}
            >
              <Calendar size={13} weight={activeTab === 'comparison' ? 'fill' : 'bold'} />
              <span>10-Season Overview</span>
            </button>
            <button
              type="button"
              className={`hud-segment-btn ${activeTab === 'lab' ? 'active' : ''}`}
              onClick={() => setActiveTab('lab')}
            >
              <Terminal size={13} weight={activeTab === 'lab' ? 'fill' : 'bold'} />
              <span>Marimo & SQL Lab</span>
            </button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
        {/* 2. Season Selector Rail (Instant Interactive Pills) */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'var(--bg-surface-1)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '8px 12px',
          marginBottom: '20px',
          overflowX: 'auto'
        }}>
          <button
            type="button"
            className="hud-segment-btn"
            onClick={handlePrevSeason}
            disabled={currentSeasonIndex >= seasonsList.length - 1}
            style={{ padding: '6px 10px', opacity: currentSeasonIndex >= seasonsList.length - 1 ? 0.35 : 1 }}
            title="Earlier Season"
            aria-label="Previous Season"
          >
            <CaretLeft size={14} weight="bold" />
            <span style={{ fontSize: '11px' }}>Earlier</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1, overflowX: 'auto', padding: '2px 0' }}>
            {seasonsList.map(s => {
              const isSelected = s.season === selectedSeason;
              return (
                <button
                  key={s.season}
                  type="button"
                  onClick={() => setSelectedSeason(s.season)}
                  className={`font-mono ${isSelected ? 'active' : ''}`}
                  style={{
                    backgroundColor: isSelected ? 'var(--accent-amber)' : 'var(--bg-surface-2)',
                    color: isSelected ? 'var(--text-inverse)' : 'var(--text-secondary)',
                    border: isSelected ? '1px solid var(--accent-amber)' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '5px 10px',
                    fontSize: '11px',
                    fontWeight: isSelected ? 800 : 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {s.season}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            className="hud-segment-btn"
            onClick={handleNextSeason}
            disabled={currentSeasonIndex <= 0}
            style={{ padding: '6px 10px', opacity: currentSeasonIndex <= 0 ? 0.35 : 1 }}
            title="Later Season"
            aria-label="Next Season"
          >
            <span style={{ fontSize: '11px' }}>Later</span>
            <CaretRight size={14} weight="bold" />
          </button>
        </div>

        {/* 3. Season KPI Deck (4-Tile HUD matching DESIGN.md) */}
        <div className="matchday-hud-grid" style={{ marginBottom: '20px' }}>
          {/* Tile 1: Campaign Profile */}
          <div className="hud-tile hud-tile-strategy">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">CAMPAIGN PROFILE</span>
              <span className="hud-strategy-badge font-mono" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)' }}>
                {selectedSeason}
              </span>
            </div>
            <div className="hud-directive-text" style={{ padding: '4px 0' }}>
              <span className="hud-highlight-text font-mono" style={{ fontSize: '15px' }}>
                38 Gameweeks
              </span>
              <span className="hud-sub-text font-mono" style={{ fontSize: '11px' }}>
                {currentSeasonMeta?.total_players?.toLocaleString() || '0'} Registered Players
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
            <div className="hud-directive-text" style={{ padding: '4px 0' }}>
              <span className="hud-highlight-text font-mono" style={{ fontSize: '15px', color: 'var(--accent-cyan)' }}>
                {currentSeasonMeta?.total_goals?.toLocaleString() || '0'} Goals
              </span>
              <span className="hud-sub-text font-mono" style={{ fontSize: '11px' }}>
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
            <div className="hud-directive-text" style={{ padding: '4px 0' }}>
              <span className="hud-highlight-text" style={{ fontSize: '15px', color: 'var(--accent-crimson)' }}>
                {currentSeasonMeta?.top_scorer_name || '—'}
              </span>
              <span className="hud-sub-text" style={{ fontSize: '11px' }}>
                Top goalscorer in the Premier League
              </span>
            </div>
          </div>

          {/* Tile 4: Top Point Hauler / Season MVP */}
          <div className="hud-tile hud-tile-scorecard">
            <div className="hud-tile-header">
              <span className="hud-tile-eyebrow font-mono">SEASON MVP</span>
              <span className="hud-squad-status font-mono" style={{ color: 'var(--accent-amber)' }}>
                {currentSeasonMeta?.top_points} PTS
              </span>
            </div>
            <div className="hud-scorecard-body">
              <div className="hud-score-main">
                <span className="hud-score-val font-mono" style={{ color: 'var(--accent-amber)', fontSize: '20px' }}>
                  {currentSeasonMeta?.top_points_name || '—'}
                </span>
                <span className="hud-score-unit font-mono">pts</span>
              </div>
              <div className="hud-score-meta font-mono">
                <span className="hud-formation-pill">{currentDreamTeam.formation} Formation</span>
              </div>
            </div>
          </div>
        </div>

        {/* 4. Tab View 1: Tactical Pitch (Dream Team) */}
        {activeTab === 'pitch' && (
          <div className="pitch-workspace" style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px' }}>
            {/* Tactical Pitch Surface */}
            <div className="pitch-container" style={{ minHeight: '620px' }}>
              <div className="pitch-marking-center-line" />
              <div className="pitch-marking-center-circle" />
              <div className="pitch-marking-penalty-top" />
              <div className="pitch-marking-penalty-bottom" />

              {/* Pitch Banner */}
              <div style={{
                position: 'relative',
                zIndex: 10,
                textAlign: 'center',
                backgroundColor: 'rgba(9, 13, 22, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 'var(--radius-xs)',
                padding: '4px 12px',
                margin: '0 auto 10px auto',
                maxWidth: 'fit-content'
              }}>
                <span className="font-mono" style={{ fontSize: '11px', fontWeight: 800, color: 'var(--accent-emerald)', letterSpacing: '0.04em' }}>
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
                    onInspect={onInspectPlayer}
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
                    onInspect={onInspectPlayer}
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
                    onInspect={onInspectPlayer}
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
                    onInspect={onInspectPlayer}
                  />
                ))}
              </div>
            </div>

            {/* Right Sidebar: Dream Team Bench & Squad Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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
                  {currentDreamTeam.bench.map((sub, idx) => (
                    <div
                      key={`${selectedSeason}-sub-${sub.player_code}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        backgroundColor: 'var(--bg-surface-2)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="font-mono" style={{
                          fontSize: '9.5px',
                          fontWeight: 800,
                          backgroundColor: sub.position === 'GK' ? 'rgba(245, 158, 11, 0.2)' : sub.position === 'DEF' ? 'rgba(59, 130, 246, 0.2)' : sub.position === 'MID' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: sub.position === 'GK' ? 'var(--accent-amber)' : sub.position === 'DEF' ? 'var(--accent-blue)' : sub.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)',
                          padding: '2px 5px',
                          borderRadius: 'var(--radius-xs)'
                        }}>
                          {sub.position}
                        </span>
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {sub.web_name}
                          </div>
                          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                            {sub.team_name} · £{Number(sub.now_cost).toFixed(1)}m
                          </div>
                        </div>
                      </div>
                      <div className="font-mono" style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)' }}>
                          {sub.total_points}
                        </div>
                        <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>pts</div>
                      </div>
                    </div>
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
                <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
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

              {/* Data & Query Notice */}
              <div style={{
                backgroundColor: 'var(--bg-surface-2)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '12px',
                fontSize: '11px',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', color: 'var(--text-primary)', fontWeight: 700 }}>
                  <Database size={14} weight="bold" style={{ color: 'var(--accent-cyan)' }} />
                  <span>SQLite & Datasette Ready</span>
                </div>
                Compiled directly from 10 complete seasons in <code className="font-mono" style={{ color: 'var(--accent-emerald)' }}>data/pl_history.db</code>.
              </div>
            </div>
          </div>
        )}

        {/* 5. Tab View 2: All-Time Records (Hall of Fame) */}
        {activeTab === 'records' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
            {/* Hall of Fame: Points */}
            <div style={{
              backgroundColor: 'var(--bg-surface-1)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Crown size={18} weight="fill" style={{ color: 'var(--accent-amber)' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                    All-Time Highest Scoring Seasons
                  </h3>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0 }}>
                    Top individual player campaigns across 10 Premier League seasons
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(vaultData.hall_of_fame_points || []).slice(0, 10).map((record, index) => (
                  <div
                    key={`hof-pts-${index}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      backgroundColor: index === 0 ? 'rgba(245, 158, 11, 0.08)' : 'var(--bg-surface-2)',
                      border: index === 0 ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '8px 12px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="font-mono" style={{
                        fontSize: '11px',
                        fontWeight: 800,
                        width: '20px',
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
                            padding: '1px 4px',
                            borderRadius: 'var(--radius-xs)',
                            backgroundColor: record.position === 'MID' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: record.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)'
                          }}>
                            {record.position}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {record.team_name} · {record.season} · {record.goals_scored}G / {record.assists}A
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

            {/* Hall of Fame: Goals (Golden Boots) */}
            <div style={{
              backgroundColor: 'var(--bg-surface-1)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <SoccerBall size={18} weight="fill" style={{ color: 'var(--accent-crimson)' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                    All-Time Most Prolific Goal Seasons
                  </h3>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0 }}>
                    Most clinical individual finishing campaigns since 2016
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(vaultData.hall_of_fame_goals || []).slice(0, 10).map((record, index) => (
                  <div
                    key={`hof-goals-${index}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      backgroundColor: index === 0 ? 'rgba(239, 68, 68, 0.08)' : 'var(--bg-surface-2)',
                      border: index === 0 ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '8px 12px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="font-mono" style={{
                        fontSize: '11px',
                        fontWeight: 800,
                        width: '20px',
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
                            padding: '1px 4px',
                            borderRadius: 'var(--radius-xs)',
                            backgroundColor: record.position === 'MID' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: record.position === 'MID' ? 'var(--accent-emerald)' : 'var(--accent-crimson)'
                          }}>
                            {record.position}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {record.team_name} · {record.season} · {record.assists} assists
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
          </div>
        )}

        {/* 6. Tab View 3: 10-Season Overview Table */}
        {activeTab === 'comparison' && (
          <div style={{
            backgroundColor: 'var(--bg-surface-1)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px',
            overflowX: 'auto'
          }}>
            <div style={{ marginBottom: '16px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                10-Season Premier League Comparative Matrix
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                Complete historical breakdown of goals, assists, top point haulers, and Golden Boot winners.
              </p>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '11px' }}>
                  <th className="font-mono" style={{ padding: '8px 12px' }}>SEASON</th>
                  <th className="font-mono" style={{ padding: '8px 12px' }}>TOP POINTS HAULER</th>
                  <th className="font-mono" style={{ padding: '8px 12px' }}>GOLDEN BOOT</th>
                  <th className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>TOTAL GOALS</th>
                  <th className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>TOTAL ASSISTS</th>
                  <th className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>PLAYERS</th>
                  <th className="font-mono" style={{ padding: '8px 12px', textAlign: 'center' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {seasonsList.map(s => {
                  const isCurrent = s.season === selectedSeason;
                  return (
                    <tr
                      key={`comp-row-${s.season}`}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isCurrent ? 'rgba(245, 158, 11, 0.08)' : 'transparent',
                        fontSize: '12px'
                      }}
                    >
                      <td className="font-mono" style={{ padding: '10px 12px', fontWeight: 800, color: isCurrent ? 'var(--accent-amber)' : 'var(--text-primary)' }}>
                        {s.season}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{s.top_points_name}</span>{' '}
                        <span className="font-mono" style={{ color: 'var(--accent-amber)', fontSize: '11px' }}>({s.top_points} pts)</span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{s.top_scorer_name}</span>{' '}
                        <span className="font-mono" style={{ color: 'var(--accent-crimson)', fontSize: '11px' }}>({s.top_scorer_goals} goals)</span>
                      </td>
                      <td className="font-mono" style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-primary)' }}>
                        {s.total_goals?.toLocaleString()}
                      </td>
                      <td className="font-mono" style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                        {s.total_assists?.toLocaleString()}
                      </td>
                      <td className="font-mono" style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
                        {s.total_players}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <button
                          type="button"
                          className="font-mono"
                          onClick={() => {
                            setSelectedSeason(s.season);
                            setActiveTab('pitch');
                          }}
                          style={{
                            backgroundColor: 'var(--bg-surface-2)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-primary)',
                            borderRadius: 'var(--radius-xs)',
                            padding: '3px 8px',
                            fontSize: '10px',
                            fontWeight: 700,
                            cursor: 'pointer'
                          }}
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

        {/* Tab View 4: In-Browser Marimo & SQL WASM Laboratory */}
        {activeTab === 'lab' && (
          <div style={{
            backgroundColor: 'var(--bg-surface-1)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px'
          }}>
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
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 700
                  }}
                >
                  <ArrowUpRight size={13} weight="bold" />
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

        {/* 7. Footer Architecture Integration Strip (Datasette & Marimo Guidance) */}
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
      className={`player-pitch-card ${kitClass}`}
      style={{ cursor: 'pointer' }}
      onClick={() => onInspect && onInspect(player)}
      title={`${player.web_name} (${player.team_name}) · ${player.total_points} total points in ${player.season}`}
    >
      {/* Top Row: Tag + Captain Badge + Cost */}
      <div className="player-card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {isCaptain && (
            <span className="captain-badge font-mono" style={{ fontSize: '9px', padding: '1px 4px' }}>
              [C]
            </span>
          )}
          <span className={`pos-tag pos-${pos.toLowerCase()} font-mono`} style={{ fontSize: '9px', padding: '1px 4px' }}>
            {pos}
          </span>
        </div>
        <span className="player-cost font-mono" style={{ fontSize: '10px' }}>
          £{cost}m
        </span>
      </div>

      {/* Middle: Player Web Name */}
      <div className="player-web-name" style={{ fontSize: '12px', fontWeight: 800, padding: '2px 0' }}>
        {player.web_name}
      </div>

      {/* Team Name */}
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px' }}>
        {player.team_name}
      </div>

      {/* Season Total Points */}
      <div className="player-xp-banner" style={{ backgroundColor: 'var(--bg-surface-subtle)', borderRadius: 'var(--radius-xs)', padding: '2px 0' }}>
        <span className="xp-val font-mono" style={{ fontSize: '12px', fontWeight: 800, color: 'var(--accent-amber)' }}>
          {player.total_points}
        </span>
        <span className="xp-unit font-mono" style={{ fontSize: '9px', marginLeft: '2px', color: 'var(--text-muted)' }}>
          pts
        </span>
      </div>
    </div>
  );
}
