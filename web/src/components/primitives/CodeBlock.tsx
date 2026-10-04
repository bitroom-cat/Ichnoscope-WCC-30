'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Copy, Check } from 'lucide-react';
import { IconButton } from './Button';

export interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  highlightLine?: number;
  className?: string;
}

export function CodeBlock({
  code,
  language,
  filename,
  highlightLine,
  className,
}: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lines = code.trim().split('\n');

  return (
    <div className={cn('rounded border border-border-subtle bg-inset overflow-hidden text-xs font-mono', className)}>
      {(filename || language) && (
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border-subtle bg-surface/50 text-text-muted">
          <span className="truncate">{filename || language}</span>
          <IconButton label="Copy code" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
          </IconButton>
        </div>
      )}

      <div className="overflow-x-auto p-3">
        <table className="border-collapse w-full">
          <tbody>
            {lines.map((line, idx) => {
              const lineNo = idx + 1;
              const isHighlight = highlightLine === lineNo;
              return (
                <tr
                  key={idx}
                  className={cn(
                    'hover:bg-hover/40 transition-colors',
                    isHighlight && 'bg-accent/15 border-l-2 border-accent font-semibold text-primary'
                  )}
                >
                  <td className="pr-4 text-right text-text-muted select-none w-8 text-caption tabular-nums">
                    {lineNo}
                  </td>
                  <td className="whitespace-pre text-primary">{line}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
