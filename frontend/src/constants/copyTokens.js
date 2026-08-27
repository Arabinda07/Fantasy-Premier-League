/**
 * FPL Dugout - Central Copy Tokens & Language Dictionary
 * Single Source of Truth for Voice, Tone & Indian English Terminology
 * Specification: docs/voice-and-tone-guide.md
 */

export const APP_BRAND = {
  name: 'FPL Dugout',
  shortName: 'Dugout',
  tagline: 'Smart Squad & Matchday Planner',
  metaDescription: 'Smart Premier League fantasy planner — expected points, optimal starting XI, 5-gameweek transfer roadmap, and live mini-league tracker.',
};

export const NAV_TABS = {
  lineup: { id: 'pitch', label: 'My Lineup', shortLabel: 'Lineup', desc: 'Active squad pitch, captaincy, chips & bench' },
  planner: { id: 'planner', label: 'Transfer Planner', shortLabel: 'Planner', desc: '5-week transfer roadmap & H2H scout' },
  rivals: { id: 'rivals', label: 'Mini-Leagues', shortLabel: 'Rivals', desc: 'Standings, rival tracking & differentials' },
  fixtures: { id: 'fixtures', label: 'Fixture Ticker', shortLabel: 'Fixtures', desc: '38-week difficulty schedule & match odds' },
  prices: { id: 'market', label: 'Price Trends', shortLabel: 'Prices', desc: 'Daily midnight rises/falls & chip guide' },
  forecaster: { id: 'studio', label: 'Points Forecaster', shortLabel: 'Forecaster', desc: 'Projection formula & accuracy scorecard' },
};

export const CHIP_ADVICE = {
  tripleCaptain: {
    name: 'Triple Captain',
    shortName: '3xC',
    targetGw: 'GW25 or GW34',
    expectedGain: '+14.2 pts expected boost',
    advice: 'Best used on heavy hitters like Haaland or Salah during a Double Gameweek with two easy fixtures.',
    tooltip: 'Activate Triple Captain (3x points for your captain)',
  },
  benchBoost: {
    name: 'Bench Boost',
    shortName: 'BB',
    targetGw: 'GW37',
    expectedGain: '+18.5 pts expected boost',
    advice: 'Best played during the biggest Double Gameweek when all 15 players in your squad have two games.',
    tooltip: 'Activate Bench Boost (15 players score this week)',
  },
  freeHit: {
    name: 'Free Hit',
    shortName: 'FH',
    targetGw: 'GW29',
    expectedGain: '+22.0 pts expected boost',
    advice: 'Save this for major Blank Gameweeks (e.g. FA Cup clash weekends) to field a full starting XI without using transfers.',
    tooltip: 'Activate Free Hit (Unlimited free transfers for 1 week)',
  },
  wildcard1: {
    name: 'First Wildcard (Early Season)',
    shortName: 'WC1',
    targetGw: 'GW6 to GW8',
    expectedGain: '+9.4 pts per GW',
    advice: 'Use during early fixture swings (GW6–GW8) to reshape your squad and bring in players from top clubs.',
    tooltip: 'Activate Wildcard (Permanent free squad rebuild)',
  },
  wildcard2: {
    name: 'Second Wildcard (Late Season)',
    shortName: 'WC2',
    targetGw: 'GW30 to GW33',
    expectedGain: '+11.8 pts per GW',
    advice: 'Set up your optimal 15-man bench and starters ahead of the massive Double Gameweeks in DGW34 and DGW37.',
    tooltip: 'Activate Wildcard (Permanent free squad rebuild)',
  },
};

export const STRATEGY_BADGES = {
  differential: {
    badge: '⚡ DIFF',
    label: 'Differential',
    tooltip: 'Differential pick — owned by under 20% of managers in your league',
  },
  template: {
    badge: '🛡️ TEMPLATE',
    label: 'Template Pick',
    tooltip: 'Popular pick — high ownership to protect your mini-league rank',
  },
  benchBoost: {
    badge: '🚀 BB',
    label: 'Bench Boost Active',
    tooltip: 'Bench Boost Active · Scoring points this gameweek',
  },
};

export const TACTICAL_GOALS = {
  maxPoints: {
    id: 'MAX_POINTS',
    label: 'Max Points',
    directive: 'Pick the highest projected points starting XI',
    tooltip: 'Max Points: Pick the best possible starting XI',
  },
  protectLead: {
    id: 'PROTECT_LEAD',
    label: 'Protect Lead',
    directive: 'Back high-ownership picks to keep your mini-league lead safe',
    tooltip: 'Protect Lead: Back high-ownership picks to keep your lead',
  },
  climbRank: {
    id: 'CHASE_RANK',
    label: 'Climb Rank',
    directive: 'Back low-ownership differential punts to make up ground on rivals',
    tooltip: 'Climb Rank: Back low-ownership punts to gain ground',
  },
};

export const METRIC_LABELS = {
  xP: 'Expected Points',
  projectedPts: 'Projected Pts',
  ptsUnits: 'pts',
  xG: 'Goal Threat (xG / 90 mins)',
  xA: 'Assist Threat (xA / 90 mins)',
  cleanSheetChance: 'Clean Sheet Chance',
  winChances: 'Win / Draw / Loss Chances',
  freeTransfers: 'Free Transfers',
  pointHits: 'Point Hits (-4 pts)',
  bankBalance: 'Bank Balance',
  squadValue: 'Squad Value',
};

export const VALIDATION_MESSAGES = {
  formation: {
    minDefenders: 'You need at least 3 Defenders in your starting XI. Please adjust your formation before confirming.',
    minGoalkeepers: 'You need exactly 1 Goalkeeper in your starting XI.',
    minForwards: 'You need at least 1 Forward in your starting XI.',
    totalStarters: 'Starting XI must contain exactly 11 players.',
  },
  budget: {
    insufficientFunds: (playerName, cost, available) =>
      `Not enough funds: ${playerName} costs £${cost.toFixed(1)}m, but you only have £${available.toFixed(1)}m available in your bank.`,
  },
  clubLimit: {
    maxThree: (clubName) =>
      `Maximum 3 players allowed from ${clubName}. Please sell a player from ${clubName} before adding another.`,
  },
};
