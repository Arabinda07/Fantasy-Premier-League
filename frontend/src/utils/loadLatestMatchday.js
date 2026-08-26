/**
 * Dynamic matchday JSON loader for the FPL Analytics Terminal.
 * Automatically discovers all available live_matchday_gw*.json datasets
 * bundled in the data directory and provides lookup by gameweek.
 */

const matchdayModules = import.meta.glob('../data/live_matchday_gw*.json', { eager: true });

const matchdayMap = {};
Object.entries(matchdayModules).forEach(([path, module]) => {
  const match = path.match(/live_matchday_gw(\d+)\.json$/);
  if (match) {
    const gw = parseInt(match[1], 10);
    matchdayMap[gw] = module.default || module;
  }
});

export const availableGameweeks = Object.keys(matchdayMap)
  .map(Number)
  .sort((a, b) => a - b);

export const latestGameweek = availableGameweeks.length > 0
  ? availableGameweeks[availableGameweeks.length - 1]
  : 1;

export function getMatchdayData(gw) {
  if (gw && matchdayMap[gw]) {
    return matchdayMap[gw];
  }
  return matchdayMap[latestGameweek] || null;
}

export function getLatestMatchdayData() {
  return {
    data: matchdayMap[latestGameweek] || null,
    gameweek: latestGameweek,
    availableGameweeks,
  };
}

export default {
  availableGameweeks,
  latestGameweek,
  getMatchdayData,
  getLatestMatchdayData,
};
