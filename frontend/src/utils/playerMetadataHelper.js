/**
 * Player Metadata and Fixture Sanitization Helper
 *
 * Solves:
 * 1. Duplicate club & fixture opponent collisions (e.g. 'Chelsea · £7.8m · @ Chelsea').
 * 2. Uniform formatting of cost (£X.Xm) and expected points across modals.
 * 3. Structured fixture & FDR (Fixture Difficulty Rating 1-5) extraction.
 */

/**
 * Normalizes team name for matching against opponent strings.
 * Strips common suffixes (FC, City, United, etc.) to detect self-match.
 */
function normalizeClubName(name) {
  if (!name || typeof name !== 'string') return '';
  return name
    .toLowerCase()
    .replace(/\b(fc|city|united|wanderers|hotspur|albion|athletic|town|villa|rover|rovers)\b/gi, '')
    .trim();
}

const CLUB_SHORT_CODES = {
  arsenal: 'ARS',
  'aston villa': 'AVL',
  bournemouth: 'BOU',
  brentford: 'BRE',
  brighton: 'BHA',
  chelsea: 'CHE',
  'crystal palace': 'CRY',
  palace: 'CRY',
  everton: 'EVE',
  fulham: 'FUL',
  ipswich: 'IPS',
  leicester: 'LEI',
  liverpool: 'LIV',
  'man city': 'MCI',
  'manchester city': 'MCI',
  'man utd': 'MUN',
  'manchester united': 'MUN',
  newcastle: 'NEW',
  'nottingham forest': 'NFO',
  forest: 'NFO',
  southampton: 'SOU',
  tottenham: 'TOT',
  spurs: 'TOT',
  'west ham': 'WHU',
  wolves: 'WOL',
  wolverhampton: 'WOL'
};

export function getClubShortCode(name) {
  if (!name || typeof name !== 'string') return '';
  const clean = name.trim().toLowerCase();
  if (CLUB_SHORT_CODES[clean]) return CLUB_SHORT_CODES[clean];
  const norm = normalizeClubName(name);
  if (CLUB_SHORT_CODES[norm]) return CLUB_SHORT_CODES[norm];
  for (const [club, code] of Object.entries(CLUB_SHORT_CODES)) {
    if (clean.includes(club) || norm.includes(club)) return code;
  }
  return name.length > 3 ? name.slice(0, 3).toUpperCase() : name.toUpperCase();
}

/**
 * Resolves sanitized player metadata and fixture info.
 *
 * @param {Object} player
 * @returns {{
 *   name: string,
 *   team: string,
 *   cost: number,
 *   costFormatted: string,
 *   position: string,
 *   expectedPoints: string,
 *   fixtureInfo: {
 *     venue: string,
 *     opponent: string,
 *     display: string,
 *     fdr: number
 *   } | null
 * }}
 */
export function resolvePlayerMetadata(player) {
  if (!player) {
    return {
      name: 'Player',
      team: 'PL',
      cost: 0,
      costFormatted: '0.0',
      position: 'FWD',
      expectedPoints: '0.00',
      fixtureInfo: null
    };
  }

  const name = player.web_name || player.name || 'Player';
  const team = player.team || player.team_name || 'PL';
  const costNum = Number(player.cost ?? player.now_cost ?? player.selling_price ?? 0);
  const costFormatted = costNum.toFixed(1);
  const position = player.position || 'FWD';

  const xpNum = Number(player.expected_points ?? player.xp ?? player.xP ?? player.dynamicXp ?? 0);
  const expectedPoints = xpNum.toFixed(2);

  // Fixture resolution & deduplication
  let rawFixture = player.fixture || player.next_opponent || '';
  if (!rawFixture && player.fixture_opponent) {
    const venuePrefix = (player.fixture_venue === 'A') ? '@' : 'vs';
    rawFixture = `${venuePrefix} ${player.fixture_opponent}`;
  }

  let fixtureInfo = null;

  if (rawFixture && typeof rawFixture === 'string' && rawFixture.trim() !== 'TBD') {
    let venue = '@';
    let opp = rawFixture.trim();

    if (opp.startsWith('@')) {
      venue = '@';
      opp = opp.replace(/^@\s*/, '').trim();
    } else if (opp.toLowerCase().startsWith('vs')) {
      venue = 'vs';
      opp = opp.replace(/^vs\s*/i, '').trim();
    } else if (player.fixture_venue === 'H') {
      venue = 'vs';
    }

    // SANITIZATION: Check for self-fixture collision (e.g. Chelsea playing @ Chelsea)
    const normTeam = normalizeClubName(team);
    const normOpp = normalizeClubName(opp);

    const isSelfMatch = Boolean(
      normTeam && normOpp && (
        normTeam === normOpp ||
        normTeam.includes(normOpp) ||
        normOpp.includes(normTeam)
      )
    );

    // If it's a self-match, check if player has a real fixture_opponent that is different
    if (isSelfMatch && player.fixture_opponent && normalizeClubName(player.fixture_opponent) !== normTeam) {
      opp = player.fixture_opponent;
      venue = (player.fixture_venue === 'A') ? '@' : 'vs';
    } else if (isSelfMatch) {
      // Drop redundant self-opponent to prevent "Chelsea · £7.8m · @ Chelsea"
      opp = null;
    }

    if (opp) {
      const rawFdr = Number(player.fdr ?? player.fixture_fdr ?? player.next_fdr ?? 3);
      const fdr = (rawFdr >= 1 && rawFdr <= 5) ? Math.round(rawFdr) : 3;
      const venueTag = (venue === '@' || player.fixture_venue === 'A') ? 'A' : 'H';
      const shortOpp = getClubShortCode(opp);

      fixtureInfo = {
        venue,
        venueTag,
        opponent: opp,
        shortOpp,
        display: `${shortOpp} (${venueTag})`,
        shortDisplay: `${shortOpp} (${venueTag})`,
        fullDisplay: `${opp} (${venueTag})`,
        fdr,
        fdrLabel: `FDR ${fdr}`
      };
    }
  }

  return {
    name,
    team,
    cost: costNum,
    costFormatted,
    position,
    expectedPoints,
    fixtureInfo
  };
}
