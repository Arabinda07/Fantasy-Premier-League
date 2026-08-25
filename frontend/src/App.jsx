import React, { useState, useEffect, lazy, Suspense } from 'react';
import Header from './components/Header';
import Breadcrumbs from './components/Breadcrumbs';
import TacticalPitch from './components/TacticalPitch';
import TransferWorkbench from './components/TransferWorkbench';
import FixtureHeatmap from './components/FixtureHeatmap';
import MarketVelocityTicker from './components/MarketVelocityTicker';
import ComponentStudio from './components/ComponentStudio';
import Footer from './components/Footer';

// Lazy-load Recharts heavy charting component on demand
const PlayerDNAInspector = lazy(() => import('./components/PlayerDNAInspector'));

// Import live data payloads
import liveMatchdayData from './data/live_matchday_gw2.json';
import allPlayersData from './data/players_full.json';
import fixturesData from './data/fixtures_all.json';
import teamsData from './data/teams_all.json';

// Helper to map tab IDs to hash routes
const TAB_TO_HASH = {
  pitch: 'lineup',
  transfers: 'transfers',
  fixtures: 'fixtures',
  market: 'market',
  math: 'methodology'
};

const HASH_TO_TAB = {
  lineup: 'pitch',
  pitch: 'pitch',
  transfers: 'transfers',
  fixtures: 'fixtures',
  market: 'market',
  methodology: 'math',
  math: 'math'
};

