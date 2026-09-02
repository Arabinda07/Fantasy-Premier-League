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
import OnboardingModal from './components/OnboardingModal';
import FixtureProbabilityDrawer from './components/FixtureProbabilityDrawer';
import ErrorBoundary from './components/ErrorBoundary';
import Footer from './components/Footer';

// Lazy-load Recharts heavy charting component on demand
const PlayerDNAInspector = lazy(() => import('./components/PlayerDNAInspector'));

// Import dynamic matchday data loader and asynchronous data hook (F-12)
import {
  getLatestMatchdayData,
  getMatchdayData,
  availableGameweeks
} from './utils/loadLatestMatchday';
import useDataLoader from './utils/useDataLoader';
import { buildLiveMatchdayPayload } from './utils/clientOptimizer';

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

  // F-12: Asynchronous Lazy-Load for massive static JSON databases
  const {
    players: allPlayersData,
    fixtures: fixturesData,
    teams: teamsData,
    isLoading: isDataLoading,
  } = useDataLoader();

  // Modals & Drawers
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
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
  const [activeStrategy, setActiveStrategy] = useState(initialMatchday.data?.strategy || 'pure_xp');

  // Check first-time onboarding on initial mount
  useEffect(() => {
    try {
      const hasOnboarded = localStorage.getItem('fpl_has_onboarded');
      const savedEntryId = localStorage.getItem('fpl_synced_entry_id');
      if (!hasOnboarded && !savedEntryId) {
        setIsOnboardingOpen(true);
      }
    } catch (e) {
      console.warn('LocalStorage check error:', e);
    }
  }, []);

  // Handle live squad sync from /api/sync
  const handleLiveSyncSuccess = (syncedData) => {
    if (!syncedData) return;

    if (!allPlayersData || allPlayersData.length === 0) {
      if (syncedData.manager) {
        setLiveData(prev => ({
          ...prev,
          manager_profile: {
            ...prev.manager_profile,
            ...syncedData.manager
          }
        }));
      }
      return;
    }

    const fullPayload = buildLiveMatchdayPayload(
      syncedData,
      allPlayersData,
      activeStrategy,
      liveData.dixon_coles_fixtures || []
    );

    setLiveData(fullPayload);
    setStarters(fullPayload.starters || []);
    setBench(fullPayload.bench || []);
    setSelectedSwapPlayer(null);
  };

  const handleExploreDemo = () => {
    setIsOnboardingOpen(false);
  };

  // Switch Gameweek Dataset handler
  const handleSelectGw = async (gw) => {
    const numGw = Number(gw);
    setSelectedGw(numGw);

    let customEntryId = null;
    try {
      customEntryId = localStorage.getItem('fpl_synced_entry_id');
    } catch {
      // Ignore localStorage errors
    }

    const isCustomManager = customEntryId && String(customEntryId) !== '9500404';

    if (isCustomManager) {
      try {
        const leagueId = localStorage.getItem('fpl_synced_league_id');
        const params = new URLSearchParams({ entry_id: customEntryId, gw: numGw });
        if (leagueId) params.append('league_id', leagueId);
        const res = await fetch(`/api/sync?${params.toString()}`);
        if (res.ok) {
          const syncData = await res.json();
          if (syncData && syncData.success) {
            handleLiveSyncSuccess(syncData);
            return;
          }
        }
      } catch (err) {
        console.warn('Failed to fetch custom manager GW data:', err);
      }
    }

    const data = getMatchdayData(numGw);
    if (data) {
      setLiveData(data);
      setStarters(data.starters || []);
      setBench(data.bench || []);
      setSelectedSwapPlayer(null);
      if (data.strategy) setActiveStrategy(data.strategy);
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
    if (!player) return;
    setInspectedPlayer(player);
    const hashRoute = TAB_TO_HASH[activeTab] || 'lineup';
    const chipQuery = activeChip !== 'none' ? `chip=${activeChip}` : '';
    const playerQuery = `player=${encodeURIComponent(player.web_name || '')}`;
    const fullQuery = [chipQuery, playerQuery].filter(Boolean).join('&');
    window.location.hash = `${hashRoute}${fullQuery ? `?${fullQuery}` : ''}`;
  };

  const handleCloseInspect = () => {
    setInspectedPlayer(null);
    const hashRoute = TAB_TO_HASH[activeTab] || 'lineup';
    const chipQuery = activeChip !== 'none' ? `?chip=${activeChip}` : '';
    window.location.hash = `${hashRoute}${chipQuery}`;
  };

  const handleOpenFixtureDrawer = (fixture) => {
    setActiveDrawerFixture(fixture);
    setIsFixtureDrawerOpen(true);
  };

  const handleCloseFixtureDrawer = () => {
    setIsFixtureDrawerOpen(false);
    setActiveDrawerFixture(null);
  };

  // Strategy Mode change handler
  const handleStrategyChange = (newStrategy) => {
    setActiveStrategy(newStrategy);
    if (liveData?.strategies && liveData.strategies[newStrategy]) {
      const s = liveData.strategies[newStrategy];
      setStarters(s.starters || []);
      setBench(s.bench || []);
      setSelectedSwapPlayer(null);
    }
  };

  // Formation Legality Validator
  const validateFormation = (currentStarters) => {
    const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
    currentStarters.forEach(p => {
      if (p && p.position) counts[p.position] = (counts[p.position] || 0) + 1;
    });
    return counts.GK === 1 && counts.DEF >= 3 && counts.DEF <= 5 && counts.MID >= 2 && counts.MID <= 5 && counts.FWD >= 1 && counts.FWD <= 3;
  };

  // Pitch Starter <-> Bench Swap Handler
  const handleSwapPlayers = (p1, p2) => {
    const isP1Starter = starters.some(s => (s.player_code || s.code) === (p1.player_code || p1.code));
    const isP2Starter = starters.some(s => (s.player_code || s.code) === (p2.player_code || p2.code));

    if (isP1Starter && !isP2Starter) {
      const newStarters = starters.map(s => (s.player_code || s.code) === (p1.player_code || p1.code) ? p2 : s);
      const newBench = bench.map(b => (b.player_code || b.code) === (p2.player_code || p2.code) ? p1 : b);
      if (validateFormation(newStarters)) {
        setStarters(newStarters);
        setBench(newBench);
        setSelectedSwapPlayer(null);
      } else {
        alert('Invalid Formation: Must have 1 GK, 3-5 DEFs, 2-5 MIDs, 1-3 FWDs.');
        setSelectedSwapPlayer(null);
      }
    } else if (!isP1Starter && isP2Starter) {
      const newStarters = starters.map(s => (s.player_code || s.code) === (p2.player_code || p2.code) ? p1 : s);
      const newBench = bench.map(b => (b.player_code || b.code) === (p1.player_code || p1.code) ? p2 : b);
      if (validateFormation(newStarters)) {
        setStarters(newStarters);
        setBench(newBench);
        setSelectedSwapPlayer(null);
      } else {
        alert('Invalid Formation: Must have 1 GK, 3-5 DEFs, 2-5 MIDs, 1-3 FWDs.');
        setSelectedSwapPlayer(null);
      }
    } else {
      setSelectedSwapPlayer(null);
    }
  };

  return (
    <div className="app-layout">
      {/* Institutional Top Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        liveData={liveData}
        selectedGw={selectedGw}
        availableGameweeks={availableGameweeks}
        onSelectGw={handleSelectGw}
        onOpenSyncModal={() => setIsSyncModalOpen(true)}
        strategy={activeStrategy}
        onSelectStrategy={handleStrategyChange}
        activeChip={activeChip}
      />

      {/* Semantic Breadcrumbs Navigation Bar */}
      <Breadcrumbs
        activeTab={activeTab}
        activeChip={activeChip}
        inspectedPlayer={inspectedPlayer}
        activeFixture={activeDrawerFixture}
        selectedGw={selectedGw}
        onNavigateTab={handleTabChange}
        onClearChip={() => handleChipChange('none')}
        onClearPlayer={handleCloseInspect}
        onClearFixture={handleCloseFixtureDrawer}
      />

      {/* Main Analytical Viewports */}
      <main className="main-content">
        {isDataLoading && (!allPlayersData || allPlayersData.length === 0) ? (
          <div style={{ padding: '32px', textAlign: 'center' }}>
            <div className="skeleton" style={{ height: '300px', maxWidth: '1200px', margin: '0 auto' }}></div>
          </div>
        ) : (
          <>
            {/* View 1: Tactical Pitch & Matchday Projections */}
            {activeTab === 'pitch' && (
              <ErrorBoundary componentName="Tactical Pitch">
                <div className="surface-scope-pitch">
                  <TacticalPitch
                    liveData={liveData}
                    starters={starters}
                    bench={bench}
                    allPlayersData={allPlayersData}
                    selectedSwapPlayer={selectedSwapPlayer}
                    setSelectedSwapPlayer={setSelectedSwapPlayer}
                    onSwapPlayers={handleSwapPlayers}
                    onInspectPlayer={handleInspectPlayer}
                    onOpenFixture={handleOpenFixtureDrawer}
                    activeChip={activeChip}
                    onSelectChip={handleChipChange}
                    strategy={activeStrategy}
                    onSelectStrategy={handleStrategyChange}
                    onNavigateTab={handleTabChange}
                  />
                </div>
              </ErrorBoundary>
            )}

            {/* View 2: Unified Transfer Studio & 5-Week Strategic Planner */}
            {activeTab === 'transfers' && (
              <ErrorBoundary componentName="Multi-GW Planner">
                <div className="surface-scope-planner">
                  <MultiGwPlanner
                    roadmap={liveData?.multi_horizon_roadmap || liveData?.multi_horizon_plan || liveData?.transfer_roadmap || []}
                    squadPlayers={[...(starters || []), ...(bench || [])]}
                    allPlayers={allPlayersData}
                    allPlayersData={allPlayersData}
                    fixturesData={fixturesData}
                    liveData={liveData}
                    onInspectPlayer={handleInspectPlayer}
                    onOpenFixture={handleOpenFixtureDrawer}
                    activeChip={activeChip}
                    onSelectChip={handleChipChange}
                  />
                </div>
              </ErrorBoundary>
            )}

            {/* View 3: Rival Threat Matrix & Game Theory View */}
            {activeTab === 'rivals' && (
              <ErrorBoundary componentName="Rival Radar">
                <div className="surface-scope-rivals">
                  <RivalThreatMatrix
                    managerProfile={liveData?.manager_profile || liveData?.manager}
                    starters={starters.length ? starters : (liveData?.starters || [])}
                    _bench={bench.length ? bench : (liveData?.bench || [])}
                    bench={bench.length ? bench : (liveData?.bench || [])}
                    allPlayers={allPlayersData}
                    allPlayersData={allPlayersData}
                    liveData={liveData}
                    onInspectPlayer={handleInspectPlayer}
                  />
                </div>
              </ErrorBoundary>
            )}

            {/* View 4: Fixture Heatmap & Schedule Dynamics */}
            {activeTab === 'fixtures' && (
              <ErrorBoundary componentName="Fixture Heatmap">
                <div className="surface-scope-fixtures">
                  <FixtureHeatmap
                    fixturesData={fixturesData}
                    teamsData={teamsData}
                    onOpenFixture={handleOpenFixtureDrawer}
                    selectedGw={selectedGw}
                  />
                </div>
              </ErrorBoundary>
            )}

            {/* View 5: Market Price Velocity Ticker */}
            {activeTab === 'market' && (
              <ErrorBoundary componentName="Market Velocity Ticker">
                <div className="surface-scope-market">
                  <MarketVelocityTicker
                    allPlayers={allPlayersData}
                    allPlayersData={allPlayersData}
                    onInspectPlayer={handleInspectPlayer}
                    liveData={liveData}
                  />
                </div>
              </ErrorBoundary>
            )}

            {/* View 6: 11-Component Mathematical Studio */}
            {activeTab === 'math' && (
              <ErrorBoundary componentName="Mathematical Studio">
                <div className="surface-scope-studio">
                  <ComponentStudio
                    players={allPlayersData}
                    onInspectPlayer={handleInspectPlayer}
                  />
                </div>
              </ErrorBoundary>
            )}
          </>
        )}
      </main>

      {/* Onboarding Gateway Modal for First-Time Visitors */}
      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        onSyncSuccess={handleLiveSyncSuccess}
        onExploreDemo={handleExploreDemo}
      />

      {/* 1-Click Live Team Sync Modal */}
      <LiveTeamSyncModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
        currentProfile={liveData.manager_profile}
        onSyncSuccess={handleLiveSyncSuccess}
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
