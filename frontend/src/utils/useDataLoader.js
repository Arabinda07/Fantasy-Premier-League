import { useState, useEffect } from 'react';

// In-memory cache for lazy-loaded JSON data
const dataCache = {
  players: null,
  fixtures: null,
  teams: null,
};

/**
 * Custom hook to asynchronously load large static JSON datasets.
 * Prevents 1.5MB+ of JSON data from blocking the initial main JavaScript bundle.
 *
 * @returns {{
 *   players: Array|null,
 *   fixtures: Array|null,
 *   teams: Array|null,
 *   isLoading: boolean,
 *   error: Error|null
 * }}
 */
export function useDataLoader() {
  const [data, setData] = useState({
    players: dataCache.players,
    fixtures: dataCache.fixtures,
    teams: dataCache.teams,
  });
  const [isLoading, setIsLoading] = useState(!dataCache.players || !dataCache.fixtures || !dataCache.teams);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If all datasets are already cached in memory, return immediately
    if (dataCache.players && dataCache.fixtures && dataCache.teams) {
      return;
    }

    let isMounted = true;

    async function loadDatasets() {
      try {
        setIsLoading(true);
        // Stage 1: Load lightweight team metadata and fixture schedule first for immediate responsiveness
        const [teamsMod, fixturesMod] = await Promise.all([
          dataCache.teams ? Promise.resolve({ default: dataCache.teams }) : import('../data/teams_all.json'),
          dataCache.fixtures ? Promise.resolve({ default: dataCache.fixtures }) : import('../data/fixtures_all.json'),
        ]);

        const teams = teamsMod.default || teamsMod;
        const fixtures = fixturesMod.default || fixturesMod;
        dataCache.teams = teams;
        dataCache.fixtures = fixtures;

        if (isMounted) {
          setData(prev => ({ ...prev, teams, fixtures }));
        }

        // Stage 2: Hydrate full 600+ player database
        const playersMod = dataCache.players
          ? { default: dataCache.players }
          : await import('../data/players_full.json');

        const players = playersMod.default || playersMod;
        dataCache.players = players;

        if (isMounted) {
          setData({ players, fixtures, teams });
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Failed to asynchronously load FPL database:', err);
        if (isMounted) {
          setError(err);
          setIsLoading(false);
        }
      }
    }

    loadDatasets();

    return () => {
      isMounted = false;
    };
  }, []);

  return {
    players: data.players || [],
    fixtures: data.fixtures || [],
    teams: data.teams || [],
    isLoading,
    error,
  };
}

export default useDataLoader;
