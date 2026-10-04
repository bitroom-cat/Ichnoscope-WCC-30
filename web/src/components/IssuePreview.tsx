'use client';

import React, { useState } from 'react';
import { RunItem } from '@/lib/api';
import { SeverityBadge, DomainBadge, ConfidenceBadge } from '@/components/primitives/Badge';
import { DiffView } from '@/components/primitives/DiffView';
import {
  Copy,
  Check,
  GitPullRequest,
  FileCode,
  CheckSquare,
  ExternalLink,
} from 'lucide-react';

export function IssuePreview({ run }: { run: RunItem }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'rendered' | 'markdown'>('rendered');
  const [checkedSteps, setCheckedSteps] = useState<Record<number, boolean>>({});

  const toggleCheck = (idx: number) => {
    setCheckedSteps((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const rawMarkdown = `## [Auto-triage] ${run.incident.exception_type}: ${run.incident.error_message}

**Severity:** ${run.severity}  **Domain:** \`${run.explanation.domain}\`  **Confidence:** ${run.culprit.confidence}
**Failing line:** \`${run.incident.file_path}:${run.incident.line_number}\`
**Suspect:** @${run.culprit.author_login} via ${run.culprit.sha} (PR-${run.culprit.pr_number || 'N/A'})
**Last changed:** ${run.culprit.within_window ? 'recent change (likely regression)' : 'old code (likely triggered by new data)'}

### Why it probably failed
${run.explanation.root_cause_hypothesis}

### Suspect change
\`\`\`diff
${run.culprit.diff}
\`\`\`

### Verification checklist
${run.explanation.checklist.map((step: string) => `- [ ] ${step}`).join('\n')}

<!-- ichnoscope:fp=${run.fingerprint} -->`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(rawMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-border-subtle bg-surface overflow-hidden shadow-xs transition-colors">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle bg-canvas/60 px-4 sm:px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="text-dense font-semibold text-primary">
            GitHub Issue Draft
          </span>
          <span className="text-text-muted">•</span>
          <span className="text-caption font-mono text-text-muted">
            fp:{run.fingerprint}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-md bg-canvas border border-border-subtle p-0.5 text-caption font-medium">
            <button
              onClick={() => setActiveTab('rendered')}
              className={`px-3 py-1 rounded-sm transition-colors ${
                activeTab === 'rendered'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Preview
            </button>
            <button
              onClick={() => setActiveTab('markdown')}
              className={`px-3 py-1 rounded-sm transition-colors ${
                activeTab === 'markdown'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Markdown
            </button>
          </div>

          <button
            onClick={copyToClipboard}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-surface text-secondary hover:text-primary border border-border-subtle text-caption font-medium transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {run.issue_url && (
            <a
              href={run.issue_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-accent-subtle text-accent hover:bg-accent/20 border border-accent/30 text-caption font-medium transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open on GitHub
            </a>
          )}
        </div>
      </div>

      {/* Body Area */}
      {activeTab === 'rendered' ? (
        <div className="p-5 sm:p-6 space-y-6">
          {/* Issue Header */}
          <div className="space-y-1.5 border-b border-border-subtle pb-4">
            <div className="flex items-center gap-2 text-caption text-text-muted">
              <span className="px-2 py-0.5 rounded-sm font-medium font-mono bg-accent-subtle text-accent border border-accent/30">
                Auto-triage
              </span>
              <span>Drafted by Ichnoscope from Sentry telemetry</span>
            </div>
            <h2 className="text-title-3 font-semibold text-primary tracking-tight flex items-baseline gap-2">
              <span className="font-mono text-danger">
                {run.incident.exception_type}:
              </span>
              <span>{run.incident.error_message}</span>
            </h2>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-3.5 rounded-lg bg-canvas border border-border-subtle text-caption">
            <div>
              <span className="text-text-muted block mb-1">Severity & Domain</span>
              <div className="flex items-center gap-1.5">
                <SeverityBadge severity={run.severity} />
                <DomainBadge domain={run.explanation.domain} />
              </div>
            </div>

            <div>
              <span className="text-text-muted block mb-1">Failing Line</span>
              <div
                className="font-mono text-accent font-medium truncate flex items-center gap-1.5"
                title={`${run.incident.file_path}:${run.incident.line_number}`}
              >
                <FileCode className="w-3.5 h-3.5 flex-shrink-0" />
                <span>
                  {run.incident.file_path}:{run.incident.line_number}
                </span>
              </div>
            </div>

            <div>
              <span className="text-text-muted block mb-1">Blamed Suspect</span>
              <div className="flex items-center gap-1.5 text-primary">
                <span className="font-semibold">@{run.culprit.author_login}</span>
                {run.culprit.pr_number && (
                  <span className="text-text-muted font-mono text-caption flex items-center">
                    <GitPullRequest className="w-3 h-3 ml-1 mr-0.5 text-accent" />
                    PR-{run.culprit.pr_number}
                  </span>
                )}
              </div>
            </div>

            <div>
              <span className="text-text-muted block mb-1">Confidence</span>
              <ConfidenceBadge confidence={run.culprit.confidence} />
            </div>
          </div>

          {/* Why it probably failed */}
          <div className="space-y-2">
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted">
              Why it probably failed
            </h3>
            <div className="p-4 rounded-lg bg-surface border border-border-subtle text-dense text-secondary leading-relaxed">
              {run.explanation.root_cause_hypothesis}
            </div>
          </div>

          {/* Suspect change (Diff) */}
          <div className="space-y-2">
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted">
              Suspect change
            </h3>
            <DiffView
              diff={run.culprit.diff}
              sha={run.culprit.sha}
              message={run.culprit.message}
            />
          </div>

          {/* Verification checklist */}
          <div className="space-y-2">
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
              <CheckSquare className="w-3.5 h-3.5 text-success" />
              Verification checklist
            </h3>
            <div className="space-y-2">
              {run.explanation.checklist.map((step: string, idx: number) => (
                <label
                  key={idx}
                  onClick={() => toggleCheck(idx)}
                  className={`flex items-start gap-3 p-3 rounded-md border text-dense cursor-pointer transition-colors ${
                    checkedSteps[idx]
                      ? 'bg-success-subtle border-success/30 text-success line-through'
                      : 'bg-surface border-border-subtle text-secondary hover:border-border-strong'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={!!checkedSteps[idx]}
                    onChange={() => {}}
                    className="mt-0.5 h-4 w-4 rounded border-border-subtle text-accent focus:ring-accent"
                  />
                  <span>{step}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Footer watermark */}
          <div className="pt-3 border-t border-border-subtle text-caption text-text-muted font-mono flex items-center justify-between">
            <span>&lt;!-- ichnoscope:fp={run.fingerprint} --&gt;</span>
            <span>Deterministic blame at release SHA</span>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <pre className="p-4 rounded-md bg-canvas border border-border-subtle text-caption font-mono text-accent overflow-x-auto whitespace-pre-wrap">
            {rawMarkdown}
          </pre>
        </div>
      )}
    </div>
  );
}
