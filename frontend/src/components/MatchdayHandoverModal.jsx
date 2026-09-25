import React, { useEffect, useRef, useMemo } from 'react';
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
import { resolvePlayerMetadata } from '../utils/playerMetadataHelper.js';

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
  isLocked = false,
  recommendedTransfer
}) {
  const modalRef = useRef(null);

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

  const gw = liveData?.gameweek || 6;
  const isRoll = Boolean(recommendedTransfer?.isRollFt);

  // Fallback defaults if none provided
  const playerIn = recommendedTransfer?.playerIn || {
    name: 'Yoane Wissa',
    team: 'Newcastle',
    cost: 6.2,
    expected_points: 3.58,
    position: 'FWD'
  };

  const playerOut = recommendedTransfer?.playerOut || {
    name: 'Jo\u00e3o Pedro',
    team: 'Chelsea',
    cost: 7.8,
    expected_points: 2.95,
    position: 'FWD'
  };

  const netGain = recommendedTransfer?.netGain != null
    ? Number(recommendedTransfer.netGain).toFixed(2)
    : (Number(playerIn.expected_points || 0) - Number(playerOut.expected_points || 0)).toFixed(2);
  const costDelta = recommendedTransfer?.costDelta != null
    ? Number(recommendedTransfer.costDelta).toFixed(1)
    : (Number(playerIn.cost || 0) - Number(playerOut.cost || 0)).toFixed(1);

  // Sanitized player metadata avoiding duplicate self-fixtures
  const outMeta = useMemo(() => resolvePlayerMetadata(playerOut), [playerOut]);
  const inMeta = useMemo(() => resolvePlayerMetadata(playerIn), [playerIn]);

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

  const officialTeamUrl = `https://fantasy.premierleague.com/entry/${managerId}/team`;

  if (!isOpen) return null;

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
            <ShieldCheck size={22} weight="fill" className="modal-unboxed-icon" />
            <div>
              <h2 id="handover-modal-title" className="modal-title">
                Matchday Checklist
              </h2>
              <p className="modal-subtitle font-mono">
                Gameweek {gw} &middot; {freeTransfers} Free Transfer{freeTransfers > 1 ? 's' : ''} Available
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
          {/* Pre-Flight Checklist Panel */}
          <div className="handover-checklist-card">
            {/* 1. Transfer Step */}
            <div className="handover-check-group">
              <div className="handover-check-header font-mono">
                <span className="step-num">1</span>
                <span>{isRoll ? 'STRATEGY: ROLL FREE TRANSFER' : 'RECOMMENDED TRANSFER'}</span>
              </div>
              {isRoll ? (
                <div className="handover-transfer-row">
                  <div className="handover-player-chip roll font-mono">
                    <CheckCircle size={15} weight="fill" color="var(--accent-emerald)" />
                    <div className="player-chip-info">
                      <span className="player-chip-name">Save Free Transfer (Roll FT)</span>
                      <span className="player-chip-meta font-mono">Bank 1 FT &middot; Carry forward to Gameweek {gw + 1}</span>
                    </div>
                  </div>
                </div>
              ) : (
                /* Unified Head-to-Head Transfer Card */
                <div className="unified-transfer-card">
                  {/* OUT Player */}
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

                  {/* Flow Bridge */}
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

                  {/* IN Player */}
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
            </div>

            {/* 2. Captaincy & Armband */}
            <div className="handover-check-group">
              <div className="handover-check-header font-mono">
                <span className="step-num">2</span>
                <span>ARMBAND &amp; TACTICAL PICKS</span>
              </div>
              <div className="handover-picks-grid">
                <div className="handover-pick-card captain">
                  <div className="pick-card-header font-mono">
                    <Crown size={14} weight="fill" color="var(--text-muted)" />
                    <span>CAPTAIN</span>
                  </div>
                  <div className="pick-card-name">{capt?.web_name || 'Gibbs-White'}</div>
                  <div className="pick-card-meta font-mono">
                    {captXp} Projected Pts (2x)
                  </div>
                </div>

                <div className="handover-pick-card vice">
                  <div className="pick-card-header font-mono">
                    <ShieldCheck size={14} weight="bold" color="var(--text-muted)" />
                    <span>VICE-CAPTAIN</span>
                  </div>
                  <div className="pick-card-name">{vc?.web_name || 'B.Fernandes'}</div>
                  <div className="pick-card-meta font-mono">
                    {vcXp} Projected Pts (Backup)
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Combined Telemetry & Deadline Strip */}
          <div className="handover-footer-strip font-mono">
            <div className="handover-telemetry-strip font-mono">
              <div className="telemetry-pill">
                <span className="telemetry-lbl">Formation</span>
                <span className="telemetry-val">{formationStr}</span>
              </div>
              <div className="telemetry-pill">
                <span className="telemetry-lbl">Expected Output</span>
                <span className="telemetry-val">{totalStartingXp} Exp Pts</span>
              </div>
              <div className="telemetry-pill bench">
                <span className="telemetry-lbl">Bench Order</span>
                <span className="telemetry-val">{bench.slice(0, 3).map(p => p.web_name).join(', ') || 'Calafiori, Calvert-Lewin'}</span>
              </div>
            </div>
            <div className="handover-deadline-banner font-mono">
              <div className="deadline-banner-text">
                <WarningCircle size={13} weight="fill" className="deadline-icon" />
                <span>Finalize transfers on the official FPL site before the Gameweek deadline.</span>
              </div>
              <a
                href={officialTeamUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="deadline-fpl-link font-mono"
              >
                <span>Open FPL</span>
                <ArrowSquareOut size={12} weight="bold" />
              </a>
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

          <button
            type="button"
            className="modal-btn-primary font-mono"
            onClick={() => {
              onConfirmLock();
              onClose();
            }}
            disabled={isLocked}
          >
            <CheckCircle size={15} weight="bold" />
            <span>{isLocked ? 'Lineup Locked' : 'Confirm & Lock Lineup'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
