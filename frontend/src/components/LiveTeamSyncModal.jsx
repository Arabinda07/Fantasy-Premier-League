import React, { useState } from 'react';
import {
  ArrowsClockwise,
  X,
  CheckCircle,
  Info,
  SoccerBall,
  UsersThree
} from '@phosphor-icons/react';

// WHY real-time sync doesn't work from the browser:
// The official FPL API (fantasy.premierleague.com/api/*) blocks browser
// requests with CORS headers — it only serves responses to its own origin.
// A proper sync would require a backend proxy / cloud function.
// For now the modal:
//   1. Shows the pre-loaded squad from live_matchday_gw2.json (accurate GW2 data)
//   2. Lets the user update their stored Entry ID / League ID (persisted to localStorage)
//   3. Explains honestly that a backend proxy would be needed for live sync

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
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    if (!entryId) return;

    try {
      localStorage.setItem('fpl_synced_entry_id', entryId);
      localStorage.setItem('fpl_synced_league_id', leagueId);
    } catch (err) {
      console.error('LocalStorage write error:', err);
    }

    if (onSyncSuccess) {
      onSyncSuccess({
        entry_id: parseInt(entryId, 10),
        manager_name: currentProfile?.manager_name || 'Arabinda Saha',
        team_name: currentProfile?.team_name || 'Fuljhore Giants',
        league_id: leagueId
      });
    }

    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
              <h2 id="sync-modal-title" className="modal-title">Squad Configuration</h2>
              <p className="modal-subtitle">
                Pre-loaded GW2 squad · update IDs for reference tracking
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} weight="bold" />
          </button>
        </div>

        {/* Info Notice — honest about what works */}
        <div className="sync-notice-banner">
          <Info size={15} weight="bold" style={{ flexShrink: 0, marginTop: '1px' }} />
          <span>
            Live API sync requires a backend proxy (the FPL API blocks browser requests via CORS).
            Your squad data is pre-loaded from the GW2 LP solver output and is accurate.
            Saving your IDs here stores them locally for display purposes.
          </span>
        </div>

        {/* ID Config Form */}
        <form onSubmit={handleSave} className="sync-form">
          <div className="form-group">
            <label htmlFor="fpl-entry-id" className="form-label">
              FPL Entry ID
            </label>
            <div className="input-with-button">
              <input
                id="fpl-entry-id"
                type="number"
                value={entryId}
                onChange={(e) => setEntryId(e.target.value)}
                placeholder="e.g. 9500404"
                required
                className="sync-input font-mono"
              />
              <button
                type="submit"
                className="sync-submit-btn"
              >
                {saved ? <CheckCircle size={15} weight="fill" /> : <ArrowsClockwise size={15} />}
                <span>{saved ? 'Saved!' : 'Save IDs'}</span>
              </button>
            </div>
            <span className="input-help">
              Found at: fantasy.premierleague.com/entry/<strong>{entryId}</strong>/history
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="fpl-league-id" className="form-label">
              Classic Mini-League ID
            </label>
            <input
              id="fpl-league-id"
              type="text"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
              placeholder="e.g. 1305495"
              className="sync-input font-mono"
            />
            <span className="input-help">
              Used to populate the Rival Radar tab with your mini-league standings.
            </span>
          </div>

          {/* Live Squad Preview (from pre-loaded JSON) */}
          <div className="profile-preview-card">
            <div className="profile-header">
              <span className="profile-tag">
                <UsersThree size={12} weight="bold" style={{ display: 'inline', marginRight: '4px' }} />
                PRE-LOADED GW2 SQUAD
              </span>
              <span className="profile-status">
                <span className="status-dot" />
                DATA CURRENT
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
