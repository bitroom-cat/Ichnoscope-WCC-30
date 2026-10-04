'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';
import { IconButton } from './Button';

export interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
}: DialogProps) {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs"
      onClick={() => onOpenChange(false)}
    >
      <div
        className={cn(
          'w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-lg bg-surface border border-border-strong p-5 sm:p-6 shadow-popover space-y-4 text-primary relative',
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-border-subtle pb-3">
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-primary">{title}</h2>
            {description && <p className="text-xs text-text-secondary">{description}</p>}
          </div>
          <IconButton
            label="Close dialog"
            size="sm"
            onClick={() => onOpenChange(false)}
          >
            <X className="w-4 h-4" />
          </IconButton>
        </div>

        <div className="text-xs text-secondary leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
