'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  count?: number;
  variant?: 'default' | 'draft';
}

export function Chip({
  className,
  active = false,
  count,
  variant = 'default',
  children,
  ...props
}: ChipProps) {
  return (
    <button
      type="button"
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition-colors duration-fast select-none cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1 focus-visible:ring-offset-canvas',
        active
          ? variant === 'draft'
            ? 'bg-draft-subtle text-draft border border-draft font-semibold'
            : 'bg-accent/15 text-accent border border-accent font-semibold'
          : 'bg-surface text-secondary border border-border-subtle hover:bg-hover hover:text-primary hover:border-border-strong',
        className
      )}
      {...props}
    >
      <span>{children}</span>
      {count !== undefined && (
        <span
          className={cn(
            'px-1 py-0.2 rounded text-caption font-mono tabular-nums',
            active
              ? variant === 'draft'
                ? 'bg-draft/20 text-draft'
                : 'bg-accent/25 text-accent'
              : 'bg-hover text-text-muted'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}
