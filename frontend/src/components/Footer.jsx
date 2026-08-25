import React from 'react';
import { GithubLogo, ArrowSquareOut } from '@phosphor-icons/react';

export default function Footer() {
  return (
    <footer className="terminal-footer-simple">
      <div className="footer-simple-inner">
        <div className="footer-copyright">
          © {new Date().getFullYear()} FPL Matchday Hub · Open Source Analytics
        </div>
        <div className="footer-links">
          <a
            href="https://github.com/Arabinda07/Fantasy-Premier-League"
            target="_blank"
            rel="noreferrer"
            className="footer-github-link"
          >
            <GithubLogo size={15} weight="fill" />
            <span>Arabinda07 / Fantasy-Premier-League</span>
            <ArrowSquareOut size={12} />
          </a>
        </div>
      </div>
    </footer>
  );
}
