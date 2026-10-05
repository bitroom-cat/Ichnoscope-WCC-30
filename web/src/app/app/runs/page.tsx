'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, RunItem } from '@/lib/api';
import {
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  GitCommit,
  RotateCcw,
  Sparkles,
  Info,
  ChevronRight,
  ExternalLink,
  Plus,
  Play,
  X,
  Radio,
  FileCode,
} from 'lucide-react';

export default function RunsListPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'published' | 'rejected'>('all');
  const [replayModalOpen, setReplayModalOpen] = useState(false);
  const [replaying, setReplaying] = useState(false);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.getRuns();
      setRuns(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const triggerReplay = async (fixture: 'payment_npe' | 'auth_jwt' | 'db_leak') => {
    setReplaying(true);
    try {
      const newRun = await api.replaySavedFixture(fixture);
      setReplayModalOpen(false);
      router.push(`/app/runs/${newRun.id}`);
    } finally {
      setReplaying(false);
    }
  };

  const pendingRuns = runs.filter(
    (r) => r.status === 'pending_approval' || r.status === 'draft_ready'
  );
  const publishedRuns = runs.filter(
    (r) => r.status === 'approved' || r.status === 'published'
  );
  const rejectedRuns = runs.filter((r) => r.status === 'rejected');

  const filteredRuns = runs.filter((run) => {
    // Filter by tab
    if (activeTab === 'pending' && run.status !== 'pending_approval' && run.status !== 'draft_ready') {
      return false;
    }
    if (activeTab === 'published' && run.status !== 'approved' && run.status !== 'published') {
      return false;
    }
    if (activeTab === 'rejected' && run.status !== 'rejected') {
      return false;
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchMsg = (run.culprit.message || '').toLowerCase().includes(q);
      const matchErr = run.incident.error_message.toLowerCase().includes(q);
      const matchType = run.incident.exception_type.toLowerCase().includes(q);
      const matchSha = run.culprit.sha.toLowerCase().includes(q);
      const matchAuthor = run.culprit.author_login.toLowerCase().includes(q);
      const matchFile = run.incident.file_path.toLowerCase().includes(q);
      if (!matchMsg && !matchErr && !matchType && !matchSha && !matchAuthor && !matchFile) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Top Banner (Render Style) */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800/40 text-xs text-purple-900 dark:text-purple-200">
        <div className="flex items-center gap-2 min-w-0">
          <Info className="w-4 h-4 text-purple-600 shrink-0" />
          <span className="truncate">
            Production listener active on <code className="font-mono font-medium">/webhook/sentry</code>.
            Correlating runtime exceptions with Git blame at release SHA.
          </span>
        </div>
        <Link
          href="/app/connections"
          className="font-semibold text-purple-700 dark:text-purple-300 hover:underline shrink-0 ml-3"
        >
          View health
        </Link>
      </div>

      {/* Page Header (Render Style) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary tracking-tight">Deploys</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Deployment history, Sentry regression alerts, and human-in-the-loop triage decisions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchRuns()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border-subtle bg-surface hover:bg-hover text-text-secondary hover:text-text-primary text-xs font-medium transition-colors"
            title="Refresh deploys"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={() => setReplayModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Trigger Webhook</span>
          </button>
        </div>
      </div>

      {/* Search & Tabs Filter Row (Render Style) */}
      <div className="border-b border-border-subtle flex flex-col md:flex-row md:items-center justify-between gap-3 pb-0">
        {/* Render Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-2 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'all'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <span>All Deploys</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-canvas border border-border-subtle text-text-muted">
              {runs.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('pending')}
            className={`px-3 py-2 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'pending'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <span>Pending Review</span>
            {pendingRuns.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 font-semibold">
                {pendingRuns.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('published')}
            className={`px-3 py-2 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'published'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <span>Live / Published</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-canvas border border-border-subtle text-text-muted">
              {publishedRuns.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('rejected')}
            className={`px-3 py-2 border-b-2 font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'rejected'
                ? 'border-purple-600 text-purple-600 dark:text-purple-400 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <span>Discarded</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-canvas border border-border-subtle text-text-muted">
              {rejectedRuns.length}
            </span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative mb-2 md:mb-0 w-full md:w-80">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search commits, files, authors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-canvas border border-border-subtle rounded-md text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-purple-600"
          />
        </div>
      </div>

      {/* Deploys List Stream (Render Style) */}
      <div className="space-y-2">
        {loading ? (
          <div className="py-20 text-center space-y-2">
            <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-text-muted">Loading deploy history...</p>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="py-16 text-center space-y-3 rounded-lg border border-border-subtle bg-surface">
            <div className="w-10 h-10 rounded-full bg-purple-50 dark:bg-purple-950/40 text-purple-600 mx-auto flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">No deploys match this filter</p>
              <p className="text-xs text-text-muted mt-1">
                Try clearing the search query or triggering a Sentry incident webhook.
              </p>
            </div>
            <button
              onClick={() => setReplayModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600 text-white text-xs font-medium hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Simulate Webhook</span>
            </button>
          </div>
        ) : (
          filteredRuns.map((run) => {
            const shortSha = run.culprit.sha ? run.culprit.sha.slice(0, 7) : '53f7103';
            const isApproved = run.status === 'approved' || run.status === 'published';
            const isPending = run.status === 'pending_approval' || run.status === 'draft_ready';
            const isRejected = run.status === 'rejected';
            const displayTitle = run.culprit.message || `${run.incident.exception_type}: ${run.incident.error_message}`;
            const triageDurationSec = (run.metrics.time_to_triage_ms / 1000).toFixed(1);

            return (
              <Link
                key={run.id}
                href={`/app/runs/${run.id}`}
                className="group block p-4 rounded-lg border border-border-subtle bg-surface hover:border-purple-400 dark:hover:border-purple-600/70 transition-all hover:shadow-xs"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  {/* Left Column: Status Icon & Commit / Incident Details */}
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    {/* Status Dot / Indicator */}
                    <div className="mt-0.5 shrink-0">
                      {isApproved ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : isRejected ? (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      ) : (
                        <span className="relative flex h-3.5 w-3.5 mt-0.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-amber-500" />
                        </span>
                      )}
                    </div>

                    {/* Commit & Metadata */}
                    <div className="space-y-1 min-w-0">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="text-xs font-semibold text-text-primary group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors truncate">
                          {displayTitle}
                        </span>
                        {run.is_regression && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 shrink-0">
                            Regression
                          </span>
                        )}
                      </div>

                      {/* Sub-line metadata (Render style) */}
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
                        {/* Status Label */}
                        <span className="font-medium text-text-secondary">
                          {isApproved ? (
                            <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Deploy succeeded | Live</span>
                          ) : isRejected ? (
                            <span className="text-rose-600 dark:text-rose-400">Discarded</span>
                          ) : (
                            <span className="text-amber-600 dark:text-amber-400 font-semibold">Awaiting sign-off</span>
                          )}
                        </span>

                        <span>•</span>

                        {/* Commit SHA Pill */}
                        <span className="inline-flex items-center gap-1 font-mono text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/30 px-1.5 py-0.5 rounded">
                          <GitCommit className="w-3 h-3" />
                          {shortSha}
                        </span>

                        <span>•</span>

                        {/* Branch */}
                        <span className="font-mono text-text-secondary">
                          production
                        </span>

                        <span>•</span>

                        {/* Author */}
                        <span>
                          @{run.culprit.author_login}
                        </span>

                        <span>•</span>

                        {/* Trigger */}
                        <span>
                          Auto-Deploy (Sentry)
                        </span>

                        <span>•</span>

                        {/* Date */}
                        <span>
                          {new Date(run.incident.first_seen || run.created_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Duration, Action & Chevron */}
                  <div className="flex items-center justify-between md:justify-end gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-border-subtle text-xs">
                    {/* Triage Speed */}
                    <div className="text-right hidden sm:block">
                      <div className="font-mono text-xs text-text-primary font-medium">
                        {triageDurationSec}s
                      </div>
                      <div className="text-[10px] text-text-muted font-mono">
                        {run.incident.users_affected} users
                      </div>
                    </div>

                    {/* Quick Button / Pill */}
                    {isPending ? (
                      <span className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-700 text-white font-medium text-xs shadow-xs transition-colors flex items-center gap-1">
                        Review & Sign-off
                      </span>
                    ) : isApproved ? (
                      <span className="px-2 py-0.5 rounded border border-emerald-500/40 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
                        Live Issue
                      </span>
                    ) : (
                      <span className="text-text-muted text-xs">
                        Archived
                      </span>
                    )}

                    <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </Link>
            );
          })
        )}
      </div>

      {/* Quick Sentry Webhook Simulation Modal */}
      {replayModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border-subtle bg-surface p-5 shadow-popover space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-purple-600 text-white flex items-center justify-center">
                  <Play className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-text-primary">Trigger Webhook Simulation</h3>
                  <p className="text-[11px] text-text-muted">Replay an incident payload to test automated triage</p>
                </div>
              </div>
              <button
                onClick={() => setReplayModalOpen(false)}
                className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-hover"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 pt-1 text-xs">
              <button
                onClick={() => triggerReplay('payment_npe')}
                disabled={replaying}
                className="w-full text-left p-3 rounded-lg border border-border-subtle bg-canvas hover:border-purple-600 hover:bg-purple-50/50 dark:hover:bg-purple-950/20 transition-all flex items-start justify-between group"
              >
                <div className="space-y-0.5">
                  <div className="font-semibold text-text-primary group-hover:text-purple-600">
                    Payment Gateway KeyError
                  </div>
                  <div className="text-[11px] text-text-muted font-mono">
                    KeyError: stripe_customer_id in payment_gateway.py
                  </div>
                  <div className="text-[10px] text-purple-600 dark:text-purple-400 font-mono">
                    Suspect: 53f7103 • P1-Critical
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-purple-600 mt-1" />
              </button>

              <button
                onClick={() => triggerReplay('auth_jwt')}
                disabled={replaying}
                className="w-full text-left p-3 rounded-lg border border-border-subtle bg-canvas hover:border-purple-600 hover:bg-purple-50/50 dark:hover:bg-purple-950/20 transition-all flex items-start justify-between group"
              >
                <div className="space-y-0.5">
                  <div className="font-semibold text-text-primary group-hover:text-purple-600">
                    Cart Checkout AttributeError
                  </div>
                  <div className="text-[11px] text-text-muted font-mono">
                    AttributeError: NoneType has no calculate_tax
                  </div>
                  <div className="text-[10px] text-purple-600 dark:text-purple-400 font-mono">
                    Suspect: 7a8b9c0 • P2-High
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-purple-600 mt-1" />
              </button>

              <button
                onClick={() => triggerReplay('db_leak')}
                disabled={replaying}
                className="w-full text-left p-3 rounded-lg border border-border-subtle bg-canvas hover:border-purple-600 hover:bg-purple-50/50 dark:hover:bg-purple-950/20 transition-all flex items-start justify-between group"
              >
                <div className="space-y-0.5">
                  <div className="font-semibold text-text-primary group-hover:text-purple-600">
                    Edge Library Frame Last
                  </div>
                  <div className="text-[11px] text-text-muted font-mono">
                    RuntimeError in urllib3 connection pool
                  </div>
                  <div className="text-[10px] text-purple-600 dark:text-purple-400 font-mono">
                    In-app frame detection heuristic
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-purple-600 mt-1" />
              </button>
            </div>

            {replaying && (
              <div className="text-center text-xs text-purple-600 dark:text-purple-400 font-medium py-1 animate-pulse">
                Synthesizing triage with LLM...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
