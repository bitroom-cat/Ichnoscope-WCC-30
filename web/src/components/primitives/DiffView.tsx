'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { GitCommit, Copy, Check } from 'lucide-react';
import { IconButton } from './Button';

export interface DiffViewProps {
  diff: string;
  sha?: string;
  message?: string;
  filename?: string;
  className?: string;
}

export function DiffView({ diff, sha, message, filename, className }: DiffViewProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lines = diff.trim().split('\n');

  return (
    <div className={cn('rounded border border-border-subtle bg-inset overflow-hidden text-xs font-mono', className)}>
      {(sha || message || filename) && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-border-subtle bg-surface/50 text-text-secondary">
          <div className="flex items-center gap-2 truncate">
            <GitCommit className="w-3.5 h-3.5 text-accent shrink-0" />
            {sha && <span className="font-semibold text-accent">{sha.slice(0, 7)}</span>}
            {filename && <span className="font-semibold text-text-primary">{filename}</span>}
            {message && <span className="truncate text-text-muted">{message}</span>}
          </div>
          <IconButton label="Copy git diff" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
          </IconButton>
        </div>
      )}

      <div className="overflow-x-auto p-2">
        <table className="border-collapse w-full">
          <tbody>
            {lines.map((line, idx) => {
              const isAdd = line.startsWith('+');
              const isDel = line.startsWith('-');
              const isHunk = line.startsWith('@');

              return (
                <tr
                  key={idx}
                  className={cn(
                    'select-text',
                    isAdd && 'bg-diff-add text-success',
                    isDel && 'bg-diff-del text-danger',
                    isHunk && 'bg-accent-subtle text-accent font-semibold'
                  )}
                >
                  <td className="w-6 px-2 text-right select-none text-text-muted text-caption tabular-nums border-r border-border-subtle/50">
                    {idx + 1}
                  </td>
                  <td className="px-3 py-0.5 whitespace-pre font-mono">{line}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
