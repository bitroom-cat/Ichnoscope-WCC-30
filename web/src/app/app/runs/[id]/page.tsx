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
  Clock,
  Radio,
  Send,
  XCircle,
  RotateCcw,
  CheckCircle2,
  ExternalLink,
  Users,
  Copy,
  Check,
  Sparkles,
  Info,
  ShieldAlert,
} from 'lucide-react';

export default function RunDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [run, setRun] = useState<RunItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'diff' | 'stack' | 'logs' | 'preview'>('overview');
  const [copiedSha, setCopiedSha] = useState(false);
  const [approving, setApproving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    if (id) {
      setLoading(true);
      api.getRunById(id)
        .then((data) => {
          if (mounted) setRun(data);
        })
        .finally(() => {
          if (mounted) setLoading(false);
        });
    }
    return () => {
      mounted = false;
    };
  }, [id]);

  const handleApprove = async () => {
    if (!run) return;
    setApproving(true);
    try {
      const updated = await api.approveRun(run.id);
      setRun(updated);
      setToastMessage('Approved draft and published GitHub issue.');
      setTimeout(() => setToastMessage(null), 4000);
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!run) return;
    try {
      const updated = await api.rejectRun(run.id, 'Operator manual rejection');
      setRun(updated);
      setToastMessage('Draft discarded.');
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: any) {
      alert(err?.message || 'Error rejecting draft');
    }
  };

  const handleRerun = async () => {
    if (!run) return;
    try {
      const updated = await api.rerunTriage(run.id);
      setRun(updated);
      setToastMessage('Triage pipeline restarted.');
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: any) {
      alert(err?.message || 'Error rerunning triage');
    }
  };

  const handleCopySha = (sha: string) => {
    navigator.clipboard.writeText(sha);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-7 h-7 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-text-muted font-medium">Loading deployment and triage telemetry...</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="py-24 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto" />
        <h2 className="text-base font-semibold text-text-primary">Incident Record Not Found</h2>
        <p className="text-xs text-text-muted">The requested run ID does not exist in the database.</p>
        <Link
          href="/app/runs"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600 text-white text-xs font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents
        </Link>
      </div>
    );
  }

  const shortSha = run.culprit.sha ? run.culprit.sha.slice(0, 7) : 'unknown';
  const isApproved = run.status === 'approved' || run.status === 'published';
  const isPending = run.status === 'pending_approval' || run.status === 'draft_ready';
  const isRejected = run.status === 'rejected';

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 px-3.5 py-2 rounded-lg bg-text-primary text-canvas text-xs font-medium shadow-popover animate-in slide-in-from-bottom-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Render Banner */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800/40 text-xs text-purple-900 dark:text-purple-200">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-purple-600 shrink-0" />
          <span>
            Production listener active on <code className="font-mono font-medium">/webhook/sentry</code>.
            Correlating git history at release SHA with LLM verification checklist.
          </span>
        </div>
        <Link
          href="/app/connections"
          className="font-semibold text-purple-700 dark:text-purple-300 hover:underline shrink-0 ml-3"
        >
          View health
        </Link>
      </div>

      {/* Render Main Hero Title (Commit message format) */}
      <div className="space-y-1.5 pt-1">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-mono text-purple-600 dark:text-purple-400 font-semibold uppercase tracking-wider">
            {run.incident.exception_type}
          </span>
          <span className="text-text-muted">•</span>
          <span className="font-mono text-text-muted">fp:{run.fingerprint}</span>
          {run.is_regression && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300">
              Regression
            </span>
          )}
        </div>

        <h1 className="text-lg sm:text-xl font-bold text-text-primary tracking-tight leading-snug">
          {run.culprit.message || run.incident.error_message}
        </h1>

        <p className="text-xs text-text-secondary font-mono">
          Failing at <span className="text-purple-600 dark:text-purple-400 font-semibold">{run.incident.file_path}:{run.incident.line_number}</span>
          {' '}• {run.incident.error_message}
        </p>
      </div>

      {/* Render Signature 2x3 Metadata Card Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Card 1: STATUS */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <div className="mt-0.5">
            {isApproved ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            ) : isRejected ? (
              <XCircle className="w-4 h-4 text-rose-500" />
            ) : (
              <span className="relative flex h-3.5 w-3.5 mt-0.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-purple-600" />
              </span>
            )}
          </div>
          <div className="space-y-0.5 min-w-0">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Status
            </div>
            <div className="font-medium text-xs text-text-primary flex items-center gap-1.5">
              <span>{isApproved ? 'Published | Live' : isRejected ? 'Rejected' : 'Triage Ready | Needs Sign-off'}</span>
            </div>
            {run.published_issue_url && (
              <a
                href={run.published_issue_url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1 mt-0.5"
              >
                <span>GitHub Issue</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Card 2: DURATION / SPEED */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <Clock className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />
          <div className="space-y-0.5">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Duration
            </div>
            <div className="font-medium text-xs text-text-primary font-mono">
              {(run.metrics.time_to_triage_ms / 1000).toFixed(2)}s
            </div>
            <div className="text-[11px] text-text-muted">
              Inference: {run.metrics.llm_provider || 'llama-3.3-70b'}
            </div>
          </div>
        </div>

        {/* Card 3: OCCURRED / DEPLOYED */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <Calendar className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />
          <div className="space-y-0.5 min-w-0">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Occurred At
            </div>
            <div className="font-medium text-xs text-text-primary truncate">
              {new Date(run.incident.first_seen || run.created_at).toLocaleString()}
            </div>
            <div className="text-[11px] text-text-muted">
              Release SHA: <code className="font-mono text-purple-600">{run.incident.release_sha ? run.incident.release_sha.slice(0, 7) : 'HEAD'}</code>
            </div>
          </div>
        </div>

        {/* Card 4: TRIGGER / SOURCE */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <Radio className="w-4 h-4 text-purple-600 mt-0.5 shrink-0" />
          <div className="space-y-0.5">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Trigger
            </div>
            <div className="font-medium text-xs text-text-primary">
              Sentry Webhook (Auto-Triage)
            </div>
            <div className="text-[11px] text-text-muted">
              Severity: <span className="font-semibold text-text-primary">{run.severity}</span> ({run.explanation.domain})
            </div>
          </div>
        </div>

        {/* Card 5: SOURCE / SUSPECT COMMIT */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <GitCommit className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />
          <div className="space-y-0.5 min-w-0">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Suspect Commit
            </div>
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <span className="text-purple-600 dark:text-purple-400 font-semibold">
                {shortSha}
              </span>
              <button
                onClick={() => handleCopySha(run.culprit.sha)}
                className="text-text-muted hover:text-text-primary p-0.5"
                title="Copy full SHA"
              >
                {copiedSha ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              </button>
              {run.culprit.pr_number && (
                <span className="text-text-muted flex items-center gap-0.5">
                  <GitPullRequest className="w-3 h-3 text-purple-600" /> #{run.culprit.pr_number}
                </span>
              )}
            </div>
            <div className="text-[11px] text-text-muted truncate">
              Author: @{run.culprit.author_login} ({run.culprit.author_name})
            </div>
          </div>
        </div>

        {/* Card 6: IMPACT & LOCATION */}
        <div className="p-3.5 rounded-lg border border-border-subtle bg-surface flex items-start gap-3">
          <Users className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />
          <div className="space-y-0.5 min-w-0">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
              Impact & Environment
            </div>
            <div className="font-medium text-xs text-text-primary">
              {run.incident.users_affected} users • {run.incident.event_count} events
            </div>
            <div className="text-[11px] text-text-muted">
              Environment: <span className="text-emerald-600 font-medium">{run.incident.environment || 'production'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Render Action & Navigation Tabs Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pt-2 pb-0">
        {/* Left Side: Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'overview'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Overview & Synthesis</span>
          </button>

          <button
            onClick={() => setActiveTab('diff')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'diff'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Suspect Code Diff</span>
          </button>

          <button
            onClick={() => setActiveTab('stack')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'stack'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Stack Excerpt</span>
          </button>

          <button
            onClick={() => setActiveTab('logs')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'logs'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Execution Logs</span>
          </button>

          <button
            onClick={() => setActiveTab('preview')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'preview'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>GitHub Issue Draft</span>
          </button>
        </div>

        {/* Right Side: Quick Action Buttons (Render Action Row) */}
        <div className="flex items-center gap-2 pb-2 sm:pb-1">
          {isPending && (
            <>
              <button
                onClick={handleReject}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border-subtle bg-surface hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-600 text-xs font-medium transition-colors"
                title="Discard this draft"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>

              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{approving ? 'Publishing...' : 'Approve & Publish'}</span>
              </button>
            </>
          )}

          <button
            onClick={handleRerun}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border-subtle bg-surface hover:bg-hover text-text-secondary hover:text-text-primary text-xs font-medium transition-colors"
            title="Re-run automated investigation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Re-run</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Overview & Synthesis */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Why It Probably Failed (LLM Root Cause Synthesis) */}
          <div className="p-4 sm:p-5 rounded-lg border border-border-subtle bg-surface space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-xs uppercase tracking-wider text-text-muted font-mono flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                Why It Probably Failed (Automated Synthesis)
              </h3>
              <span className="text-[11px] font-mono text-text-muted">
                Confidence: {run.explanation.confidence_level || 'high'}
              </span>
            </div>
            <p className="text-xs text-text-primary leading-relaxed bg-canvas p-3 rounded-md border border-border-subtle font-sans">
              {run.explanation.root_cause_hypothesis}
            </p>
          </div>

          {/* 3-Step Verification Checklist */}
          <div className="p-4 sm:p-5 rounded-lg border border-border-subtle bg-surface space-y-3">
            <h3 className="font-semibold text-xs uppercase tracking-wider text-text-muted font-mono flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              Verification Steps (Actionable Triage Checklist)
            </h3>
            <div className="space-y-2">
              {run.explanation.checklist.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-2.5 rounded bg-canvas border border-border-subtle text-xs text-text-primary"
                >
                  <span className="w-4 h-4 rounded border border-border-strong text-purple-600 flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-mono font-bold">
                    {idx + 1}
                  </span>
                  <span className="leading-snug">{step}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Diff Excerpt */}
          <div className="p-4 sm:p-5 rounded-lg border border-border-subtle bg-surface space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-xs uppercase tracking-wider text-text-muted font-mono flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5 text-purple-600" />
                Suspect Code Diff Preview
              </h3>
              <button
                onClick={() => setActiveTab('diff')}
                className="text-xs text-purple-600 hover:underline"
              >
                Expand full diff →
              </button>
            </div>
            <DiffView diff={run.culprit.diff} filename={run.incident.file_path} />
          </div>
        </div>
      )}

      {/* Tab 2: Full Suspect Commit Diff */}
      {activeTab === 'diff' && (
        <div className="p-4 sm:p-5 rounded-lg border border-border-subtle bg-surface space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle text-xs">
            <div className="font-mono text-text-primary font-semibold flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-purple-600" />
              <span>{run.incident.file_path}</span>
            </div>
            <div className="text-text-muted font-mono">
              Commit {shortSha} by @{run.culprit.author_login}
            </div>
          </div>
          <DiffView diff={run.culprit.diff} filename={run.incident.file_path} />
        </div>
      )}

      {/* Tab 3: Stack Excerpt */}
      {activeTab === 'stack' && (
        <div className="p-4 sm:p-5 rounded-lg border border-border-subtle bg-surface space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle text-xs">
            <h3 className="font-semibold text-text-primary">Failing Stack Trace Excerpt</h3>
            <span className="text-text-muted font-mono text-[11px]">
              Last in-app frame: line {run.incident.line_number}
            </span>
          </div>
          <pre className="font-mono text-xs bg-canvas p-4 rounded-md border border-border-subtle text-text-secondary overflow-x-auto whitespace-pre leading-relaxed">
            {run.incident.stack_excerpt || run.incident.stack_trace}
          </pre>
        </div>
      )}

      {/* Tab 4: Execution Logs */}
      {activeTab === 'logs' && (
        <div className="rounded-lg border border-border-subtle overflow-hidden">
          <LogViewer logs={run.logs} />
        </div>
      )}

      {/* Tab 5: GitHub Issue Draft */}
      {activeTab === 'preview' && (
        <div className="rounded-lg border border-border-subtle bg-surface p-4 sm:p-6">
          <IssuePreview run={run} />
        </div>
      )}
    </div>
  );
}
