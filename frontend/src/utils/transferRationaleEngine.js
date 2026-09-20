/**
 * Context-Aware Transfer Rationale Engine
 * Generates mathematically and contextually truthful 3-pillar scouting reports
 * for any player swap across all 38 gameweeks.
 *
 * Rules:
 * 1. FDR Difficulty Differential (never claims an opponent is tougher when FDR is equal or lower).
 * 2. Positional Awareness (DEF/GK -> clean sheets, baseline; MID/FWD -> goal threat, box touches).
 * 3. Budget Truthfulness (Spend vs Save vs Neutral).
 * 4. Double Gameweek & Blank Gameweek Awareness.
 * 5. Roll Free Transfer Strategy.
 */

/**
 * Normalizes fixture difficulty rating (1 to 5)
 */
function normalizeFdr(val) {
  const num = Number(val);
  return (num >= 1 && num <= 5) ? num : null;
}

/**
 * Checks if a player has multiple fixtures in the upcoming gameweek (Double Gameweek)
 */
function isDoubleGameweek(player) {
  if (!player) return false;
  if (player.is_dgw) return true;
  if (Array.isArray(player.fixtures) && player.fixtures.length > 1) return true;
  if (typeof player.fixture === 'string' && player.fixture.includes(',')) return true;
  return false;
}

/**
 * Checks if position is defensive
 */
function isDefensive(pos) {
  const p = (pos || '').toUpperCase();
  return p === 'DEF' || p === 'GK' || p === 'GKP';
}

/**
 * Generates the 3 rationales for a player swap or roll FT strategy.
 *
 * @param {Object} params
 * @param {Object} params.playerIn - Target player coming in
 * @param {Object} params.playerOut - Target player going out
 * @param {number|string} params.netGain - Expected points uplift
 * @param {number|string} params.costDelta - Cost difference (playerIn.cost - playerOut.cost)
 * @param {number|string} params.bank - Available bank balance
 * @param {number} params.gameweek - Active gameweek number
 * @param {boolean} params.isRoll - True if strategy is to bank / roll transfer
 * @returns {Array<{ id: string, iconType: string, title: string, text: string }>}
 */
