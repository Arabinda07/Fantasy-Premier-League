import React from 'react';
import { Collapsible } from '@astryxdesign/core';

/**
 * CollapsibleSection — Standardized Progressive Disclosure Primitive
 * Powered by @astryxdesign/core Collapsible with Direction J surface styling.
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
  const triggerNode = (
    <div className="nike-collapsible-header-row">
      <div className="nike-collapsible-title-wrap">
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
  );

  return (
    <div className={`nike-collapsible-section astryx-collapsible-bridge ${className}`}>
      <Collapsible
        trigger={triggerNode}
        defaultIsOpen={defaultOpen}
        isOpen={controlledIsOpen}
        onOpenChange={onToggle}
        chevronPosition="start"
        className="astryx-collapsible-root"
      >
        <div className="nike-collapsible-inner">
          {children}
        </div>
      </Collapsible>
    </div>
  );
}

