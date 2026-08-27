import React, { useState } from 'react';
import {
  ArrowsClockwise,
  X,
  CheckCircle,
  WarningCircle,
  SoccerBall,
  UsersThree,
  ArrowSquareOut
} from '@phosphor-icons/react';

export default function LiveTeamSyncModal({
  isOpen,
  onClose,
  onSyncSuccess,
  currentProfile
}) {
  const [entryId, setEntryId] = useState(
    () => localStorage.getItem('fpl_synced_entry_id') || String(currentProfile?.entry_id || '9500404')
  );
  const [leagueId, setLeagueId] = useState(
    () => localStorage.getItem('fpl_synced_league_id') || String(currentProfile?.league_id || '1305495')
  );
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSync = async (e) => {
    if (e) e.preventDefault();
    setError(null);
    setSaved(false);

    const cleanEntryId = String(entryId).trim();
    if (!cleanEntryId || isNaN(Number(cleanEntryId))) {
      setError('Please enter a valid numeric FPL Team ID.');
      return;
    }

    setIsLoading(true);
    setLoadingStep('Connecting to official FPL servers...');

    try {
      const params = new URLSearchParams({ entry_id: cleanEntryId });
      if (leagueId && String(leagueId).trim()) {
        params.append('league_id', String(leagueId).trim());
      }

      setLoadingStep('Fetching picks & transfer history...');
      const response = await fetch(`/api/sync?${params.toString()}`);
      
      const contentType = response.headers.get('content-type') || '';
      let data;
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        throw new Error('Sync endpoint returned non-JSON data. If running locally, ensure the dev server is active.');
      }

      if (!response.ok || !data.success) {
        if (data.error === 'ENTRY_NOT_FOUND') {
          throw new Error(`FPL Team ID ${cleanEntryId} was not found on FPL servers.`);
        } else if (data.error === 'FPL_MAINTENANCE') {
          throw new Error('Official FPL API is currently updating gameweek data.');
        } else {
          throw new Error(data.message || 'Failed to fetch squad data.');
        }
      }

      // Save to localStorage
      try {
        localStorage.setItem('fpl_synced_entry_id', cleanEntryId);
        if (leagueId) localStorage.setItem('fpl_synced_league_id', String(leagueId).trim());
      } catch (err) {
        console.warn('LocalStorage write failed:', err);
      }

      if (onSyncSuccess) {
        onSyncSuccess(data);
      }

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('[Sync Modal Error]:', err);
      setError(err.message || 'Unable to sync live data. Please check your connection or ID.');
    } finally {
      setIsLoading(false);
      setLoadingStep('');
    }
  };

  const manager = currentProfile;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content sync-modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sync-modal-title"
      >
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="sync-icon-wrapper">
              <SoccerBall size={18} weight="fill" />
            </div>
            <div>
              <h2 id="sync-modal-title" className="modal-title">Squad Configuration & Sync</h2>
              <p className="modal-subtitle">
                Official FPL Team ID & Classic Mini-League Tracker
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} weight="bold" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="sync-error-banner" role="alert">
            <WarningCircle size={18} weight="bold" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <div style={{ fontWeight: 700 }}>Sync Notice</div>
              <div>{error}</div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSync} className="sync-form">
          <div className="form-group">
            <label htmlFor="fpl-entry-id" className="form-label">
              FPL Team ID (Entry ID)
            </label>
            <div className="input-with-button">
              <input
                id="fpl-entry-id"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={entryId}
                onChange={(e) => setEntryId(e.target.value)}
                placeholder="e.g. 9500404"
                required
                className="sync-input font-mono"
                disabled={isLoading}
              />
              <button
                type="submit"
                className="sync-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <ArrowsClockwise size={15} className="spin-animation" />
                    <span>Syncing...</span>
                  </>
                ) : saved ? (
                  <>
                    <CheckCircle size={15} weight="fill" />
                    <span>Synced!</span>
                  </>
                ) : (
                  <>
                    <ArrowsClockwise size={15} />
                    <span>Sync Live Data</span>
                  </>
                )}
              </button>
            </div>
            <span className="input-help">
              Found at: fantasy.premierleague.com/entry/<strong>{entryId || '9500404'}</strong>/history
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="fpl-league-id" className="form-label">
              Classic Mini-League ID (Optional)
            </label>
            <input
              id="fpl-league-id"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
              placeholder="e.g. 1305495"
              className="sync-input font-mono"
              disabled={isLoading}
            />
            <span className="input-help">
              Used to populate the Rival Radar tab with your mini-league standings.
            </span>
          </div>

          {/* Kinetic Loading Status */}
          {isLoading && (
            <div className="sync-ticker-box">
              <ArrowsClockwise size={15} className="spin-animation" />
              <span>{loadingStep}</span>
            </div>
          )}

          {/* Live Squad Preview Card */}
          <div className="profile-preview-card">
            <div className="profile-header">
              <span className="profile-tag">
                <UsersThree size={12} weight="bold" style={{ display: 'inline', marginRight: '4px' }} />
                ACTIVE SQUAD ROSTER
              </span>
              <span className="profile-status">
                <span className="live-sync-indicator" />
                <span>LIVE SYNC ACTIVE</span>
              </span>
            </div>
            <div className="profile-grid">
              <div>
                <div className="profile-label">Manager</div>
                <div className="profile-val">{manager?.manager_name || 'Arabinda Saha'}</div>
              </div>
              <div>
                <div className="profile-label">Team</div>
                <div className="profile-val">{manager?.team_name || 'Fuljhore Giants'}</div>
              </div>
              <div>
                <div className="profile-label">Bank</div>
                <div className="profile-val font-mono">£{Number(manager?.bank || 0.0).toFixed(1)}m</div>
              </div>
              <div>
                <div className="profile-label">Free Transfers</div>
                <div className="profile-val font-mono">{manager?.free_transfers || 1} FT</div>
              </div>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
