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

export const CAPTAINCY_DECISION_BRIEF = {
  title: "Manager's Decision Brief",
  subtitle: 'Why Bruno Fernandes (C) is your best captain pick this week',
  badge: '👑 CAPTAINCY BRIEF',
  selectedCaptain: {
    name: 'Bruno Fernandes',
    shortName: 'B.Fernandes',
    team: 'Man Utd',
    fixture: 'IPS (H)',
    baseXp: 5.6,
    captainXp: 11.2,
    role: 'Primary penalty taker and takes all set-pieces',
  },
  rationales: [
    {
      id: 'fixture_mult',
      icon: 'HouseLine',
      title: 'Easy Home Match (+36% Goal Threat)',
      summary: 'Man United host promoted Ipswich Town at Old Trafford, giving Bruno a huge home boost (+36% team goal threat).',
      badge: '+36% Goal Threat',
    },
    {
      id: 'penalty_order',
      icon: 'Target',
      title: 'Takes Every Penalty',
      summary: 'Undisputed first-choice penalty taker for United, who win plenty of spot-kicks in the box (7–9 per season).',
      badge: 'First-Choice PK',
    },
    {
      id: 'set_piece_monopoly',
      icon: 'CornersOut',
      title: 'Takes All Corners & Free-Kicks',
      summary: 'Delivers every corner and direct free-kick, creating big scoring chances and scooping extra bonus points.',
      badge: 'All Dead Balls',
    },
    {
      id: 'higher_ev',
      icon: 'TrendUp',
      title: 'Highest Projected Points (11.2 pts as C)',
      summary: 'Projected for 5.6 points (11.2 with the armband)—the safest and highest captain pick this gameweek.',
      badge: '11.2 Exp Pts',
    },
  ],
  alternatives: [
    {
      name: 'Erling Haaland',
      team: 'Man City',
      fixture: 'CHE (A)',
      xp: 4.9,
      captainXp: 9.8,
      comparison: 'Tough away match against Chelsea at Stamford Bridge. Bruno has a much easier fixture at home.',
      verdict: 'Tough away game (9.8 pts as C)',
    },
    {
      name: 'Mohamed Salah',
      team: 'Liverpool',
      fixture: 'IPS (A)',
      xp: 5.1,
      captainXp: 10.2,
      comparison: 'Away at Ipswich and does not take all set-pieces. Bruno’s full set-piece duties give him the edge.',
      verdict: 'Away trip · 1.0 pt behind Bruno',
    },
    {
      name: 'Cole Palmer',
      team: 'Chelsea',
      fixture: 'MCI (H)',
      xp: 3.7,
      captainXp: 7.4,
      comparison: 'Tough opener against champions Man City, which limits Chelsea’s scoring chances.',
      verdict: 'Faces Man City (7.4 pts as C)',
    },
  ],
};

export const STRUCTURAL_BUILDS = {
  spread: {
    id: 'spread',
    name: 'Big in the Middle',
    shortName: '5 Big Midfielders',
    formation: '3-5-2',
    tagline: '3-5-2 · Stacked 5-man midfield',
    description: 'Packs your midfield with five top scorers: Palmer, Bruno (C), Szoboszlai, Mbeumo, and Tavernier.',
    keyPlayers: ['Palmer', 'B.Fernandes', 'Szoboszlai', 'Mbeumo', 'Tavernier'],
    captain: 'B.Fernandes',
    formationDetails: '3-5-2 Formation',
    badge: '3-5-2 SPREAD',
    badgeColor: 'var(--accent-cyan)',
    tooltip: 'Big in the Middle: 3-5-2 with 5 top-scoring midfielders and Bruno (C)',
  },
  anchor: {
    id: 'anchor',
    name: 'Haaland Mega-Anchor',
    shortName: 'Haaland Heavy',
    formation: '3-4-3',
    tagline: '3-4-3 · Haaland captain with budget rotation',
    description: 'Builds around Haaland (£15.5m) as permanent captain, using smart budget picks to round out the squad.',
    keyPlayers: ['Haaland', 'Calvert-Lewin', 'B.Fernandes', 'Mbeumo', 'Gabriel'],
    captain: 'Haaland',
    formationDetails: '3-4-3 / 3-5-2 Anchor',
    badge: 'HAALAND ANCHOR',
    badgeColor: 'var(--accent-amber)',
    tooltip: 'Haaland Mega-Anchor: Build around Haaland (£15.5m) with cheap enablers',
  },
};

export const SET_PIECE_TIERS = {
  high: {
    tier: 'High',
    rate: 0.18,
    rateFormatted: '0.18 pk/90',
    label: 'High PK',
    badge: '🎯 High PK',
    desc: 'Top Penalty Team (~7–9 penalties a season)',
    tooltip: 'Penalty Taker: Team wins lots of spot-kicks in the box (~7–9 per season)',
    teams: ['Man City', 'Chelsea', 'Arsenal', 'Liverpool', 'Man Utd'],
  },
  standard: {
    tier: 'Standard',
    rate: 0.12,
    rateFormatted: '0.12 pk/90',
    label: 'Std PK',
    badge: '🎯 Std PK',
    desc: 'Average Penalty Team (~4–5 penalties a season)',
    tooltip: 'Penalty Taker: Team wins an average number of spot-kicks (~4–5 per season)',
    teams: ['Aston Villa', 'Newcastle', 'Spurs', 'Brighton', 'Brentford', 'West Ham', 'Crystal Palace', 'Fulham', 'Bournemouth'],
  },
  low: {
    tier: 'Low',
    rate: 0.07,
    rateFormatted: '0.07 pk/90',
    label: 'Low PK',
    badge: '🎯 Low PK',
    desc: 'Low Penalty Team (~2–3 penalties a season)',
    tooltip: 'Penalty Taker: Team rarely wins penalties in the box (~2–3 per season)',
    teams: ['Everton', "Nott'm Forest", 'Wolves', 'Leicester', 'Ipswich Town', 'Southampton', 'Sunderland'],
  },
};

export const DEFCON_BADGES = {
  awayDefcon: {
    badge: '🛡️ Away Defcon (+5%)',
    shortBadge: '🛡️ DEFCON',
    label: 'Away Defcon (+5%)',
    desc: 'More tackles and ball recoveries in away games (+5% defensive points)',
    tooltip: 'Away Match Bonus: Defenders under away pressure make more tackles and recoveries, boosting baseline points (+5%).',
  },
};

export function getPenaltyTierForTeam(teamName) {
  if (!teamName) return SET_PIECE_TIERS.standard;
  const cleanTeam = teamName.trim();
  if (SET_PIECE_TIERS.high.teams.some(t => cleanTeam.toLowerCase().includes(t.toLowerCase()) || t.toLowerCase().includes(cleanTeam.toLowerCase()))) {
    return SET_PIECE_TIERS.high;
  }
  if (SET_PIECE_TIERS.low.teams.some(t => cleanTeam.toLowerCase().includes(t.toLowerCase()) || t.toLowerCase().includes(cleanTeam.toLowerCase()))) {
    return SET_PIECE_TIERS.low;
  }
  return SET_PIECE_TIERS.standard;
}


