import React from 'react';
import { GithubLogo } from '@phosphor-icons/react';

export default function Footer() {
  return (
    <footer className="terminal-footer-simple">
      <div className="footer-simple-inner">
        <div className="footer-copyright">
          © {new Date().getFullYear()} FPL Dugout
        </div>
        <div className="footer-links">
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

