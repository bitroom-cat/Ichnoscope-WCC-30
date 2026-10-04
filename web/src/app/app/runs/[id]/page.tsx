'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, RunItem } from '@/lib/api';
import {
  RunStatusBadge,
  SeverityBadge,
  DomainBadge,
  ConfidenceBadge,
  RegressionBadge,
} from '@/components/primitives/Badge';
import { ActionBar } from '@/components/ActionBar';
import { IssuePreview } from '@/components/IssuePreview';
import { LogViewer } from '@/components/primitives/LogViewer';
import { DiffView } from '@/components/primitives/DiffView';
import {
  ArrowLeft,
  GitCommit,
  GitPullRequest,
  FileCode,
  Calendar,
  Layers,
  Terminal,
  FileText,
  Code2,
  AlertTriangle,
} from 'lucide-react';

export default function RunDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [run, setRun] = useState<RunItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'preview' | 'diff' | 'stack' | 'logs'>('preview');

  const loadRun = async () => {
    setLoading(true);
    try {
      const data = await api.getRunById(id);
      setRun(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadRun();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleApprove = async () => {
    if (!run) return;
    const updated = await api.approveRun(run.id);
    setRun(updated);
  };

  const handleReject = async (reason?: string) => {
    if (!run) return;
    const updated = await api.rejectRun(run.id, reason);
    setRun(updated);
  };

  const handleRerun = async () => {
    if (!run) return;
    const updated = await api.rerunTriage(run.id);
    setRun(updated);
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-dense text-text-muted">Loading incident record...</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="py-20 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-warning mx-auto" />
        <h2 className="text-title-3 font-semibold text-primary">Incident Not Found</h2>
        <p className="text-dense text-text-muted">The requested run ID does not exist.</p>
        <Link
          href="/app/runs"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-accent text-on-accent text-dense font-medium"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Incident List
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Breadcrumb */}
      <div>
        <Link
          href="/app/runs"
          className="inline-flex items-center gap-1.5 text-dense text-secondary hover:text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents
        </Link>
      </div>

      {/* Header Card */}
      <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs transition-colors space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <RunStatusBadge status={run.status} />
            <SeverityBadge severity={run.severity} />
            <DomainBadge domain={run.explanation.domain} />
            <RegressionBadge isRegression={run.is_regression} />
            <span className="text-caption font-mono text-text-muted">fp:{run.fingerprint}</span>
          </div>

          <div className="flex items-center gap-2 text-caption">
            <ConfidenceBadge confidence={run.culprit.confidence} />
            <span className="text-text-muted font-mono text-caption">
              {(run.metrics.time_to_triage_ms / 1000).toFixed(2)}s • {run.metrics.llm_provider}
            </span>
          </div>
        </div>

        <div>
          <h1 className="text-title-2 font-semibold text-primary tracking-tight flex flex-wrap items-baseline gap-2">
            <span className="font-mono text-danger">{run.incident.exception_type}:</span>
            <span>{run.incident.error_message}</span>
          </h1>

          <div className="flex flex-wrap items-center gap-3 text-caption text-secondary font-mono mt-1.5">
            <span className="text-accent font-medium flex items-center gap-1">
              <FileCode className="w-3.5 h-3.5" />
              {run.incident.file_path}:{run.incident.line_number}
            </span>
            <span>•</span>
            <span>Release SHA: {run.incident.release_sha}</span>
            <span>•</span>
            <span>Env: {run.incident.environment}</span>
            <span>•</span>
            <span>{run.incident.users_affected} users affected</span>
          </div>
        </div>
      </div>

      {/* Action Bar (Approve / Reject / Re-run) */}
      <ActionBar run={run} onApprove={handleApprove} onReject={handleReject} onRerun={handleRerun} />

      {/* Suspect Commit Bar */}
      <div className="p-4 rounded-lg border border-border-subtle bg-surface shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3 text-dense transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-canvas text-primary font-bold text-caption flex items-center justify-center border border-border-subtle">
            {run.culprit.author_login.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-text-muted text-caption uppercase font-mono">Suspect Author:</span>
              <span className="font-semibold text-primary">@{run.culprit.author_login}</span>
              <span className="text-secondary text-caption">({run.culprit.author_name})</span>
            </div>
            <div className="flex items-center gap-2 text-secondary mt-0.5 font-mono text-caption">
              <GitCommit className="w-3.5 h-3.5 text-accent" />
              <span className="text-accent font-medium">{run.culprit.sha}</span>
              <span>—</span>
              <span className="truncate max-w-sm">{run.culprit.message}</span>
              {run.culprit.pr_number && (
                <span className="text-accent flex items-center gap-0.5">
                  <GitPullRequest className="w-3 h-3" /> PR-{run.culprit.pr_number}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="text-secondary flex items-center gap-1.5 text-caption">
          <Calendar className="w-3.5 h-3.5" />
          <span>
            {run.culprit.within_window ? (
              <span className="text-warning font-medium">Committed within 24h (Likely regression)</span>
            ) : (
              <span>Old code (Likely triggered by new payload)</span>
            )}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-subtle gap-1 text-dense">
        <button
          onClick={() => setActiveTab('preview')}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 font-medium border-b-2 transition-all ${
            activeTab === 'preview'
              ? 'border-accent text-accent font-semibold'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          <FileText className="w-4 h-4" />
          Issue Draft
        </button>

        <button
          onClick={() => setActiveTab('diff')}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 font-medium border-b-2 transition-all ${
            activeTab === 'diff'
              ? 'border-accent text-accent font-semibold'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          <Code2 className="w-4 h-4" />
          Suspect Commit Diff
        </button>

        <button
          onClick={() => setActiveTab('stack')}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 font-medium border-b-2 transition-all ${
            activeTab === 'stack'
              ? 'border-accent text-accent font-semibold'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          <Layers className="w-4 h-4" />
          Stack Excerpt
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 font-medium border-b-2 transition-all ${
            activeTab === 'logs'
              ? 'border-accent text-accent font-semibold'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          <Terminal className="w-4 h-4" />
          Pipeline Execution Logs ({run.logs.length})
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'preview' && (
        <div>
          <IssuePreview run={run} />
        </div>
      )}

      {activeTab === 'diff' && (
        <DiffView
          diff={run.culprit.diff}
          sha={run.culprit.sha}
          message={run.culprit.message}
        />
      )}

      {activeTab === 'stack' && (
        <div className="rounded-lg border border-border-subtle bg-surface p-5 space-y-4 shadow-xs">
          <div>
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-1">
              Last In-Application Stack Frame
            </h3>
            <p className="text-caption text-secondary">
              Extracted deterministically from Sentry JSON. Stripped container path prefix.
            </p>
          </div>

          <div className="p-3.5 rounded-md bg-canvas border border-border-subtle font-mono text-caption text-accent font-semibold">
            {run.incident.file_path}:{run.incident.line_number}
          </div>

          <div>
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-1">
              Raw Stack Excerpt
            </h3>
            <pre className="p-4 rounded-md bg-canvas border border-border-subtle text-caption font-mono text-secondary whitespace-pre-wrap overflow-x-auto">
              {run.incident.stack_excerpt}
            </pre>
          </div>
        </div>
      )}

      {activeTab === 'logs' && (
        <div>
          <LogViewer
            logs={run.logs.map((log) => ({
              ts: log.ts || '00:00:00.000',
              level: (log.level as 'info' | 'warn' | 'error') || 'info',
              message: log.message,
              step: log.step,
            }))}
          />
        </div>
      )}
    </div>
  );
}
