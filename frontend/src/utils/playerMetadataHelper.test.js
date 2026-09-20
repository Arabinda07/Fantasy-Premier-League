import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { resolvePlayerMetadata } from './playerMetadataHelper.js';

describe('resolvePlayerMetadata', () => {
  it('prevents self-opponent collision bug (Chelsea vs @ Chelsea)', () => {
    const player = {
      web_name: 'João Pedro',
      team: 'Chelsea',
      cost: 7.8,
      position: 'FWD',
      expected_points: 2.95,
      fixture: '@ Chelsea',
      fdr: 4
    };

    const meta = resolvePlayerMetadata(player);
    assert.equal(meta.team, 'Chelsea');
    assert.equal(meta.costFormatted, '7.8');
    // fixtureInfo should be sanitized to null or real fixture since Chelsea cannot play Chelsea
    assert.equal(meta.fixtureInfo, null);
  });

  it('correctly formats valid opponents with FDR', () => {
    const player = {
      web_name: 'Wissa',
      team: 'Newcastle',
      cost: 6.2,
      position: 'FWD',
      expected_points: 3.58,
      fixture: '@ Coventry',
      fdr: 2
    };

    const meta = resolvePlayerMetadata(player);
    assert.equal(meta.team, 'Newcastle');
    assert.equal(meta.costFormatted, '6.2');
    assert.deepEqual(meta.fixtureInfo, {
      venue: '@',
      venueTag: 'A',
      opponent: 'Coventry',
      shortOpp: 'COV',
      display: 'COV (A)',
      shortDisplay: 'COV (A)',
      fullDisplay: 'Coventry (A)',
      fdr: 2,
      fdrLabel: 'FDR 2'
    });
  });

  it('recovers fixture_opponent if primary fixture matches player club', () => {
    const player = {
      web_name: 'João Pedro',
      team: 'Chelsea',
      cost: 7.8,
      position: 'FWD',
      expected_points: 2.95,
      fixture: '@ Chelsea',
      fixture_opponent: 'Arsenal',
      fixture_venue: 'A',
      fixture_fdr: 5
    };

    const meta = resolvePlayerMetadata(player);
    assert.equal(meta.team, 'Chelsea');
    assert.deepEqual(meta.fixtureInfo, {
      venue: '@',
      venueTag: 'A',
      opponent: 'Arsenal',
      shortOpp: 'ARS',
      display: 'ARS (A)',
      shortDisplay: 'ARS (A)',
      fullDisplay: 'Arsenal (A)',
      fdr: 5,
      fdrLabel: 'FDR 5'
    });
  });

  it('correctly formats home fixture with (H)', () => {
    const player = {
      web_name: 'Wissa',
      team: 'Newcastle',
      cost: 6.2,
      position: 'FWD',
      expected_points: 3.58,
      fixture: 'vs Bournemouth',
      fixture_venue: 'H',
      fdr: 3
    };

    const meta = resolvePlayerMetadata(player);
    assert.equal(meta.fixtureInfo.venueTag, 'H');
    assert.equal(meta.fixtureInfo.display, 'BOU (H)');
  });
});
