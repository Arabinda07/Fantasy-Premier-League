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
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    async function loadDatasets() {
      try {
        setIsLoading(true);
        // Dynamically import all 3 datasets asynchronously in parallel
        const [playersMod, fixturesMod, teamsMod] = await Promise.all([
          dataCache.players ? Promise.resolve({ default: dataCache.players }) : import('../data/players_full.json'),
          dataCache.fixtures ? Promise.resolve({ default: dataCache.fixtures }) : import('../data/fixtures_all.json'),
          dataCache.teams ? Promise.resolve({ default: dataCache.teams }) : import('../data/teams_all.json'),
        ]);

        const players = playersMod.default || playersMod;
        const fixtures = fixturesMod.default || fixturesMod;
        const teams = teamsMod.default || teamsMod;

        dataCache.players = players;
        dataCache.fixtures = fixtures;
        dataCache.teams = teams;

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
