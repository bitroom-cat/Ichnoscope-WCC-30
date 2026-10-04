'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'p-12 text-center rounded bg-surface border border-border-subtle flex flex-col items-center justify-center space-y-3 relative overflow-hidden',
        className
      )}
    >
      {/* Signature Motif: The Trace */}
      <div className="w-16 h-1 rounded-full bg-accent/40 mb-2 relative">
        <div className="absolute inset-0 bg-accent rounded-full animate-pulse" />
      </div>

      <div className="space-y-1 max-w-sm">
        <h3 className="text-sm font-semibold text-primary">{title}</h3>
        {description && <p className="text-xs text-text-secondary leading-relaxed">{description}</p>}
      </div>

      {actionLabel && onAction && (
        <div className="pt-2">
          <Button variant="secondary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
