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

  const handleResetOnboarding = () => {
    try {
      localStorage.removeItem('fpl_has_onboarded');
      localStorage.removeItem('fpl_synced_entry_id');
      localStorage.removeItem('fpl_synced_league_id');
      window.location.reload();
    } catch (e) {
      console.warn(e);
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
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-box">
              <SoccerBall size={18} weight="fill" />
            </div>
            <div>
              <h2 id="sync-modal-title" className="modal-title">
                Squad Configuration & Sync
              </h2>
              <p className="modal-subtitle">
                Official FPL Team ID & Classic Mini-League Tracker
              </p>
            </div>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={16} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSync} className="sync-modal-body">
          {error && (
            <div className="sync-error-banner" role="alert">
              <WarningCircle size={16} weight="fill" className="error-icon" />
              <div>
                <strong>Sync Notice</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {saved && (
            <div className="sync-success-banner" role="status">
              <CheckCircle size={16} weight="fill" className="success-icon" />
              <span>Squad & Mini-League successfully synced with FPL servers!</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="fpl-entry-id" className="form-label">
              FPL Team ID (Entry ID)
            </label>
            <div className="input-action-row">
              <input
                id="fpl-entry-id"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={entryId}
                onChange={(e) => setEntryId(e.target.value)}
                placeholder="e.g. 9500404"
                className="sync-input font-mono"
                required
                disabled={isLoading}
              />
              <button
                type="submit"
                className="btn-primary sync-submit-btn font-mono"
                disabled={isLoading}
              >
                <ArrowsClockwise
                  size={14}
                  weight="bold"
                  className={isLoading ? 'spin-animation' : ''}
                />
                <span>{isLoading ? 'Syncing...' : 'Sync Live Data'}</span>
              </button>
            </div>
            <span className="input-help">
              Found at: fantasy.premierleague.com/entry/<strong>{entryId || 'YOUR_ID'}</strong>/history
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

          {isLoading && (
            <div className="sync-ticker-box">
              <ArrowsClockwise size={15} className="spin-animation" />
              <span>{loadingStep}</span>
            </div>
          )}

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

          <div className="modal-actions" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              type="button"
              className="btn-secondary font-mono"
              style={{ fontSize: '11px', color: 'var(--text-muted)' }}
              onClick={handleResetOnboarding}
              title="Clear cached profile and restart onboarding"
            >
              Reset / Reopen Onboarding
            </button>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
