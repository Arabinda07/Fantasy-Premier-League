import React, { useState, useEffect, lazy, Suspense } from 'react';
import Header from './components/Header';
import Breadcrumbs from './components/Breadcrumbs';
import TacticalPitch from './components/TacticalPitch';
import MultiGwPlanner from './components/MultiGwPlanner';
import RivalThreatMatrix from './components/RivalThreatMatrix';
import FixtureHeatmap from './components/FixtureHeatmap';
import MarketVelocityTicker from './components/MarketVelocityTicker';
import ComponentStudio from './components/ComponentStudio';
import LiveTeamSyncModal from './components/LiveTeamSyncModal';
import FixtureProbabilityDrawer from './components/FixtureProbabilityDrawer';
import ErrorBoundary from './components/ErrorBoundary';
import Footer from './components/Footer';

// Lazy-load Recharts heavy charting component on demand
const PlayerDNAInspector = lazy(() => import('./components/PlayerDNAInspector'));

// Import dynamic matchday data loader and asynchronous data hook (F-12)
import {
  getLatestMatchdayData,
  getMatchdayData,
  availableGameweeks,
  latestGameweek
} from './utils/loadLatestMatchday';
import useDataLoader from './utils/useDataLoader';

// Helper to map tab IDs to hash routes
const TAB_TO_HASH = {
  pitch: 'lineup',
  transfers: 'planner',
  rivals: 'rivals',
  fixtures: 'fixtures',
  market: 'market',
  math: 'studio'
};

const HASH_TO_TAB = {
  lineup: 'pitch',
  pitch: 'pitch',
  planner: 'transfers',
  strategy: 'transfers',
  transfers: 'transfers',
  rivals: 'rivals',
  fixtures: 'fixtures',
  market: 'market',
  studio: 'math',
  methodology: 'math',
  math: 'math'
};

