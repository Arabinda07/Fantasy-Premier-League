import React, { useState } from 'react';
import {
  SoccerBall,
  ArrowsClockwise,
  ArrowSquareOut,
  Question,
  CaretDown,
  CaretRight,
  X,
  WarningCircle,
  CheckCircle,
  Eye,
  Lightning
} from '@phosphor-icons/react';

export default function OnboardingModal({
  isOpen,
  onClose,
  onSyncSuccess,
  onExploreDemo
}) {
  const [entryId, setEntryId] = useState('');
  const [leagueId, setLeagueId] = useState('');
  const [showGuide, setShowGuide] = useState(false);
  const [showLeagueInput, setShowLeagueInput] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSync = async (e) => {
    if (e) e.preventDefault();
    setError(null);

    const cleanEntryId = String(entryId).trim();
    if (!cleanEntryId || isNaN(Number(cleanEntryId))) {
      setError('Please enter a valid numeric FPL Team ID (e.g. 9500404).');
      return;
    }

    setIsLoading(true);
    setLoadingStep('Connecting to official FPL servers...');

    try {
      // 1. Fetch from Serverless Sync Endpoint
      const params = new URLSearchParams({ entry_id: cleanEntryId });
      if (leagueId && String(leagueId).trim()) {
        params.append('league_id', String(leagueId).trim());
      }

      setLoadingStep('Fetching picks & transfer history...');
      const response = await fetch(`/api/sync?${params.toString()}`);
      const data = await response.json();

      if (!response.ok || !data.success) {
        if (data.error === 'ENTRY_NOT_FOUND') {
          throw new Error(`FPL Team ID ${cleanEntryId} was not found. Please double-check your ID.`);
        } else if (data.error === 'FPL_MAINTENANCE') {
          throw new Error('Official FPL API is updating gameweek data. Please explore the demo squad for now.');
        } else {
          throw new Error(data.message || 'Failed to sync squad from FPL servers.');
        }
      }

      setLoadingStep('Reconciling 11-component DNA & solving optimal XI...');

      // Save to localStorage
      try {
        localStorage.setItem('fpl_synced_entry_id', cleanEntryId);
        if (leagueId) localStorage.setItem('fpl_synced_league_id', String(leagueId).trim());
        localStorage.setItem('fpl_has_onboarded', 'true');
      } catch (storageErr) {
        console.warn('LocalStorage write failed:', storageErr);
      }

      if (onSyncSuccess) {
        onSyncSuccess(data);
      }
      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('[Onboarding Sync Error]:', err);
      setError(err.message || 'Unable to sync live data. Check your network or try the demo squad.');
    } finally {
      setIsLoading(false);
      setLoadingStep('');
    }
  };

  const handleDemo = () => {
    try {
      localStorage.setItem('fpl_has_onboarded', 'true');
    } catch (err) {
      console.warn('LocalStorage write failed:', err);
    }
    if (onExploreDemo) {
      onExploreDemo();
    }
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content onboarding-modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
      >
        {/* Header Badge */}
        <div className="onboarding-badge">
          <SoccerBall size={14} weight="fill" />
          <span>FPL INTELLIGENCE TERMINAL · 2026-27</span>
        </div>

        {/* Title and Subtitle */}
        <h2 id="onboarding-title" className="onboarding-title">
          Deploy ML Predictions to Your Squad
        </h2>
        <p className="onboarding-desc">
          Enter your FPL Team ID to simulate optimal starting formations, algorithm captaincy,
          and budget-constrained transfer upgrades tailored to your exact 15 players.
        </p>

        {/* Error Alert */}
        {error && (
          <div className="sync-error-banner" role="alert">
            <WarningCircle size={18} weight="bold" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <div style={{ fontWeight: 700, marginBottom: '2px' }}>Sync Notice</div>
              <div>{error}</div>
            </div>
          </div>
        )}

        {/* Sync Form */}
        <form onSubmit={handleSync} className="sync-form">
          <div className="form-group">
            <label htmlFor="onboarding-entry-id" className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>FPL Team ID (Entry ID)</span>
              <button
                type="button"
                className="id-finder-toggle"
                onClick={() => setShowGuide(!showGuide)}
                aria-expanded={showGuide}
              >
                <Question size={13} weight="bold" />
                <span>{showGuide ? 'Hide Guide' : 'Where is my Team ID?'}</span>
              </button>
            </label>

            <input
              id="onboarding-entry-id"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={entryId}
              onChange={(e) => setEntryId(e.target.value)}
              placeholder="e.g. 9500404"
              className="sync-input font-mono"
              autoFocus
              disabled={isLoading}
            />

            {/* Expandable ID Discovery Guide */}
            {showGuide && (
              <div className="id-finder-card">
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  How to find your 7-digit Team ID (10 seconds):
                </div>
                <ol className="id-finder-steps">
                  <li>Log in at <strong>fantasy.premierleague.com</strong>.</li>
                  <li>Click on the <strong>'Points'</strong> or <strong>'Gameweek History'</strong> tab.</li>
                  <li>Look at your browser address bar:</li>
                </ol>
                <div className="id-finder-url-box">
                  <span>fantasy.premierleague.com/entry/<mark>9500404</mark>/history</span>
                </div>
                <a
                  href="https://fantasy.premierleague.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="id-finder-link"
                >
                  <span>Open fantasy.premierleague.com in new tab</span>
                  <ArrowSquareOut size={12} weight="bold" />
                </a>
              </div>
            )}
          </div>

          {/* Optional Mini-League Section */}
          <div className="form-group">
            {!showLeagueInput ? (
              <button
                type="button"
                className="id-finder-toggle"
                style={{ alignSelf: 'flex-start', textDecoration: 'none' }}
                onClick={() => setShowLeagueInput(true)}
              >
                <CaretRight size={12} weight="bold" />
                <span>+ Add Classic Mini-League ID for Rival Radar (Optional)</span>
              </button>
            ) : (
              <div>
                <label htmlFor="onboarding-league-id" className="form-label">
                  Classic Mini-League ID (Optional)
                </label>
                <input
                  id="onboarding-league-id"
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
                  Found in your mini-league URL: leagues-classic/<strong>1305495</strong>/standings
                </span>
              </div>
            )}
          </div>

          {/* Kinetic Loading Status */}
          {isLoading && (
            <div className="sync-ticker-box">
              <ArrowsClockwise size={15} className="spin-animation" />
              <span>{loadingStep}</span>
            </div>
          )}

          {/* Actions */}
          <div className="onboarding-actions">
            <button
              type="submit"
              className="btn-primary-action"
              disabled={isLoading || !entryId.trim()}
            >
              {isLoading ? (
                <>
                  <ArrowsClockwise size={16} className="spin-animation" />
                  <span>Syncing Live Squad...</span>
                </>
              ) : (
                <>
                  <Lightning size={16} weight="fill" />
                  <span>Sync My Squad & Optimize Lineup</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="btn-secondary-action"
              onClick={handleDemo}
              disabled={isLoading}
            >
              <Eye size={15} weight="bold" />
              <span>Explore Demo Squad (GW2 Top-10k Template)</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
