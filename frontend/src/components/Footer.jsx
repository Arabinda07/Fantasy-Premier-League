import React from 'react';
import { GithubLogo } from '@phosphor-icons/react';

export default function Footer({ onNavigateTab }) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="terminal-footer-simple">
      <div className="footer-simple-inner">
        <div className="footer-brand-meta">
          <span className="footer-copyright">© {currentYear} FPL Dugout</span>
          <span className="footer-divider">·</span>
          <span className="footer-tagline">Smart Squad & Matchday Planner</span>
        </div>

        {onNavigateTab && (
          <nav className="footer-nav" aria-label="Footer Quick Navigation">
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab('pitch')}
            >
              My Lineup
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab('transfers')}
            >
              Transfer Planner
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab('rivals')}
            >
              Mini-Leagues
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab('fixtures')}
            >
              Fixture Ticker
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab('vault')}
            >
              Historical Archive
            </button>
          </nav>
        )}

        <div className="footer-meta-actions">
          <span className="footer-attribution">Data: Official FPL API & OKF v0.2</span>
          <a
            href="https://github.com/Arabinda07/Fantasy-Premier-League"
            target="_blank"
            rel="noreferrer"
            className="footer-github-icon-link"
            aria-label="GitHub Repository (Arabinda07/Fantasy-Premier-League)"
            title="GitHub Repository"
          >
            <GithubLogo size={18} weight="fill" />
          </a>
        </div>
      </div>
    </footer>
  );
}


