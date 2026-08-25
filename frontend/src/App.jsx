import React, { useState, lazy, Suspense } from 'react';
import Header from './components/Header';
import TacticalPitch from './components/TacticalPitch';
import TransferWorkbench from './components/TransferWorkbench';
import FixtureHeatmap from './components/FixtureHeatmap';
import MarketVelocityTicker from './components/MarketVelocityTicker';

// Lazy-load Recharts heavy charting component on demand
const PlayerDNAInspector = lazy(() => import('./components/PlayerDNAInspector'));

// Import live data payloads
import liveMatchdayData from './data/live_matchday_gw2.json';
import allPlayersData from './data/players_full.json';
import fixturesData from './data/fixtures_all.json';
import teamsData from './data/teams_all.json';

export default function App() {
  const [activeTab, setActiveTab] = useState('pitch');
  const [selectedStrategy, setSelectedStrategy] = useState('pure_xp');

  // Squad State (Allowing interactive starter / bench swaps)
  const [starters, setStarters] = useState(liveMatchdayData.starters || []);
  const [bench, setBench] = useState(liveMatchdayData.bench || []);
  const [selectedSwapPlayer, setSelectedSwapPlayer] = useState(null);
  const [inspectedPlayer, setInspectedPlayer] = useState(null);

  // Handle interactive player selection and swap
  const handleSelectPlayer = (player) => {
    if (!selectedSwapPlayer) {
      setSelectedSwapPlayer(player);
    } else if (selectedSwapPlayer.player_code === player.player_code) {
      setSelectedSwapPlayer(null); // Deselect
    } else {
      // Perform swap between starter and bench
      const isSelectedStarter = starters.some(p => p.player_code === selectedSwapPlayer.player_code);
      const isTargetStarter = starters.some(p => p.player_code === player.player_code);

      if (isSelectedStarter !== isTargetStarter) {
        // One is starter, one is bench -> Valid swap!
        const starterObj = isSelectedStarter ? selectedSwapPlayer : player;
        const benchObj = isSelectedStarter ? player : selectedSwapPlayer;

        const newStarters = starters.map(p =>
          p.player_code === starterObj.player_code
            ? { ...benchObj, is_starter: true, is_captain: starterObj.is_captain, is_vice_captain: starterObj.is_vice_captain, bench_order: null }
            : p
        );

        const newBench = bench.map(p =>
          p.player_code === benchObj.player_code
            ? { ...starterObj, is_starter: false, is_captain: false, is_vice_captain: false, bench_order: benchObj.bench_order }
            : p
        );

        setStarters(newStarters);
        setBench(newBench);
        setSelectedSwapPlayer(null);
      } else {
        // Both starters or both bench -> change selection
        setSelectedSwapPlayer(player);
      }
    }
  };

  // Recalculate dynamic starting XI xP
  const startingXp = starters.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
  const captBonus = starters.find(p => p.is_captain)?.expected_points || 0;

  return (
    <div>
      {/* Top Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        liveData={liveMatchdayData}
        selectedStrategy={selectedStrategy}
        setSelectedStrategy={setSelectedStrategy}
      />

      <main className="app-container">
        {/* View 1: Tactical Pitch & Lineup Visualizer */}
        {activeTab === 'pitch' && (
          <TacticalPitch
            starters={starters}
            bench={bench}
            selectedPlayer={selectedSwapPlayer}
            onSelectPlayer={handleSelectPlayer}
            onInspectPlayer={setInspectedPlayer}
            actionSummary={liveMatchdayData.action_summary}
            startingXp={startingXp + Number(captBonus)}
            totalXp={liveMatchdayData.total_xp}
          />
        )}

        {/* View 2: Multi-Horizon Transfer Workbench */}
        {activeTab === 'transfers' && (
          <TransferWorkbench
            roadmap={liveMatchdayData.multi_horizon_roadmap}
            allPlayers={allPlayersData}
            onInspectPlayer={setInspectedPlayer}
          />
        )}

        {/* View 3: 38-Gameweek Fixture Heatmap */}
        {activeTab === 'fixtures' && (
          <FixtureHeatmap
            fixtures={fixturesData}
            teams={teamsData}
          />
        )}

        {/* View 4: Market Velocity & Price Trends */}
        {activeTab === 'market' && (
          <MarketVelocityTicker
            allPlayers={allPlayersData}
            onInspectPlayer={setInspectedPlayer}
          />
        )}

        {/* View 5: 11-Component Mathematical Studio */}
        {activeTab === 'math' && (
          <div style={{ background: 'var(--bg-surface-1)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '8px' }}>
              11-COMPONENT EXPECTATION STUDIO & MATHEMATICAL SPECIFICATION
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: 1.5 }}>
              Click any asset in the table below to deconstruct their discrete point expectation formula ($C_1 \dots C_{11}$) and inspect conjugate venue adjustments.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
              {starters.concat(bench).map(p => (
                <div
                  key={p.player_code}
                  onClick={() => setInspectedPlayer(p)}
                  style={{
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.team} · {p.position}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="font-mono" style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
                      {Number(p.expected_points || 0).toFixed(2)}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>xP</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* 11-Component Player DNA Modal with Lazy-Load Suspense */}
      {inspectedPlayer && (
        <Suspense fallback={<div className="modal-overlay"><div className="modal-content skeleton" style={{ height: '400px' }}></div></div>}>
          <PlayerDNAInspector
            player={inspectedPlayer}
            onClose={() => setInspectedPlayer(null)}
          />
        </Suspense>
      )}
    </div>
  );
}
