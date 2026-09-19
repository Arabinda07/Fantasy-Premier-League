import React, { useEffect, useRef } from 'react';
import {
  ShieldCheck,
  X,
  ArrowSquareOut,
  CheckCircle,
  WarningCircle,
  CaretRight,
  User,
  Crown
} from '@phosphor-icons/react';

export default function MatchdayHandoverModal({
  isOpen,
  onClose,
  onConfirmLock,
  liveData,
  starters = [],
  bench = [],
  managerId = '9500404',
  managerName = 'Arabinda Saha',
  teamName = 'Fuljhore Giants',
  freeTransfers = 1,
  isLocked = false
}) {
  const modalRef = useRef(null);

  // Keyboard accessibility: Focus placement, Escape key to dismiss & focus trap (WCAG 2.1.2 & 2.4.3)
  useEffect(() => {
    if (!isOpen) return;

    // Auto-focus dialog on mount for assistive tech and keyboard users
    const focusTimer = setTimeout(() => {
      if (modalRef.current) {
        modalRef.current.focus();
      }
    }, 50);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      clearTimeout(focusTimer);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const gw = liveData?.gameweek || 6;
  const capt = starters.find(p => p.is_captain) || starters[0];
  const vc = starters.find(p => p.is_vice_captain) || starters[1];

  const getPlayerXp = (p) => {
    if (!p) return 0;
    const val = p.dynamicXp ?? p.expected_points ?? p.xp ?? p.xP ?? 0;
    return Number(val) || 0;
  };

  const captXp = capt ? (getPlayerXp(capt) * 2).toFixed(1) : '0.0';
  const vcXp = vc ? getPlayerXp(vc).toFixed(1) : '0.0';

  const defs = starters.filter(p => p.position === 'DEF');
  const mids = starters.filter(p => p.position === 'MID');
  const fwds = starters.filter(p => p.position === 'FWD');
  const formationStr = `${defs.length}-${mids.length}-${fwds.length}`;

  const startersBaseSum = starters.reduce((acc, p) => acc + getPlayerXp(p), 0);
  const totalStartingXp = (startersBaseSum + (capt ? getPlayerXp(capt) : 0)).toFixed(1);

  // Official FPL URLs with actual manager entry ID
  const officialTeamUrl = `https://fantasy.premierleague.com/entry/${managerId}/team`;
  const officialTransfersUrl = 'https://fantasy.premierleague.com/transfers';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className="modal-content handover-modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="handover-modal-title"
        tabIndex={-1}
        style={{ outline: 'none' }}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-box emerald">
              <ShieldCheck size={20} weight="fill" />
            </div>
            <div>
              <h2 id="handover-modal-title" className="modal-title">
                Matchday Handover Checklist
              </h2>
              <p className="modal-subtitle">
                Gameweek {gw} Sign-Off &middot; Official Premier League Advisory
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

        <div className="handover-modal-body">
          {/* Manager & Team Profile Banner */}
          <div className="handover-profile-card">
            <div className="handover-profile-header">
              <span className="handover-profile-tag font-mono">
                <User size={12} weight="bold" style={{ display: 'inline', marginRight: '4px' }} />
                SQUAD IDENTITY
              </span>
              <span className="handover-profile-id font-mono">
                TEAM ID: #{managerId}
              </span>
            </div>
            <div className="handover-profile-details">
              <div>
                <span className="profile-detail-label">Manager</span>
                <span className="profile-detail-val">{managerName}</span>
              </div>
              <div>
                <span className="profile-detail-label">Team</span>
                <span className="profile-detail-val">{teamName}</span>
              </div>
              <div>
                <span className="profile-detail-label">Free Transfers In Hand</span>
                <span className="profile-detail-val font-mono">{freeTransfers} FT</span>
              </div>
            </div>
          </div>

          {/* Section 1: Transfer Checklist Reminder */}
          <div className="handover-section">
            <div className="handover-section-title font-mono">
              1. RECOMMENDED TRANSFER ON FPL SITE
            </div>
            <div className="handover-transfer-card">
              <div className="handover-transfer-row">
                <div className="handover-transfer-pill in">
                  <span className="transfer-tag font-mono">IN</span>
                  <div className="transfer-details">
                    <span className="transfer-name">Yoane Wissa</span>
                    <span className="transfer-meta font-mono">FWD &middot; &pound;6.1m &middot; 5.33 Exp Pts</span>
                  </div>
                </div>
                <CaretRight size={16} className="transfer-arrow" />
                <div className="handover-transfer-pill out">
                  <span className="transfer-tag font-mono">OUT</span>
                  <div className="transfer-details">
                    <span className="transfer-name">Jo&atilde;o Pedro</span>
                    <span className="transfer-meta font-mono">FWD &middot; Sold @ &pound;5.7m</span>
                  </div>
                </div>
              </div>
              <div className="handover-transfer-note">
                <CheckCircle size={13} weight="fill" color="var(--accent-emerald)" />
                <span>Lineup on pitch is already synchronized with Wissa in your starting XI.</span>
              </div>
            </div>
          </div>

          {/* Section 2: Captaincy & Matchday Telemetry */}
          <div className="handover-section">
            <div className="handover-section-title font-mono">
              2. CAPTAINCY &amp; FORMATION SIGN-OFF
            </div>
            <div className="handover-picks-grid">
              <div className="handover-pick-box captain">
                <div className="pick-box-header font-mono">
                  <Crown size={14} weight="fill" color="#eab308" />
                  <span>SUGGESTED CAPTAIN</span>
                </div>
                <div className="pick-box-name">{capt?.web_name || 'Gibbs-White'}</div>
                <div className="pick-box-meta font-mono">
                  {captXp} Projected Points (Double Points)
                </div>
              </div>

              <div className="handover-pick-box vice">
                <div className="pick-box-header font-mono">
                  <ShieldCheck size={14} weight="bold" color="var(--accent-cyan)" />
                  <span>VICE-CAPTAIN</span>
                </div>
                <div className="pick-box-name">{vc?.web_name || 'B.Fernandes'}</div>
                <div className="pick-box-meta font-mono">
                  {vcXp} Projected Points (Backup)
                </div>
              </div>
            </div>

            <div className="handover-formation-bar font-mono">
              <span className="handover-telemetry-item">Formation: <strong>{formationStr}</strong></span>
              <span className="handover-telemetry-dot">&middot;</span>
              <span className="handover-telemetry-item">Projected Output: <strong>{totalStartingXp} Exp Pts</strong></span>
              <span className="handover-telemetry-dot">&middot;</span>
              <span className="handover-telemetry-item">Bench Order: {bench.slice(0, 3).map(p => p.web_name).join(', ') || 'Calafiori, Calvert-Lewin, De Cuyper'}</span>
            </div>
          </div>

          {/* Section 3: Official Premier League Advisory */}
          <div className="handover-advisory-box" role="alert">
            <WarningCircle size={18} weight="fill" className="advisory-icon" />
            <div className="advisory-content">
              <strong>Official Matchday Submission Reminder</strong>
              <p>
                Dugout is an analytical decision engine. The transfers and tactical picks shown here are demonstration recommendations.
                You must execute the transfer and confirm your starting lineup and captaincy directly on the official Fantasy Premier League website before the Gameweek deadline.
              </p>
            </div>
          </div>

          {/* Section 4: Direct Links to Official FPL Site */}
          <div className="handover-fpl-links">
            <a
              href={officialTransfersUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary handover-link-btn font-mono"
            >
              <span>Make Transfer on FPL</span>
              <ArrowSquareOut size={14} weight="bold" />
            </a>

            <a
              href={officialTeamUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary handover-link-btn font-mono"
            >
              <span>Open My Team (#{managerId})</span>
              <ArrowSquareOut size={14} weight="bold" />
            </a>
          </div>

          {/* Section 5: Modal Actions */}
          <div className="handover-modal-actions">
            <button
              type="button"
              className="modal-btn-ghost"
              onClick={onClose}
            >
              Close
            </button>

            <button
              type="button"
              className="handover-confirm-btn font-mono"
              onClick={() => {
                onConfirmLock();
                onClose();
              }}
              disabled={isLocked}
            >
              <CheckCircle size={15} weight="bold" />
              <span>{isLocked ? 'Lineup Already Locked' : 'Confirm & Lock Lineup in Dugout'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