export default function App() {
  const [activeTab, setActiveTab] = useState('pitch');
  const [inspectedPlayer, setInspectedPlayer] = useState(null);
  const [activeChip, setActiveChip] = useState('none');
  const [compareSubItem, setCompareSubItem] = useState(null);

  // Squad State (Allowing interactive starter / bench swaps)
  const [starters, setStarters] = useState(liveMatchdayData.starters || []);
  const [bench, setBench] = useState(liveMatchdayData.bench || []);
  const [selectedSwapPlayer, setSelectedSwapPlayer] = useState(null);

  // Parse URL Hash on initial load and handle back/forward navigation
  useEffect(() => {
    const parseHash = () => {
      const hashStr = window.location.hash.replace(/^#\/?/, '');
      if (!hashStr) return;

      const [routePart, queryPart] = hashStr.split('?');
      const targetTab = HASH_TO_TAB[routePart];
      if (targetTab) {
        setActiveTab(targetTab);
      }

      if (queryPart) {
        const params = new URLSearchParams(queryPart);
        const chip = params.get('chip');
        if (chip) setActiveChip(chip);

        const playerName = params.get('player');
        if (playerName && allPlayersData) {
          const matched = allPlayersData.find(
            p => (p.web_name || '').toLowerCase() === playerName.toLowerCase()
          );
          if (matched) setInspectedPlayer(matched);
        }
      }
    };

    parseHash();
    window.addEventListener('hashchange', parseHash);
    return () => window.removeEventListener('hashchange', parseHash);
  }, []);

  // Sync state changes to URL Hash
  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    setCompareSubItem(null);
    const hashRoute = TAB_TO_HASH[newTab] || 'lineup';
    const chipQuery = activeChip !== 'none' ? `?chip=${activeChip}` : '';
    window.location.hash = `${hashRoute}${chipQuery}`;
  };

  const handleChipChange = (newChip) => {
    setActiveChip(newChip);
    const hashRoute = TAB_TO_HASH[activeTab] || 'lineup';
    const chipQuery = newChip !== 'none' ? `?chip=${newChip}` : '';
    window.location.hash = `${hashRoute}${chipQuery}`;
  };

  const handleInspectPlayer = (player) => {
    setInspectedPlayer(player);
    if (player) {
      const hashRoute = TAB_TO_HASH[activeTab] || 'lineup';
      const chipQuery = activeChip !== 'none' ? `chip=${activeChip}&` : '';
      window.location.hash = `${hashRoute}?${chipQuery}player=${encodeURIComponent(player.web_name)}`;
    }
  };

  const handleCloseInspect = () => {
    setInspectedPlayer(null);
    const hashRoute = TAB_TO_HASH[activeTab] || 'lineup';
    const chipQuery = activeChip !== 'none' ? `?chip=${activeChip}` : '';
    window.location.hash = `${hashRoute}${chipQuery}`;
  };

  // Handle interactive player selection and swap
  const handleSelectPlayer = (player) => {
    if (!selectedSwapPlayer) {
      setSelectedSwapPlayer(player);
      return;
    }

    // If clicking same player, deselect
    if (selectedSwapPlayer.player_code === player.player_code) {
      setSelectedSwapPlayer(null);
      return;
    }

    const isFirstStarter = starters.some(p => p.player_code === selectedSwapPlayer.player_code);
    const isSecondStarter = starters.some(p => p.player_code === player.player_code);

    // If swapping between Starter and Bench
    if (isFirstStarter !== isSecondStarter) {
      const newStarters = starters.map(p =>
        p.player_code === (isFirstStarter ? selectedSwapPlayer.player_code : player.player_code)
          ? { ...(isFirstStarter ? player : selectedSwapPlayer), is_starter: true }
          : p
      );
      const newBench = bench.map(p =>
        p.player_code === (isFirstStarter ? player.player_code : selectedSwapPlayer.player_code)
          ? { ...(isFirstStarter ? selectedSwapPlayer : player), is_starter: false }
          : p
      );

      setStarters(newStarters);
      setBench(newBench);
      setSelectedSwapPlayer(null);
    } else {
      setSelectedSwapPlayer(player);
    }
  };

  // Recalculate dynamic starting XI xP
  const startingXp = starters.reduce((acc, p) => acc + Number(p.expected_points || 0), 0);
  const capt = starters.find(p => p.is_captain);
  const captBonus = capt ? capt.expected_points : 0;

  // Active breadcrumb sub-item label
  const breadcrumbSubItem = inspectedPlayer
    ? `${inspectedPlayer.web_name} (${inspectedPlayer.team})`
    : compareSubItem;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Top Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        liveData={liveMatchdayData}
      />

      {/* 3-Level Breadcrumb Trail */}
      <Breadcrumbs
        activeTab={activeTab}
        onNavigateTab={handleTabChange}
        subItem={breadcrumbSubItem}
        onClearSubItem={() => {
          setInspectedPlayer(null);
          setCompareSubItem(null);
        }}
      />

      <main className="app-container" style={{ flex: '1 0 auto' }}>
        {/* View 1: Tactical Pitch & Lineup Visualizer */}
        {activeTab === 'pitch' && (
          <TacticalPitch
            starters={starters}
            bench={bench}
            selectedPlayer={selectedSwapPlayer}
            onSelectPlayer={handleSelectPlayer}
            onInspectPlayer={handleInspectPlayer}
            actionSummary={liveMatchdayData.action_summary}
            startingXp={startingXp + Number(captBonus)}
            totalXp={liveMatchdayData.total_xp}
            chipSimulations={liveMatchdayData.chip_simulations || {}}
            activeChip={activeChip}
            onSelectChip={handleChipChange}
          />
        )}

        {/* View 2: Multi-Horizon Transfer Workbench */}
        {activeTab === 'transfers' && (
          <TransferWorkbench
            roadmap={liveMatchdayData.multi_horizon_roadmap}
            allPlayers={allPlayersData}
            squadPlayers={[...starters, ...bench]}
            onInspectPlayer={handleInspectPlayer}
            onCompareChange={setCompareSubItem}
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
            onInspectPlayer={handleInspectPlayer}
          />
        )}

        {/* View 5: 11-Component Mathematical Studio */}
        {activeTab === 'math' && (
          <ComponentStudio
            players={allPlayersData}
            onInspectPlayer={handleInspectPlayer}
          />
        )}
      </main>

      {/* 11-Component Player DNA Modal with Lazy-Load Suspense */}
      {inspectedPlayer && (
        <Suspense fallback={<div className="modal-overlay"><div className="modal-content skeleton" style={{ height: '400px' }}></div></div>}>
          <PlayerDNAInspector
            player={inspectedPlayer}
            onClose={handleCloseInspect}
          />
        </Suspense>
      )}

      {/* Institutional Footer Navigation */}
      <Footer
        onNavigateTab={handleTabChange}
        liveData={liveMatchdayData}
      />
    </div>
  );
}
