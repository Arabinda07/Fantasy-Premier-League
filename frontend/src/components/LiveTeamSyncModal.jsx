import React, { useState } from 'react';
import {
  ArrowsClockwise,
  X,
  CheckCircle,
  WarningCircle,
  ShieldCheck,
  UsersThree
} from '@phosphor-icons/react';

export default function LiveTeamSyncModal({
  isOpen,
  onClose,
  onSyncSuccess,
  currentProfile
}) {
  const [entryId, setEntryId] = useState(currentProfile?.entry_id || '9500404');
  const [leagueId, setLeagueId] = useState(currentProfile?.league_id || '1305495');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  if (!isOpen) return null;

  const handleSync = (e) => {
    e.preventDefault();
    if (!entryId) return;

    setLoading(true);
    setStatusMsg(null);

    // Simulate API fetch delay & profile synchronization
    setTimeout(() => {
      setLoading(false);
      setStatusMsg({
        type: 'success',
        text: `Synced team #${entryId}! Your live lineup, bench order, and mini-league standings are loaded.`
      });

      // Save to localStorage
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
    }, 600);
  };

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
              <ArrowsClockwise size={18} weight="bold" />
            </div>
            <div>
              <h2 id="sync-modal-title" className="modal-title">Sync Official FPL Team & League</h2>
              <p className="modal-subtitle">Import your live squad, bench order, and mini-league rivals directly from FPL</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} weight="bold" />
          </button>
        </div>

        {/* Sync Form */}
        <form onSubmit={handleSync} className="sync-form">
          <div className="form-group">
            <label htmlFor="fpl-entry-id" className="form-label">
              FPL Entry ID:
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
                disabled={loading}
                className="sync-submit-btn"
              >
                <ArrowsClockwise size={15} className={loading ? 'spin-animation' : ''} />
                <span>{loading ? 'Syncing...' : 'Sync Team'}</span>
              </button>
            </div>
            <span className="input-help">
              Find your ID in the URL when viewing "Gameweek History" on fantasy.premierleague.com (e.g. entry/9500404/history)
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="fpl-league-id" className="form-label">
              Classic Mini-League ID (Optional):
            </label>
            <input
              id="fpl-league-id"
              type="text"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
              placeholder="e.g. 123456 (Friends League / Work Cup)"
              className="sync-input font-mono"
            />
            <span className="input-help">
              Pulls rival squads so you can track differentials and protect your mini-league rank.
            </span>
          </div>

          {/* Current Live Profile Preview */}
          <div className="profile-preview-card">
            <div className="profile-header">
              <span className="profile-tag">CONNECTED FPL SQUAD</span>
              <span className="profile-status">
                <span className="status-dot"></span> LIVE SYNCED
              </span>
            </div>
            <div className="profile-grid">
              <div>
                <div className="profile-label">Manager</div>
                <div className="profile-val">{currentProfile?.manager_name || 'Arabinda Saha'}</div>
              </div>
              <div>
                <div className="profile-label">Team Name</div>
                <div className="profile-val">{currentProfile?.team_name || 'Fuljhore Giants'}</div>
              </div>
              <div>
                <div className="profile-label">Money in Bank</div>
                <div className="profile-val font-mono">£{Number(currentProfile?.bank || 0.0).toFixed(1)}m</div>
              </div>
              <div>
                <div className="profile-label">Free Transfers</div>
                <div className="profile-val font-mono">{currentProfile?.free_transfers || 1} Available</div>
              </div>
            </div>
          </div>

          {/* Status Alert */}
          {statusMsg && (
            <div className={`sync-status-alert ${statusMsg.type}`}>
              {statusMsg.type === 'success' ? (
                <CheckCircle size={18} weight="fill" />
              ) : (
                <WarningCircle size={18} weight="fill" />
              )}
              <span>{statusMsg.text}</span>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Done
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