export default function App() {
  const [activeTab, setActiveTab] = useState('pitch');
  const [inspectedPlayer, setInspectedPlayer] = useState(null);
  const [activeChip, setActiveChip] = useState('none');
  const [compareSubItem, setCompareSubItem] = useState(null);

  // F-12: Asynchronous Lazy-Load for massive static JSON databases
  const {
    players: allPlayersData,
    fixtures: fixturesData,
    teams: teamsData,
    isLoading: isDataLoading,
  } = useDataLoader();

  // Modals & Drawers
  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
  const [isFixtureDrawerOpen, setIsFixtureDrawerOpen] = useState(false);
  const [activeDrawerFixture, setActiveDrawerFixture] = useState(null);

  // Dynamic Live Matchday State (defaults automatically to latest available GW)
  const initialMatchday = getLatestMatchdayData();
  const [selectedGw, setSelectedGw] = useState(initialMatchday.gameweek || 1);
  const [liveData, setLiveData] = useState(initialMatchday.data || {});
  const [starters, setStarters] = useState(initialMatchday.data?.starters || []);
  const [bench, setBench] = useState(initialMatchday.data?.bench || []);
  const [selectedSwapPlayer, setSelectedSwapPlayer] = useState(null);

  // Switch Gameweek Dataset handler
  const handleSelectGw = (gw) => {
    const numGw = Number(gw);
    setSelectedGw(numGw);
    const data = getMatchdayData(numGw);
    if (data) {
      setLiveData(data);
      setStarters(data.starters || []);
      setBench(data.bench || []);
      setSelectedSwapPlayer(null);
    }
  };

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
        if (playerName && allPlayersData && allPlayersData.length > 0) {
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
  }, [allPlayersData]);

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
    if (!player) {
      setInspectedPlayer(null);
      return;
    }

    // Lookup full mathematical profile from database
    const detailed = allPlayersData?.find(
      p => (p.player_code === player.player_code) ||
           (p.code === player.player_code) ||
           (p.web_name && player.web_name && p.web_name.toLowerCase() === player.web_name.toLowerCase())
    );

    const merged = detailed ? { ...detailed, ...player } : player;
    setInspectedPlayer(merged);

    if (player.web_name) {
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

  // Fixture Drawer Handlers
  const handleOpenFixtureDrawer = (fixtureDetails) => {
    setActiveDrawerFixture(fixtureDetails);
    setIsFixtureDrawerOpen(true);
  };

  const handleCloseFixtureDrawer = () => {
    setIsFixtureDrawerOpen(false);
    setActiveDrawerFixture(null);
  };

  // Interactive starter / bench swap handler
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
      const starterPlayer = isFirstStarter ? selectedSwapPlayer : player;
      const benchPlayer = isFirstStarter ? player : selectedSwapPlayer;

      // F-13 fix: Validate that the resulting formation is legal before committing
      const newStarterPositions = starters
        .filter(p => p.player_code !== starterPlayer.player_code)
        .concat({ ...benchPlayer, is_starter: true })
        .reduce((acc, p) => { acc[p.position] = (acc[p.position] || 0) + 1; return acc; }, {});

      const isValidFormation = (
        (newStarterPositions['GK'] || 0) === 1 &&
        (newStarterPositions['DEF'] || 0) >= 3 &&
        (newStarterPositions['MID'] || 0) >= 2 &&
        (newStarterPositions['FWD'] || 0) >= 1
      );

      if (!isValidFormation) {
        // Invalid formation — reject swap silently
        setSelectedSwapPlayer(null);
        return;
      }

      const newStarters = starters.map(p =>
        p.player_code === starterPlayer.player_code
          ? { ...benchPlayer, is_starter: true }
          : p
      );
      const newBench = bench.map(p =>
        p.player_code === benchPlayer.player_code
          ? { ...starterPlayer, is_starter: false }
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
      {/* Skip-to-Content Accessibility Link (WCAG 2.4.1) */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* Top Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        liveData={liveData}
        selectedGw={selectedGw}
        availableGameweeks={availableGameweeks}
        onSelectGw={handleSelectGw}
        onOpenSyncModal={() => setIsSyncModalOpen(true)}
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

      <main id="main-content" className="app-container" style={{ flex: '1 0 auto' }}>
        {isDataLoading ? (
          <div className="fpl-loader-skeleton-container" role="status">
            <div className="fpl-loader-spinner"></div>
            <div className="fpl-loader-text font-mono">HYDRATING FPL MATCHDAY DATA ENGINE...</div>
          </div>
        ) : (
          <>
            {/* View 1: Tactical Pitch & Lineup Visualizer */}
            {activeTab === 'pitch' && (
              <ErrorBoundary componentName="Tactical Pitch">
                <TacticalPitch
                  starters={starters}
                  bench={bench}
                  selectedPlayer={selectedSwapPlayer}
                  onSelectPlayer={handleSelectPlayer}
                  onInspectPlayer={handleInspectPlayer}
                  onOpenMatchup={handleOpenFixtureDrawer}
                  actionSummary={liveData.action_summary}
                  startingXp={startingXp + Number(captBonus)}
                  totalXp={liveData.total_xp}
                  chipSimulations={liveData.chip_simulations || {}}
                  activeChip={activeChip}
                  onSelectChip={handleChipChange}
                />
              </ErrorBoundary>
            )}

            {/* View 2: Multi-Horizon 5-GW Strategy Canvas */}
            {activeTab === 'transfers' && (
              <ErrorBoundary componentName="Transfer Workbench">
                <MultiGwPlanner
                  roadmap={liveData.multi_horizon_roadmap}
                  squadPlayers={[...starters, ...bench]}
                  allPlayers={allPlayersData}
                  onInspectPlayer={handleInspectPlayer}
                />
              </ErrorBoundary>
            )}

            {/* View 3: Mini-League Rival Threat Matrix */}
            {activeTab === 'rivals' && (
              <ErrorBoundary componentName="Rival Threat Matrix">
                <RivalThreatMatrix
                  managerProfile={liveData.manager_profile}
                  starters={starters}
                  bench={bench}
                />
              </ErrorBoundary>
            )}

            {/* View 4: 38-Gameweek Fixture Heatmap */}
            {activeTab === 'fixtures' && (
              <ErrorBoundary componentName="Fixture Heatmap">
                <FixtureHeatmap
                  fixtures={fixturesData}
                  teams={teamsData}
                />
              </ErrorBoundary>
            )}

            {/* View 5: Market Velocity & Price Trends */}
            {activeTab === 'market' && (
              <ErrorBoundary componentName="Market Velocity Ticker">
                <MarketVelocityTicker
                  allPlayers={allPlayersData}
                  onInspectPlayer={handleInspectPlayer}
                />
              </ErrorBoundary>
            )}

            {/* View 6: 11-Component Mathematical Studio */}
            {activeTab === 'math' && (
              <ErrorBoundary componentName="Mathematical Studio">
                <ComponentStudio
                  players={allPlayersData}
                  onInspectPlayer={handleInspectPlayer}
                />
              </ErrorBoundary>
            )}
          </>
        )}
      </main>

      {/* 1-Click Live Team Sync Modal */}
      <LiveTeamSyncModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
        currentProfile={liveData.manager_profile}
        onSyncSuccess={(newProfile) => {
          setLiveData(prev => ({
            ...prev,
            manager_profile: {
              ...prev.manager_profile,
              ...newProfile
            }
          }));
        }}
      />

      {/* Dixon-Coles Fixture Probability Drawer */}
      <FixtureProbabilityDrawer
        isOpen={isFixtureDrawerOpen}
        onClose={handleCloseFixtureDrawer}
        fixtureData={activeDrawerFixture}
        dixonColesList={liveData.dixon_coles_fixtures || []}
      />

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
        liveData={liveData}
      />
    </div>
  );
}