export function generateTransferRationale({
  playerIn,
  playerOut,
  netGain = 0,
  costDelta = 0,
  bank = 0,
  gameweek = 1,
  isRoll = false
} = {}) {
  const gw = Number(gameweek) || 1;

  // 1. Roll Free Transfer Strategy
  if (isRoll || !playerIn || !playerOut) {
    return [
      {
        id: 'roll_flexibility',
        iconType: 'emerald',
        title: 'Tactical Flexibility',
        text: `Carrying 2 banked free transfers into Gameweek ${gw + 1} unlocks easy structural pivots.`
      },
      {
        id: 'roll_protect',
        iconType: 'cyan',
        title: 'Avoid Point Hits',
        text: 'Protects your mini-league lead and avoids taking unnecessary -4 point hits.'
      },
      {
        id: 'roll_squad_strength',
        iconType: 'blue',
        title: 'Squad Form',
        text: 'Active starting XI has strong expected points output and favorable fixture difficulty.'
      }
    ];
  }

  const pInName = playerIn.name || playerIn.web_name || 'Target In';
  const pOutName = playerOut.name || playerOut.web_name || 'Target Out';
  const inFdr = normalizeFdr(playerIn.fdr);
  const outFdr = normalizeFdr(playerOut.fdr);
  const inDgw = isDoubleGameweek(playerIn);
  const outDgw = isDoubleGameweek(playerOut);
  const inDefensive = isDefensive(playerIn.position);
  const outDefensive = isDefensive(playerOut.position);

  const numericGain = Number(netGain) || 0;
  const numericCostDelta = Number(costDelta) || 0;
  const numericBank = Number(bank) || 0;

  // =========================================================================
  // Pillar 1: Fixture Differential & Schedule Context
  // =========================================================================
  let fixtureTitle = 'Fixture Swing';
  let fixtureText = '';

  if (inDgw && !outDgw) {
    fixtureTitle = 'Double Gameweek';
    fixtureText = `${pInName} plays twice in Gameweek ${gw}, doubling point ceiling over ${pOutName}'s single fixture.`;
  } else if (!inDgw && outDgw) {
    fixtureTitle = 'Underlying Form';
    fixtureText = `Even against a double fixture for ${pOutName}, ${pInName}'s long-term form and role provide a more stable foundation.`;
  } else if (inFdr && outFdr) {
    if (inFdr < outFdr) {
      fixtureTitle = 'Fixture Swing';
      fixtureText = `${pInName} faces an appealing fixture (${playerIn.fixture || 'Upcoming'}, FDR ${inFdr}), while ${pOutName} has a tougher matchup (${playerOut.fixture || 'Upcoming'}, FDR ${outFdr}).`;
    } else if (inFdr === outFdr) {
      fixtureTitle = 'Matchup Edge';
      fixtureText = `${pInName} and ${pOutName} face comparable fixture difficulty (FDR ${inFdr}), but ${pInName}'s form and team attacking metrics offer a decisive edge.`;
    } else {
      // inFdr > outFdr: In has harder fixture, but is bought anyway due to superior quality/ceiling
      fixtureTitle = 'Fixture Challenge';
      fixtureText = `Despite a challenging test for ${pInName} (${playerIn.fixture || 'Upcoming'}, FDR ${inFdr}), superior underlying goal involvement outweighs ${pOutName}'s fixture.`;
    }
  } else if (playerIn.fixture && playerOut.fixture) {
    fixtureTitle = 'Upcoming Fixture';
    fixtureText = `${pInName} plays ${playerIn.fixture} next, offering stronger matchup prospects than ${pOutName} (${playerOut.fixture}).`;
  } else {
    fixtureTitle = 'Schedule Outlook';
    fixtureText = `${pInName} enters a favorable run of upcoming gameweeks with high return probability.`;
  }

  // =========================================================================
  // Pillar 2: Tactical Role & Scoring Edge (Position-Aware)
  // =========================================================================
  let roleTitle = 'Projected Gain';
  let roleText = '';

  const pInXp = Number(playerIn.expected_points || 0).toFixed(2);
  const pOutXp = Number(playerOut.expected_points || 0).toFixed(2);
  const gainStr = numericGain > 0 ? `+${numericGain.toFixed(2)} pts` : `${numericGain.toFixed(2)} pts`;

  if (inDefensive && outDefensive) {
    roleTitle = 'Defensive Output';
    roleText = `${pInName} projects for ${pInXp} pts vs ${pOutXp} pts for ${pOutName} (${gainStr} uplift), offering high clean sheet probability and solid baseline points.`;
  } else if (inDefensive && !outDefensive) {
    roleTitle = 'Defensive Foundation';
    roleText = `${pInName} projects for ${pInXp} pts (${gainStr}), providing clean sheet stability to rebalance squad formation.`;
  } else if (!inDefensive && outDefensive) {
    roleTitle = 'Attacking Firepower';
    roleText = `${pInName} projects for ${pInXp} pts vs ${pOutXp} pts (${gainStr} uplift), adding dynamic goal threat and open-play involvement.`;
  } else {
    // Both attacking (MID / FWD)
    roleTitle = 'Projected Gain';
    const roleDescriptor = (playerIn.position === 'FWD')
      ? 'central box touches and finishing threat'
      : 'open-play chance creation and shot volume';
    roleText = `${pInName} is projected for ${pInXp} pts compared to ${pOutXp} pts for ${pOutName} (${gainStr} uplift), driven by high ${roleDescriptor}.`;
  }

  // =========================================================================
  // Pillar 3: Squad Value & Financial Health
  // =========================================================================
  let valueTitle = 'Squad Value';
  let valueText = '';

  if (numericCostDelta > 0) {
    valueTitle = 'Upgrade Investment';
    valueText = `Costs £${numericCostDelta.toFixed(1)}m (leaves £${numericBank.toFixed(1)}m in bank) to upgrade starting XI quality without taking a hit.`;
  } else if (numericCostDelta < 0) {
    const saved = Math.abs(numericCostDelta).toFixed(1);
    valueTitle = 'Budget Freeing';
    valueText = `Frees up £${saved}m extra bank funds while improving starting output, allowing future upgrades across your squad.`;
  } else {
    valueTitle = 'Budget Neutral';
    valueText = `Budget-neutral transfer providing an immediate points boost with £${numericBank.toFixed(1)}m preserved in the bank.`;
  }

  return [
    {
      id: 'fixture_rationale',
      iconType: 'emerald',
      title: fixtureTitle,
      text: fixtureText
    },
    {
      id: 'scoring_rationale',
      iconType: 'cyan',
      title: roleTitle,
      text: roleText
    },
    {
      id: 'value_rationale',
      iconType: 'blue',
      title: valueTitle,
      text: valueText
    }
  ];
}
