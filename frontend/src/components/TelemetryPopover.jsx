import React, { useState } from 'react';
import { Popover } from '@astryxdesign/core';
import { Info } from '@phosphor-icons/react';

/**
 * Direction J Standard Telemetry Popover
 * Powered by @astryxdesign/core Popover (adaptive BottomSheet on compact touch screens,
 * anchored viewport-aware overlay on desktop, Escape/light-dismiss built in).
 */
export default function TelemetryPopover({
  title,
  children,
  triggerLabel = 'Notes',
  triggerTitle,
  triggerIcon: TriggerIcon = Info,
  triggerClassName = 'telemetry-notes-btn font-mono',
  groupClassName = 'telemetry-notes-group',
  popoverClassName = 'telemetry-popover-card font-mono'
}) {
  const [isOpen, setIsOpen] = useState(false);

  const popoverContent = (
    <div className="astryx-telemetry-popover-inner">
      {title && (
        <h3 className="telemetry-popover-title">
          {title}
        </h3>
      )}
      <div className="telemetry-popover-body">
        {children}
      </div>
    </div>
  );

  return (
    <div className={groupClassName}>
      <Popover
        isOpen={isOpen}
        onOpenChange={setIsOpen}
        placement="below"
        alignment="end"
        presentation="adaptive"
        width={320}
        padding={3}
        label={typeof title === 'string' ? title : triggerLabel}
        className={`astryx-telemetry-popover ${popoverClassName}`}
        content={popoverContent}
      >
        <button
          type="button"
          className={`${triggerClassName} ${isOpen ? 'active' : ''}`}
          title={triggerTitle || `Click to view ${triggerLabel}`}
        >
          {TriggerIcon && <TriggerIcon size={13} weight="bold" />}
          <span>{triggerLabel}</span>
        </button>
      </Popover>
    </div>
  );
}
