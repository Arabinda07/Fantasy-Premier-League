import React, { useState, useId } from 'react';
import { CaretDown } from '@phosphor-icons/react';

/**
 * CollapsibleSection — Standardized Progressive Disclosure Primitive
 * Built in alignment with Nike's design system:
 * - Sharp container geometry (0px border radius)
 * - Color-blocked surface (#181818) with 1px hairline border
 * - Accessible keyboard and screen-reader controls (aria-expanded, aria-controls)
 * - Smooth transition state with zero layout jitter
 */
export default function CollapsibleSection({
  title,
  subtitle,
  badge,
  badgeVariant = 'neutral',
  defaultOpen = false,
  isOpen: controlledIsOpen,
  onToggle,
  headerAction,
  className = '',
  children
}) {
  const [internalIsOpen, setInternalIsOpen] = useState(defaultOpen);
  const isControlled = controlledIsOpen !== undefined;
  const isOpen = isControlled ? controlledIsOpen : internalIsOpen;

  const contentId = useId();
  const headerId = useId();

  const handleToggle = () => {
    if (onToggle) {
      onToggle(!isOpen);
    }
    if (!isControlled) {
      setInternalIsOpen(!isOpen);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <div className={`nike-collapsible-section ${isOpen ? 'is-open' : 'is-collapsed'} ${className}`}>
      <div
        id={headerId}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-controls={contentId}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className="nike-collapsible-header"
      >
        <div className="nike-collapsible-title-wrap">
          <span className="nike-collapsible-chevron-wrap">
            <CaretDown
              size={14}
              weight="bold"
              className={`nike-collapsible-chevron ${isOpen ? 'rotate-180' : ''}`}
            />
          </span>
          <span className="nike-collapsible-title">{title}</span>
          {badge && (
            <span className={`nike-collapsible-badge badge-${badgeVariant} font-mono`}>
              {badge}
            </span>
          )}
          {subtitle && (
            <span className="nike-collapsible-subtitle">{subtitle}</span>
          )}
        </div>

        {headerAction && (
          <div
            className="nike-collapsible-action-wrap"
            onClick={(e) => e.stopPropagation()}
          >
            {headerAction}
          </div>
        )}
      </div>

      <div
        id={contentId}
        role="region"
        aria-labelledby={headerId}
        className={`nike-collapsible-content ${isOpen ? 'open' : 'closed'}`}
      >
        <div className="nike-collapsible-inner">
          {children}
        </div>
      </div>
    </div>
  );
}

