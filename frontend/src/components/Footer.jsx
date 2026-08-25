import React from 'react';
import {
  SoccerBall,
  GithubLogo,
  BookOpen,
  ArrowSquareOut
} from '@phosphor-icons/react';

export default function Footer({ onNavigateTab, liveData }) {
  return (
    <footer className="terminal-footer">
      <div className="footer-content">
        <div className="footer-grid">
          {/* Col 1: Brand & Purpose */}
          <div className="footer-col brand-col">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <div style={{ background: 'var(--accent-emerald)', color: '#090D16', padding: '3px 5px', borderRadius: 'var(--radius-xs)', display: 'flex', alignItems: 'center' }}>
                <SoccerBall size={15} weight="fill" />
              </div>
              <span style={{ fontWeight: 800, fontSize: '15px', color: 'var(--text-primary)' }}>
                FPL Matchday Hub
              </span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '280px' }}>
              Data-driven Fantasy Premier League decision support terminal. Built with multi-gameweek transfer planning and empirical expected point decomposition.
            </p>
            <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Data synced for Gameweek {liveData?.gameweek || 2} · {liveData?.season || '2026-27'}
            </div>
          </div>

          {/* Col 2: Navigation Hub */}
          <div className="footer-col">
            <div className="footer-col-title">Terminal Views</div>
            <ul className="footer-links-list">
              <li>
                <button onClick={() => onNavigateTab('pitch')} className="footer-link-btn">
                  Matchday XI & Lineup
                </button>
              </li>
              <li>
                <button onClick={() => onNavigateTab('transfers')} className="footer-link-btn">
                  Transfer Planner (3-GW)
                </button>
              </li>
              <li>
                <button onClick={() => onNavigateTab('fixtures')} className="footer-link-btn">
                  Fixture Difficulty Ticker
                </button>
              </li>
              <li>
                <button onClick={() => onNavigateTab('market')} className="footer-link-btn">
                  Price Change Alerts
                </button>
              </li>
              <li>
                <button onClick={() => onNavigateTab('math')} className="footer-link-btn">
                  Points Breakdown Studio
                </button>
              </li>
            </ul>
          </div>

          {/* Col 3: Methodology & Reference */}
          <div className="footer-col">
            <div className="footer-col-title">Methodology & Data</div>
            <ul className="footer-links-list">
              <li style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} color="var(--accent-emerald)" />
                <span>11-Component Point Decomposition</span>
              </li>
              <li style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} color="var(--accent-cyan)" />
                <span>Empirical Bayes Prior Shrinkage</span>
              </li>
              <li style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} color="var(--accent-amber)" />
                <span>Mixed-Integer Linear Programming (MILP)</span>
              </li>
              <li style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                <span>Historical Data back to 2016-17</span>
              </li>
            </ul>
          </div>

          {/* Col 4: Repository & Legal */}
          <div className="footer-col">
            <div className="footer-col-title">Open Source</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <a
                href="https://github.com/vaastav/Fantasy-Premier-League"
                target="_blank"
                rel="noreferrer"
                className="footer-github-link"
              >
                <GithubLogo size={16} weight="fill" />
                <span>GitHub Repository</span>
                <ArrowSquareOut size={12} />
              </a>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Fantasy Premier League is a registered trademark of the Football Association Premier League Ltd. This is an open-source analytics toolkit.
              </p>
            </div>
          </div>
        </div>

        <div className="footer-bottom-bar">
          <div>© {new Date().getFullYear()} FPL Matchday Hub · Open Source Analytics</div>
          <div style={{ fontFamily: 'var(--font-mono)' }}>Fast · Deterministic · Zero Telemetry</div>
        </div>
      </div>
    </footer>
  );
}
