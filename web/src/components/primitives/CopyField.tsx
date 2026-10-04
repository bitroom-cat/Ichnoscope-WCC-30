'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Copy, Check } from 'lucide-react';

export interface CopyFieldProps {
  value: string;
  label?: string;
  className?: string;
}

export function CopyField({ value, label, className }: CopyFieldProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      onClick={handleCopy}
      role="button"
      tabIndex={0}
      title="Click to copy"
      className={cn(
        'group inline-flex items-center justify-between gap-2 px-2.5 py-1 rounded bg-inset border border-border-subtle hover:border-border-strong text-xs font-mono transition-colors duration-fast cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring',
        className
      )}
    >
      <span className="truncate text-primary select-all">{label || value}</span>
      <span className="shrink-0 text-text-muted group-hover:text-primary transition-colors">
        {copied ? (
          <span className="inline-flex items-center gap-1 text-caption text-success font-sans">
            <Check className="w-3.5 h-3.5" />
            <span>Copied</span>
          </span>
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </span>
    </div>
  );
}
