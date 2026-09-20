import React, { useEffect, useRef, useMemo, useState } from 'react';
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
import { generateTransferRationale } from '../utils/transferRationaleEngine.js';

export default function TransferBreakdownModal({
  isOpen,
  onClose,
  managerId = '9500404',
  gameweek = 6,
  recommendedTransfer,
  bank = 0.4
}) {
  const modalRef = useRef(null);
  const [rationaleExpanded, setRationaleExpanded] = useState(false);

  // Keyboard accessibility: Focus placement, Escape key to dismiss & focus trap (WCAG 2.1.2 & 2.4.3)
  useEffect(() => {
    if (!isOpen) return;

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

  const gw = gameweek || 6;
  const isRoll = Boolean(recommendedTransfer?.isRollFt);

  // Default fallback data for initial demonstration if none provided
  const defaultPlayerOut = {
    name: 'Jo\u00e3o Pedro',
    team: 'Brighton',
    position: 'FWD',
    expected_points: 3.85,
    cost: 5.7,
    fixture: '@ Chelsea',
    fdr: 4
  };

  const defaultPlayerIn = {
    name: 'Yoane Wissa',
    team: 'Brentford',
    position: 'FWD',
    expected_points: 5.33,
    cost: 6.1,
    fixture: '@ Coventry',
    fdr: 2
  };

  const playerOut = recommendedTransfer?.playerOut || defaultPlayerOut;
  const playerIn = recommendedTransfer?.playerIn || defaultPlayerIn;
  const netGain = recommendedTransfer?.netGain != null
    ? Number(recommendedTransfer.netGain).toFixed(2)
    : (Number(playerIn.expected_points || 0) - Number(playerOut.expected_points || 0)).toFixed(2);
  const costDelta = recommendedTransfer?.costDelta != null
    ? Number(recommendedTransfer.costDelta).toFixed(1)
    : (Number(playerIn.cost || 0) - Number(playerOut.cost || 0)).toFixed(1);

  // Deterministic, context-aware rationale generation
  const rationales = useMemo(() => {
    return generateTransferRationale({
      playerIn,
      playerOut,
      netGain,
      costDelta,
      bank,
      gameweek: gw,
      isRoll
    });
  }, [playerIn, playerOut, netGain, costDelta, bank, gw, isRoll]);

  const renderIcon = (iconType) => {
    if (iconType === 'emerald') return <Calendar size={14} weight="bold" />;
    if (iconType === 'cyan') return <TrendUp size={14} weight="bold" />;
    return <ShieldCheck size={14} weight="bold" />;
  };

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
        tabIndex={-1}
        style={{ outline: 'none' }}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-box blue">
              <ArrowsLeftRight size={20} weight="bold" />
            </div>
            <div>
              <h2 id="breakdown-modal-title" className="modal-title">
                Transfer Recommendation
              </h2>
              <p className="modal-subtitle font-mono">
                {isRoll
                  ? `Gameweek ${gw} \u00b7 Bank Free Transfer`
                  : `Gameweek ${gw} \u00b7 +${netGain} Projected Points Gain`}
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
          {isRoll ? (
            /* Roll Free Transfer Spec Card */
            <div className="breakdown-comparison-card roll font-mono">
              <div className="roll-status-box">
                <span className="player-col-badge in font-mono">RECOMMENDED STRATEGY</span>
                <div className="roll-title">Save Free Transfer (Roll FT)</div>
                <div className="roll-desc">
                  No immediate transfers required this gameweek. Field your active starting XI.
                </div>
              </div>
            </div>
          ) : (
            /* Head-to-Head Comparison Card */
            <div className="breakdown-comparison-card">
              {/* Delta Banner — full-width top on mobile */}
              <div className="breakdown-delta-col font-mono">
                <div className="delta-pill">
                  <Sparkle size={13} weight="fill" />
                  <span>+{netGain} pts</span>
                </div>
                <CaretRight size={18} className="delta-arrow" />
                <span className="delta-cost-note">
                  {Number(costDelta) > 0
                    ? `Costs \u00a3${costDelta}m`
                    : Number(costDelta) < 0
                    ? `Saves \u00a3${Math.abs(Number(costDelta)).toFixed(1)}m`
                    : 'Budget Neutral'}
                </span>
              </div>

              {/* Outgoing Player */}
              <div className="breakdown-player-col out">
                <div className="breakdown-col-header">
                  <span className="player-col-badge out font-mono">OUT</span>
                </div>
                <div className="player-col-name">{playerOut.name}</div>
                <div className="player-col-metric">
                  <span className="metric-val font-mono">{Number(playerOut.expected_points || 0).toFixed(2)}</span>
                  <span className="metric-lbl font-mono">Exp Pts</span>
                </div>
                <div className="player-col-compact-meta font-mono">
                  {playerOut.team} &middot; &pound;{Number(playerOut.cost || 0).toFixed(1)}m &middot; {playerOut.fixture || 'TBD'}
                </div>
              </div>

              {/* Incoming Player */}
              <div className="breakdown-player-col in">
                <div className="breakdown-col-header">
                  <span className="player-col-badge in font-mono">IN</span>
                </div>
                <div className="player-col-name">{playerIn.name}</div>
                <div className="player-col-metric">
                  <span className="metric-val font-mono">{Number(playerIn.expected_points || 0).toFixed(2)}</span>
                  <span className="metric-lbl font-mono">Exp Pts</span>
                </div>
                <div className="player-col-compact-meta font-mono">
                  {playerIn.team} &middot; &pound;{Number(playerIn.cost || 0).toFixed(1)}m &middot; {playerIn.fixture || 'TBD'}
                </div>
              </div>
            </div>
          )}

          {/* Unified Rationale Spec Card — collapsible on mobile */}
          <div className={`breakdown-rationale-card ${rationaleExpanded ? 'rationale-expanded' : ''}`}>
            <button
              type="button"
              className="rationale-card-toggle"
              onClick={() => setRationaleExpanded(!rationaleExpanded)}
              aria-expanded={rationaleExpanded}
            >
              <span className="rationale-card-title font-mono">
                WHY THIS MOVE WORKS
              </span>
              <CaretRight
                size={12}
                weight="bold"
                className={`rationale-caret ${rationaleExpanded ? 'expanded' : ''}`}
              />
            </button>
            <div className="rationale-list">
              {rationales.map((item) => (
                <div key={item.id} className="rationale-item">
                  <div className={`rationale-icon ${item.iconType}`}>
                    {renderIcon(item.iconType)}
                  </div>
                  <div className="rationale-content">
                    <strong>{item.title}:</strong>{' '}
                    <span className="rationale-text">{item.text}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Actions Docked at Bottom */}
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
            <span>Make Transfer on Official FPL</span>
            <ArrowSquareOut size={14} weight="bold" />
          </a>
        </div>
      </div>
    </div>
  );
}
