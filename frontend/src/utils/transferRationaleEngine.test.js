/**
 * Unit Test Suite for Context-Aware Transfer Rationale Engine
 */
import assert from 'node:assert';
import { generateTransferRationale } from './transferRationaleEngine.js';

console.log('🧪 Starting Transfer Rationale Engine Test Suite...\n');

// 1. Fixture Swing: Lower FDR vs Higher FDR
console.log('▶ Test 1: Easier FDR in vs Harder FDR out');
const res1 = generateTransferRationale({
  playerIn: { name: 'Wissa', position: 'FWD', fixture: '@ Coventry', fdr: 2, expected_points: 5.33, cost: 6.1 },
  playerOut: { name: 'João Pedro', position: 'FWD', fixture: '@ Chelsea', fdr: 4, expected_points: 3.85, cost: 5.7 },
  netGain: 1.48,
  costDelta: 0.4,
  bank: 0.5,
  gameweek: 6
});

assert.strictEqual(res1.length, 3);
assert.strictEqual(res1[0].title, 'Fixture Swing');
assert.ok(res1[0].text.includes('FDR 2'));
assert.ok(res1[0].text.includes('FDR 4'));
assert.strictEqual(res1[1].title, 'Projected Gain');
assert.ok(res1[1].text.includes('+1.48 pts'));
assert.strictEqual(res1[2].title, 'Upgrade Investment');
assert.ok(res1[2].text.includes('Costs £0.4m'));
console.log('  ✔ Test 1 passed.');

// 2. Equal FDR: Matchup Edge
console.log('▶ Test 2: Equal FDR matchup');
const res2 = generateTransferRationale({
  playerIn: { name: 'Mbeumo', position: 'MID', fixture: 'WOL (H)', fdr: 3, expected_points: 6.2, cost: 7.1 },
  playerOut: { name: 'Gordon', position: 'MID', fixture: 'FUL (A)', fdr: 3, expected_points: 4.8, cost: 7.3 },
  netGain: 1.4,
  costDelta: -0.2,
  bank: 1.0,
  gameweek: 7
});

assert.strictEqual(res2[0].title, 'Matchup Edge');
assert.ok(res2[0].text.includes('comparable fixture difficulty'));
assert.strictEqual(res2[2].title, 'Budget Freeing');
assert.ok(res2[2].text.includes('Frees up £0.2m'));
console.log('  ✔ Test 2 passed.');

// 3. Harder FDR: Fixture Challenge without inverted claims
console.log('▶ Test 3: Harder FDR for incoming elite player');
const res3 = generateTransferRationale({
  playerIn: { name: 'Haaland', position: 'FWD', fixture: 'ARS (H)', fdr: 4, expected_points: 7.5, cost: 15.2 },
  playerOut: { name: 'Solanke', position: 'FWD', fixture: 'SOU (H)', fdr: 2, expected_points: 4.5, cost: 7.5 },
  netGain: 3.0,
  costDelta: 7.7,
  bank: 8.0,
  gameweek: 5
});

assert.strictEqual(res3[0].title, 'Fixture Challenge');
assert.ok(res3[0].text.includes('challenging test'));
assert.ok(!res3[0].text.includes('tougher matchup for Solanke')); // Never inverts truth
console.log('  ✔ Test 3 passed.');

// 4. Defender-to-Defender Transfer (Clean Sheet terminology)
console.log('▶ Test 4: Defender transfer terminology');
const res4 = generateTransferRationale({
  playerIn: { name: 'Gabriel', position: 'DEF', fixture: 'LEI (H)', fdr: 2, expected_points: 5.5, cost: 6.1 },
  playerOut: { name: 'Konsa', position: 'DEF', fixture: 'MCI (A)', fdr: 5, expected_points: 2.1, cost: 4.5 },
  netGain: 3.4,
  costDelta: 1.6,
  bank: 2.0,
  gameweek: 6
});

assert.strictEqual(res4[1].title, 'Defensive Output');
assert.ok(res4[1].text.includes('clean sheet probability'));
assert.ok(!res4[1].text.includes('firepower')); // Never calls defenders firepower
console.log('  ✔ Test 4 passed.');

// 5. Double Gameweek Detection
console.log('▶ Test 5: Double Gameweek awareness');
const res5 = generateTransferRationale({
  playerIn: { name: 'Palmer', position: 'MID', fixture: 'BOU (A), EVE (H)', fdr: 2, is_dgw: true, expected_points: 11.2, cost: 10.8 },
  playerOut: { name: 'Saka', position: 'MID', fixture: 'MCI (A)', fdr: 5, expected_points: 4.1, cost: 10.0 },
  netGain: 7.1,
  costDelta: 0.8,
  bank: 1.0,
  gameweek: 34
});

assert.strictEqual(res5[0].title, 'Double Gameweek');
assert.ok(res5[0].text.includes('plays twice in Gameweek 34'));
console.log('  ✔ Test 5 passed.');

// 6. Roll Free Transfer Strategy
console.log('▶ Test 6: Roll Free Transfer strategy');
const res6 = generateTransferRationale({
  isRoll: true,
  gameweek: 8
});

assert.strictEqual(res6.length, 3);
assert.strictEqual(res6[0].title, 'Tactical Flexibility');
assert.ok(res6[0].text.includes('Gameweek 9'));
assert.strictEqual(res6[1].title, 'Avoid Point Hits');
assert.strictEqual(res6[2].title, 'Squad Form');
console.log('  ✔ Test 6 passed.');

console.log('\n================================================================');
console.log('🎉 ALL 6 TRANSFER RATIONALE ENGINE TESTS PASSED CLEANLY.');
console.log('================================================================\n');
