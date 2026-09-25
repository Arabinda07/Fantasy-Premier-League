import React, { useEffect, useRef, useMemo, useState } from 'react';
import {
  X,
  ArrowSquareOut,
  ArrowsLeftRight,
  CaretRight,
  TrendUp,
  ShieldCheck,
  Calendar
} from '@phosphor-icons/react';
import { generateTransferRationale } from '../utils/transferRationaleEngine.js';
import { resolvePlayerMetadata } from '../utils/playerMetadataHelper.js';

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

  // Sanitized player metadata avoiding duplicate self-fixtures
  const outMeta = useMemo(() => resolvePlayerMetadata(playerOut), [playerOut]);
  const inMeta = useMemo(() => resolvePlayerMetadata(playerIn), [playerIn]);

  // Deterministic, context-aware rationale generation synchronized with player metadata
  const rationales = useMemo(() => {
    const syncPlayerIn = {
      ...playerIn,
      fixture: inMeta.fixtureInfo ? inMeta.fixtureInfo.display : playerIn.fixture,
      fdr: inMeta.fixtureInfo ? inMeta.fixtureInfo.fdr : playerIn.fdr
    };
    const syncPlayerOut = {
      ...playerOut,
      fixture: outMeta.fixtureInfo ? outMeta.fixtureInfo.display : playerOut.fixture,
      fdr: outMeta.fixtureInfo ? outMeta.fixtureInfo.fdr : playerOut.fdr
    };

    return generateTransferRationale({
      playerIn: syncPlayerIn,
      playerOut: syncPlayerOut,
      netGain,
      costDelta,
      bank,
      gameweek: gw,
      isRoll
    });
  }, [playerIn, playerOut, inMeta, outMeta, netGain, costDelta, bank, gw, isRoll]);

  const renderIcon = (iconType) => {
    if (iconType === 'emerald') return <Calendar size={14} weight="bold" />;
    if (iconType === 'cyan') return <TrendUp size={14} weight="bold" />;
    return <ShieldCheck size={14} weight="bold" />;
  };

  if (!isOpen) return null;

  const officialTransfersUrl = 'https://fantasy.premierleague.com/transfers';
  const officialTeamUrl = `https://fantasy.premierleague.com/entry/${managerId}/team`;

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
            <ArrowsLeftRight size={22} weight="bold" className="modal-unboxed-icon" />
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
            /* Unified Head-to-Head Transfer Card */
            <div className="unified-transfer-card">
              {/* 1. Outgoing Player (Left Box) */}
              <div className="unified-player-box out">
                <div className="unified-box-header font-mono">
                  <span className="player-col-badge out">OUT</span>
                  <span className="player-col-pos">{outMeta.position}</span>
                </div>
                <div className="unified-player-name">{outMeta.name}</div>
                <div className="unified-player-xp font-mono">
                  <span className="xp-val">{outMeta.expectedPoints}</span>
                  <span className="xp-lbl">Exp Pts</span>
                </div>
                <div className="unified-player-meta font-mono">
                  <span className="unified-player-meta-cost">{outMeta.team} &middot; &pound;{outMeta.costFormatted}m</span>
                  {outMeta.fixtureInfo && (
                    <span
                      className={`fixture-pill fdr-${outMeta.fixtureInfo.fdr}`}
                      title={`${outMeta.fixtureInfo.fullDisplay || outMeta.fixtureInfo.display} · FDR ${outMeta.fixtureInfo.fdr}`}
                    >
                      {outMeta.fixtureInfo.display}
                    </span>
                  )}
                </div>
              </div>

              {/* 2. Flow Bridge (Center) */}
              <div className="unified-transfer-bridge font-mono">
                <div className="delta-pill">
                  <span>+{netGain} pts</span>
                </div>
                <CaretRight size={14} className="delta-arrow" />
                <span className="delta-cost-note">
                  {Number(costDelta) > 0
                    ? `Costs \u00a3${costDelta}m`
                    : Number(costDelta) < 0
                    ? `Saves \u00a3${Math.abs(Number(costDelta)).toFixed(1)}m`
                    : 'Budget Neutral'}
                </span>
              </div>

              {/* 3. Incoming Player (Right Box) */}
              <div className="unified-player-box in">
                <div className="unified-box-header font-mono">
                  <span className="player-col-badge in">IN</span>
                  <span className="player-col-pos">{inMeta.position}</span>
                </div>
                <div className="unified-player-name">{inMeta.name}</div>
                <div className="unified-player-xp font-mono">
                  <span className="xp-val">{inMeta.expectedPoints}</span>
                  <span className="xp-lbl">Exp Pts</span>
                </div>
                <div className="unified-player-meta font-mono">
                  <span className="unified-player-meta-cost">{inMeta.team} &middot; &pound;{inMeta.costFormatted}m</span>
                  {inMeta.fixtureInfo && (
                    <span
                      className={`fixture-pill fdr-${inMeta.fixtureInfo.fdr}`}
                      title={`${inMeta.fixtureInfo.fullDisplay || inMeta.fixtureInfo.display} · FDR ${inMeta.fixtureInfo.fdr}`}
                    >
                      {inMeta.fixtureInfo.display}
                    </span>
                  )}
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
              aria-controls="transfer-rationale-list"
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
            <div id="transfer-rationale-list" className="rationale-list">
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

        {/* Docked Action Bar */}
        <div className="modal-action-footer">
          <button
            type="button"
            className="modal-btn-ghost font-mono"
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
