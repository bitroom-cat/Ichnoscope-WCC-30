'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export interface ToastProps {
  type?: 'success' | 'error' | 'info';
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  onClose?: () => void;
  className?: string;
}

export function Toast({
  type = 'info',
  title,
  message,
  action,
  onClose,
  className,
}: ToastProps) {
  const icons = {
    success: <CheckCircle2 className="w-4 h-4 text-success shrink-0" />,
    error: <AlertCircle className="w-4 h-4 text-danger shrink-0" />,
    info: <Info className="w-4 h-4 text-info shrink-0" />,
  };

  return (
    <div
      role="status"
      className={cn(
        'flex items-start gap-3 p-3.5 rounded bg-elevated border border-border-strong text-primary shadow-popover text-xs',
        className
      )}
    >
      {icons[type]}
      <div className="flex-1 space-y-0.5">
        <p className="font-semibold text-primary">{title}</p>
        {message && <p className="text-secondary leading-relaxed">{message}</p>}
        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="text-accent hover:underline font-medium pt-1 block"
          >
            {action.label}
          </button>
        )}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss toast"
          className="text-text-muted hover:text-primary transition-colors p-0.5"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
