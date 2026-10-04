'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Search, Copy, Check, Download, ArrowDown } from 'lucide-react';
import { IconButton } from './Button';

export interface LogEntry {
  ts: string;
  level: 'info' | 'warn' | 'error';
  step: string;
  message: string;
}

export interface LogViewerProps {
  logs: LogEntry[];
  className?: string;
}

export function LogViewer({ logs, className }: LogViewerProps) {
  const [search, setSearch] = React.useState('');
  const [levelFilter, setLevelFilter] = React.useState<string>('all');
  const [followTail, setFollowTail] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (followTail && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, followTail]);

  const filteredLogs = logs.filter((log) => {
    if (levelFilter !== 'all' && log.level !== levelFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        log.message.toLowerCase().includes(q) ||
        log.step.toLowerCase().includes(q) ||
        log.ts.includes(q)
      );
    }
    return true;
  });

  const handleCopy = () => {
    const text = logs
      .map((l) => `[${l.ts}] [${l.step.toUpperCase()}] [${l.level.toUpperCase()}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleDownload = () => {
    const text = logs
      .map((l) => `[${l.ts}] [${l.step.toUpperCase()}] [${l.level.toUpperCase()}] ${l.message}`)
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ichnoscope-pipeline-${Date.now()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={cn('rounded border border-border-subtle bg-inset overflow-hidden flex flex-col', className)}>
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-3.5 py-2 border-b border-border-subtle bg-surface text-xs">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-7 pl-8 pr-2.5 rounded-sm bg-inset border border-border-subtle text-primary text-caption font-mono placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-focus-ring"
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="h-7 px-2 rounded-sm bg-inset border border-border-subtle text-primary text-caption font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-focus-ring"
          >
            <option value="all">All levels</option>
            <option value="info">Info only</option>
            <option value="warn">Warnings</option>
            <option value="error">Errors</option>
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setFollowTail(!followTail)}
            className={cn(
              'inline-flex items-center gap-1 px-2 py-1 rounded-sm text-caption font-mono border transition-colors',
              followTail
                ? 'bg-accent/15 text-accent border-accent font-semibold'
                : 'bg-surface text-text-muted border-border-subtle hover:text-primary hover:border-border-strong'
            )}
          >
            <ArrowDown className="w-3 h-3" />
            <span>Follow tail</span>
          </button>

          <IconButton label="Copy all logs" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
          </IconButton>

          <IconButton label="Download log file" size="sm" onClick={handleDownload}>
            <Download className="w-3.5 h-3.5" />
          </IconButton>
        </div>
      </div>

      {/* Terminal View */}
      <div
        ref={scrollRef}
        className="p-3 font-mono text-caption leading-relaxed space-y-1 max-h-[380px] overflow-y-auto select-text"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-text-muted text-center py-8">No log entries matching filter.</div>
        ) : (
          filteredLogs.map((log, idx) => (
            <div
              key={idx}
              className="flex items-baseline gap-2.5 hover:bg-hover/50 px-1 py-0.5 rounded transition-colors"
            >
              <span className="text-text-muted text-caption shrink-0 tabular-nums">{log.ts}</span>
              <span className="text-text-muted text-caption uppercase px-1 rounded bg-surface border border-border-subtle shrink-0">
                {log.step}
              </span>
              <span
                className={cn(
                  'flex-1 break-words',
                  log.level === 'info' && 'text-text-secondary',
                  log.level === 'warn' && 'text-warning font-medium',
                  log.level === 'error' && 'text-danger font-semibold'
                )}
              >
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
