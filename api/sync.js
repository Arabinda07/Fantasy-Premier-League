/**
 * Vercel Serverless Function: Multi-User FPL Live Sync Endpoint
 * 
 * Route: /api/sync?entry_id=123456[&gw=1][&league_id=1305495]
 * 
 * Concurrently queries the official Fantasy Premier League REST endpoints,
 * computes rolling free transfers (1..5), enriches mini-league rival data,
 * and returns a consolidated, CORS-compliant JSON payload.
 */

const FPL_BASE_URL = 'https://fantasy.premierleague.com/api';

const DEFAULT_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json',
};

/**
 * Robust fetch with timeout and status handling
 */
async function fetchFpl(url, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      headers: DEFAULT_HEADERS,
      signal: controller.signal,
    });

    if (res.status === 503) {
      const err = new Error('FPL_MAINTENANCE');
      err.code = 'FPL_MAINTENANCE';
      err.status = 503;
      throw err;
    }

    if (res.status === 404) {
      const err = new Error('NOT_FOUND');
      err.code = 'NOT_FOUND';
      err.status = 404;
      throw err;
    }

    if (!res.ok) {
      const err = new Error(`FPL_HTTP_${res.status}`);
      err.status = res.status;
      throw err;
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      const timeoutErr = new Error('FPL_TIMEOUT');
      timeoutErr.code = 'FPL_TIMEOUT';
      timeoutErr.status = 504;
      throw timeoutErr;
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Calculate available rolling Free Transfers (1..5) using official 2024-25+ rules.
 */
export function calculateFreeTransfers(transfersHistory, targetGw = 1) {
  if (!targetGw || targetGw <= 1) return 1;
  if (!Array.isArray(transfersHistory) || transfersHistory.length === 0) {
    // If no transfers made across previous GWs, accumulate +1 per GW up to 5
    return Math.min(5, targetGw);
  }

  // Count transfers per gameweek
  const gwTransfers = {};
  for (const t of transfersHistory) {
    const ev = t.event;
    if (ev != null) {
      gwTransfers[ev] = (gwTransfers[ev] || 0) + 1;
    }
  }

  // Detect Wildcard / Free Hit bulk transfers (4+ transfers with 0 total cost)
  const chipGws = new Set();
  for (const gwStr of Object.keys(gwTransfers)) {
    const gwNum = parseInt(gwStr, 10);
    if (gwTransfers[gwNum] >= 4) {
      const moves = transfersHistory.filter((t) => t.event === gwNum);
      const totalCost = moves.reduce((sum, m) => sum + (m.event_transfers_cost || 0), 0);
      if (totalCost === 0) {
        chipGws.add(gwNum);
      }
    }
  }

  // Replay FT accumulation from GW1 to targetGw - 1
  let ft = 1; // GW1 starts with 1 FT
  for (let g = 1; g < targetGw; g++) {
    if (chipGws.has(g)) {
      ft = Math.min(5, ft + 1);
      continue;
    }

    const used = gwTransfers[g] || 0;
    if (used <= ft) {
      const remaining = ft - used;
      ft = Math.min(5, remaining + 1);
    } else {
      // Took hits: FT resets to 1 for the next GW
      ft = 1;
    }
  }

  return Math.max(1, Math.min(5, ft));
}

/**
 * Main Serverless Handler
 */
export default async function handler(req, res) {
  // 1. CORS Headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
  );

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // 2. Parse Query Parameters
  const query = req.query || {};
  // Support standard URL query if req.query is undefined (e.g. native Node runner)
  let rawEntryId = query.entry_id || query.id;
  let rawGw = query.gw || query.event;
  let rawLeagueId = query.league_id || query.league;

  if (!rawEntryId && req.url && req.url.includes('?')) {
    const urlParams = new URLSearchParams(req.url.split('?')[1]);
    rawEntryId = urlParams.get('entry_id') || urlParams.get('id');
    rawGw = urlParams.get('gw') || urlParams.get('event');
    rawLeagueId = urlParams.get('league_id') || urlParams.get('league');
  }

  const entryId = parseInt(rawEntryId, 10);
  if (!entryId || isNaN(entryId)) {
    res.status(400).json({
      success: false,
      error: 'INVALID_ENTRY_ID',
      message: 'A valid numeric FPL Entry ID (e.g. 9500404) is required.',
    });
    return;
  }

  const leagueId = rawLeagueId ? parseInt(rawLeagueId, 10) : null;

  try {
    // 3. Fetch Entry Summary
    let summary;
    try {
      summary = await fetchFpl(`${FPL_BASE_URL}/entry/${entryId}/`);
    } catch (err) {
      if (err.code === 'NOT_FOUND') {
        res.status(404).json({
          success: false,
          error: 'ENTRY_NOT_FOUND',
          message: `FPL Entry ID ${entryId} was not found on the official FPL server.`,
        });
        return;
      }
      if (err.code === 'FPL_MAINTENANCE') {
        res.status(503).json({
          success: false,
          error: 'FPL_MAINTENANCE',
          message: 'The official FPL API is currently updating for the gameweek. Please try again shortly.',
        });
        return;
      }
      throw err;
    }

    // Determine target gameweek
    const currentEvent = summary.current_event || 1;
    let targetGw = rawGw ? parseInt(rawGw, 10) : currentEvent;
    if (isNaN(targetGw) || targetGw < 1) targetGw = 1;

    // 4. Concurrently fetch picks, transfers, and mini-league standings
    const promises = {
      picks: (async () => {
        try {
          return await fetchFpl(`${FPL_BASE_URL}/entry/${entryId}/event/${targetGw}/picks/`);
        } catch (err) {
          // If target GW picks not yet available (404), fall back to previous GW
          if (err.code === 'NOT_FOUND' && targetGw > 1) {
            try {
              return await fetchFpl(`${FPL_BASE_URL}/entry/${entryId}/event/${targetGw - 1}/picks/`);
            } catch (fallbackErr) {
              return { picks: [], entry_history: null, active_chip: null };
            }
          }
          return { picks: [], entry_history: null, active_chip: null };
        }
      })(),
      transfers: (async () => {
        try {
          return await fetchFpl(`${FPL_BASE_URL}/entry/${entryId}/transfers/`);
        } catch {
          return [];
        }
      })(),
      league: (async () => {
        if (!leagueId) return null;
        try {
          return await fetchFpl(`${FPL_BASE_URL}/leagues-classic/${leagueId}/standings/`);
        } catch {
          return null;
        }
      })(),
    };

    const results = await Promise.all([promises.picks, promises.transfers, promises.league]);
    const [picksData, transfersData, leagueData] = results;

    // 5. Calculate Free Transfers
    const freeTransfers = calculateFreeTransfers(transfersData, targetGw);

    // 6. Enrich Rivals if league data is present
    let enrichedRivals = [];
    let leagueName = null;

    if (leagueData && leagueData.standings && Array.isArray(leagueData.standings.results)) {
      leagueName = leagueData.league ? leagueData.league.name : `Mini-League #${leagueId}`;
      const topResults = leagueData.standings.results
        .filter((r) => r.entry !== entryId)
        .slice(0, 5);

      // Fetch picks for top rivals concurrently
      const rivalPicksPromises = topResults.map(async (r) => {
        try {
          let rivalPicks = await fetchFpl(`${FPL_BASE_URL}/entry/${r.entry}/event/${targetGw}/picks/`);
          if ((!rivalPicks || !rivalPicks.picks || rivalPicks.picks.length === 0) && targetGw > 1) {
            rivalPicks = await fetchFpl(`${FPL_BASE_URL}/entry/${r.entry}/event/${targetGw - 1}/picks/`);
          }

          const picksList = rivalPicks?.picks || [];
          const captPick = picksList.find((p) => p.is_captain);

          return {
            entry_id: r.entry,
            manager_name: r.player_name || `Manager ${r.entry}`,
            team_name: r.entry_name || `Team ${r.entry}`,
            rank: r.rank || 0,
            overall_rank: r.rank || 0,
            total_points: r.total || 0,
            event_points: r.event_total || 0,
            captain_element: captPick ? captPick.element : null,
            squad_elements: picksList.map((p) => p.element),
          };
        } catch {
          return {
            entry_id: r.entry,
            manager_name: r.player_name || `Manager ${r.entry}`,
            team_name: r.entry_name || `Team ${r.entry}`,
            rank: r.rank || 0,
            overall_rank: r.rank || 0,
            total_points: r.total || 0,
            event_points: r.event_total || 0,
            captain_element: null,
            squad_elements: [],
          };
        }
      });

      enrichedRivals = await Promise.all(rivalPicksPromises);
    }

    // 7. Format Consolidated Response
    const rawPicks = picksData?.picks || [];
    const entryHist = picksData?.entry_history || {};

    const bank = (entryHist.bank != null ? entryHist.bank : (summary.last_deadline_bank || 0)) / 10.0;
    const teamValue = (entryHist.value != null ? entryHist.value : (summary.last_deadline_value || 1000)) / 10.0;

    const responsePayload = {
      success: true,
      timestamp: new Date().toISOString(),
      gameweek: targetGw,
      manager_profile: {
        entry_id: entryId,
        manager_name: `${summary.player_first_name || ''} ${summary.player_last_name || ''}`.trim() || `Manager ${entryId}`,
        team_name: summary.name || `Team ${entryId}`,
        overall_rank: summary.summary_overall_rank || 0,
        overall_points: summary.summary_overall_points || 0,
        bank: Number(bank.toFixed(1)),
        team_value: Number(teamValue.toFixed(1)),
        free_transfers: freeTransfers,
        active_chip: picksData?.active_chip || null,
        squad_elements: rawPicks.map((p) => p.element),
        squad_picks: rawPicks.map((p) => ({
          element: p.element,
          position: p.position,
          multiplier: p.multiplier || 1,
          is_captain: Boolean(p.is_captain),
          is_vice_captain: Boolean(p.is_vice_captain),
          selling_price: p.selling_price ? Number((p.selling_price / 10.0).toFixed(1)) : null,
          purchase_price: p.purchase_price ? Number((p.purchase_price / 10.0).toFixed(1)) : null,
        })),
        league_id: leagueId,
        league_name: leagueName,
      },
      transfers_history: transfersData,
      league_standings: leagueData,
      rivals: enrichedRivals,
    };

    res.status(200).json(responsePayload);
  } catch (err) {
    console.error(`[API /api/sync] Internal Error:`, err);
    res.status(500).json({
      success: false,
      error: 'SERVER_ERROR',
      message: err.message || 'An unexpected error occurred while syncing with FPL servers.',
    });
  }
}
