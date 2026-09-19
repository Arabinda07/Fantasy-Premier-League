import React, { useEffect, useRef } from 'react';
import {
  X,
  ArrowSquareOut,
  ArrowsLeftRight,
  CaretRight,
  TrendUp,
  ShieldCheck,
  Calendar,
  Sparkle
} from '@phosphor-icons/react';

export default function TransferBreakdownModal({
  isOpen,
  onClose,
  managerId = '9500404'
}) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

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
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const officialTransfersUrl = 'https://fantasy.premierleague.com/transfers';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className="modal-content transfer-breakdown-modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="breakdown-modal-title"
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-box" style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'var(--accent-blue)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <ArrowsLeftRight size={20} weight="bold" />
            </div>
            <div>
              <h2 id="breakdown-modal-title" className="modal-title">
                Transfer Recommendation Breakdown
              </h2>
              <p className="modal-subtitle">
                Mathematical Rationale &middot; Gameweek 6
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

        <div className="breakdown-modal-body">
          {/* Head-to-Head Comparison Card */}
          <div className="breakdown-comparison-grid">
            {/* Outgoing Player */}
            <div className="breakdown-player-col out">
              <div className="player-col-badge font-mono">
                <span>TARGET OUT</span>
              </div>
              <div className="player-col-name">Jo&atilde;o Pedro</div>
              <div className="player-col-team font-mono">Brighton &middot; FWD</div>
              <div className="player-col-metric">
                <span className="metric-val font-mono">3.85</span>
                <span className="metric-lbl font-mono">Exp Pts (GW6)</span>
              </div>
              <div className="player-col-submetrics font-mono">
                <div>Selling Price: &pound;5.7m</div>
                <div>Fixture: @ Chelsea</div>
                <div>Profit Retained: &pound;0.1m</div>
              </div>
            </div>

            {/* Delta Column */}
            <div className="breakdown-delta-col font-mono">
              <div className="delta-pill">
                <Sparkle size={13} weight="fill" color="var(--accent-emerald)" />
                <span>+1.48 Exp Pts</span>
              </div>
              <CaretRight size={20} className="delta-arrow" />
              <div className="delta-cost-note">
                Budget Impact: &pound;0.4m
              </div>
            </div>

            {/* Incoming Player */}
            <div className="breakdown-player-col in">
              <div className="player-col-badge font-mono">
                <span>TARGET IN</span>
              </div>
              <div className="player-col-name">Yoane Wissa</div>
              <div className="player-col-team font-mono">Brentford &middot; FWD</div>
              <div className="player-col-metric">
                <span className="metric-val font-mono">5.33</span>
                <span className="metric-lbl font-mono">Exp Pts (GW6)</span>
              </div>
              <div className="player-col-submetrics font-mono">
                <div>Cost: &pound;6.1m</div>
                <div>Fixture: @ Coventry City</div>
                <div>Trend: &plusmn;0.0m (Stable)</div>
              </div>
            </div>
          </div>

          {/* 3 Pillars of Rationale */}
          <div className="breakdown-pillars-grid">
            <div className="breakdown-pillar-card">
              <div className="pillar-header font-mono">
                <Calendar size={14} weight="bold" color="var(--accent-emerald)" />
                <span>FIXTURE RUN</span>
              </div>
              <p className="pillar-text">
                Wissa faces newly-promoted Coventry City and Wolves in back-to-back gameweeks, with high transition vulnerability.
              </p>
            </div>

            <div className="breakdown-pillar-card">
              <div className="pillar-header font-mono">
                <TrendUp size={14} weight="bold" color="var(--accent-cyan)" />
                <span>50% PROFIT RETENTION</span>
              </div>
              <p className="pillar-text">
                Purchased Pedro at &pound;5.5m and selling at &pound;5.7m locks in &pound;0.1m profit before difficult Chelsea match.
              </p>
            </div>

            <div className="breakdown-pillar-card">
              <div className="pillar-header font-mono">
                <ShieldCheck size={14} weight="bold" color="var(--accent-blue)" />
                <span>TACTICAL FIT</span>
              </div>
              <p className="pillar-text">
                Brentford attack creates high expected goals on the break; Wissa starts in central striker role with zero cameo hazard.
              </p>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="breakdown-modal-actions">
            <button
              type="button"
              className="modal-btn-ghost"
              onClick={onClose}
            >
              Close
            </button>

            <a
              href={officialTransfersUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="modal-btn-primary font-mono"
            >
              <span>Execute Transfer on Official FPL</span>
              <ArrowSquareOut size={14} weight="bold" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
