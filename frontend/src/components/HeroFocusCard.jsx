import React from 'react';
import { ArrowUpRight } from '@phosphor-icons/react';

/**
 * HeroFocusCard — Monolithic Focal Point Primitive
 * Built in alignment with Nike's design system:
 * - Enforces the "Rule of One": Exactly 1 dominant visual focal point per tab
 * - Monolithic display typography (40px/48px)
 * - Signature Nike 48px pill CTA button (9999px radius) with nested action icon
 * - Sharp color-blocked container (0px radius) with generous macro-whitespace
 */
export default function HeroFocusCard({
  eyebrow,
  heroValue,
  heroUnit,
  headline,
  description,
  metaBadge,
  primaryCtaText,
  onPrimaryCtaClick,
  primaryCtaDisabled = false,
  primaryCtaIcon: PrimaryCtaIcon = ArrowUpRight,
  secondaryAction,
  className = '',
  children
}) {
  return (
    <div className={`nike-hero-card ${className}`}>
      <div className="nike-hero-header">
        <div className="nike-hero-meta-strip">
          {eyebrow && (
            <span className="nike-hero-eyebrow font-mono">
              {eyebrow}
            </span>
          )}
          {metaBadge && (
            <div className="nike-hero-badge-wrap">
              {metaBadge}
            </div>
          )}
        </div>

        {heroValue !== undefined && heroValue !== null && (
          <div className="nike-hero-metric-row">
            <span className="nike-hero-value font-mono">
              {heroValue}
            </span>
            {heroUnit && (
              <span className="nike-hero-unit font-mono">
                {heroUnit}
              </span>
            )}
          </div>
        )}

        {headline && (
          <h2 className="nike-hero-headline">
            {headline}
          </h2>
        )}

        {description && (
          <p className="nike-hero-description">
            {description}
          </p>
        )}

        {(primaryCtaText || secondaryAction) && (
          <div className="nike-hero-cta-strip">
            {primaryCtaText && (
              <button
                type="button"
                className="nike-pill-cta"
                onClick={onPrimaryCtaClick}
                disabled={primaryCtaDisabled}
              >
                <span className="nike-pill-cta-text">{primaryCtaText}</span>
                {PrimaryCtaIcon && (
                  <span className="nike-pill-cta-icon-bubble">
                    <PrimaryCtaIcon size={16} weight="bold" />
                  </span>
                )}
              </button>
            )}

            {secondaryAction && (
              <div className="nike-hero-secondary-action">
                {secondaryAction}
              </div>
            )}
          </div>
        )}
      </div>

      {children && (
        <div className="nike-hero-content-body">
          {children}
        </div>
      )}
    </div>
  );
}

