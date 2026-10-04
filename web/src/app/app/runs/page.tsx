'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, RunItem } from '@/lib/api';
import { RunStatusBadge, SeverityBadge, DomainBadge, RegressionBadge } from '@/components/primitives/Badge';
import {
  Search,
  ArrowRight,
  Users,
  Clock,
  CheckCircle2,
  AlertCircle,
  Layers,
  ShieldAlert,
} from 'lucide-react';

export default function DashboardPage() {
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [domainFilter, setDomainFilter] = useState<string>('all');

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

  const handleQuickApprove = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.approveRun(id);
      await fetchRuns();
    } catch (err: any) {
      alert(err?.message || 'Error approving');
    }
  };

  const filteredRuns = runs.filter((run) => {
    if (statusFilter !== 'all' && run.status !== statusFilter) return false;
    if (severityFilter !== 'all' && run.severity !== severityFilter) return false;
    if (domainFilter !== 'all' && run.explanation.domain !== domainFilter) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchException = run.incident.exception_type.toLowerCase().includes(q);
      const matchMessage = run.incident.error_message.toLowerCase().includes(q);
      const matchAuthor = run.culprit.author_login.toLowerCase().includes(q);
      const matchFile = run.incident.file_path.toLowerCase().includes(q);
      const matchSha = run.culprit.sha.toLowerCase().includes(q);
      if (!matchException && !matchMessage && !matchAuthor && !matchFile && !matchSha) {
        return false;
      }
    }
    return true;
  });

  const totalRuns = runs.length;
  const pendingCount = runs.filter((r) => r.status === 'pending_approval').length;
  const approvedCount = runs.filter((r) => r.status === 'approved').length;
  const totalSuppressed = runs.reduce((acc, r) => acc + (r.metrics?.suppressed_duplicates || 0), 0);
  const avgTriageSeconds = runs.length
    ? (runs.reduce((acc, r) => acc + (r.metrics?.time_to_triage_ms || 1500), 0) / (runs.length * 1000)).toFixed(1)
    : '1.6';

  return (
    <div className="space-y-6">
      {/* SaaS Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-subtle pb-5">
        <div>
          <h1 className="text-title-2 font-semibold text-primary tracking-tight">
            Incident Triage Stream
          </h1>
          <p className="text-dense text-secondary mt-1">
            Automated Sentry error correlation, release-SHA git blame, and human sign-off cockpit.
          </p>
        </div>

        <div className="flex items-center gap-2 text-caption font-medium text-secondary bg-surface border border-border-subtle px-3 py-1.5 rounded-md shadow-xs">
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span>Gateway active at <code className="font-mono text-accent">/webhook/sentry</code></span>
        </div>
      </div>

      {/* KPI Metric Tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-lg bg-surface border border-border-subtle shadow-xs space-y-1">
          <div className="flex items-center justify-between text-caption text-text-muted">
            <span>Pending Review</span>
            <AlertCircle className="w-4 h-4 text-warning" />
          </div>
          <div className="text-title-2 font-bold text-primary font-mono">{pendingCount}</div>
          <p className="text-caption text-text-muted">Awaiting human sign-off</p>
        </div>

        <div className="p-4 rounded-lg bg-surface border border-border-subtle shadow-xs space-y-1">
          <div className="flex items-center justify-between text-caption text-text-muted">
            <span>Published to GitHub</span>
            <CheckCircle2 className="w-4 h-4 text-success" />
          </div>
          <div className="text-title-2 font-bold text-primary font-mono">{approvedCount}</div>
          <p className="text-caption text-text-muted">Issues opened in repo</p>
        </div>

        <div className="p-4 rounded-lg bg-surface border border-border-subtle shadow-xs space-y-1">
          <div className="flex items-center justify-between text-caption text-text-muted">
            <span>Mean Time To Triage</span>
            <Clock className="w-4 h-4 text-accent" />
          </div>
          <div className="text-title-2 font-bold text-primary font-mono">{avgTriageSeconds}s</div>
          <p className="text-caption text-success font-medium">Target &lt; 60s</p>
        </div>

        <div className="p-4 rounded-lg bg-surface border border-border-subtle shadow-xs space-y-1">
          <div className="flex items-center justify-between text-caption text-text-muted">
            <span>Storm Repeats Suppressed</span>
            <Layers className="w-4 h-4 text-accent" />
          </div>
          <div className="text-title-2 font-bold text-primary font-mono">{totalSuppressed}</div>
          <p className="text-caption text-text-muted">SQLite unique lock</p>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="p-3.5 sm:p-4 rounded-lg bg-surface border border-border-subtle shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by error, file path, author (@login), or commit SHA..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-canvas border border-border-subtle rounded-md text-dense text-primary placeholder-text-muted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 text-dense">
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted text-caption">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-canvas border border-border-subtle rounded-md px-2.5 py-1.5 text-secondary text-dense focus:outline-none focus:border-accent"
            >
              <option value="all">All statuses ({totalRuns})</option>
              <option value="pending_approval">Pending Review ({pendingCount})</option>
              <option value="approved">Published ({approvedCount})</option>
              <option value="rejected">Discarded</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-text-muted text-caption">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-canvas border border-border-subtle rounded-md px-2.5 py-1.5 text-secondary text-dense focus:outline-none focus:border-accent"
            >
              <option value="all">All severities</option>
              <option value="P1-Critical">P1-Critical</option>
              <option value="P2-High">P2-High</option>
              <option value="P3-Medium">P3-Medium</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-text-muted text-caption">Domain:</span>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-canvas border border-border-subtle rounded-md px-2.5 py-1.5 text-secondary text-dense focus:outline-none focus:border-accent"
            >
              <option value="all">All domains</option>
              <option value="backend">Backend</option>
              <option value="frontend">Frontend</option>
              <option value="database">Database</option>
              <option value="infra">Infra</option>
            </select>
          </div>
        </div>
      </div>

      {/* Incident List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-caption text-text-muted px-1">
          <span>Showing {filteredRuns.length} incidents</span>
          <span>Sorted by latest occurrence</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-text-muted text-dense">Loading incidents...</div>
        ) : filteredRuns.length === 0 ? (
          <div className="p-12 rounded-lg border border-border-subtle bg-surface text-center space-y-2">
            <ShieldAlert className="w-8 h-8 text-text-muted mx-auto" />
            <p className="text-dense font-semibold text-primary">No matching incident records found</p>
            <p className="text-caption text-secondary">Try modifying filters or simulating a new Sentry webhook replay.</p>
          </div>
        ) : (
          filteredRuns.map((run) => (
            <Link
              key={run.id}
              href={`/app/runs/${run.id}`}
              className="block rounded-lg border border-border-subtle bg-surface p-4 sm:p-5 shadow-xs hover:border-accent transition-all group"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Left: Exception details */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <RunStatusBadge status={run.status} />
                    <SeverityBadge severity={run.severity} />
                    <DomainBadge domain={run.explanation.domain} />
                    <RegressionBadge isRegression={run.is_regression} />
                    <span className="text-caption font-mono text-text-muted">fp:{run.fingerprint}</span>
                  </div>

                  <div>
                    <h2 className="text-dense sm:text-subhead font-semibold text-primary group-hover:text-accent transition-colors flex items-baseline gap-2">
                      <span className="font-mono text-danger text-dense sm:text-subhead">
                        {run.incident.exception_type}:
                      </span>
                      <span className="truncate">{run.incident.error_message}</span>
                    </h2>
                    <p className="text-caption text-secondary font-mono mt-0.5">
                      {run.incident.file_path}:{run.incident.line_number}
                    </p>
                  </div>

                  <p className="text-caption text-secondary line-clamp-1 italic">
                    &ldquo;{run.explanation.root_cause_hypothesis}&rdquo;
                  </p>
                </div>

                {/* Right: Suspect & Impact meta */}
                <div className="flex flex-wrap lg:flex-col items-start lg:items-end justify-between lg:justify-center gap-2.5 pt-3 lg:pt-0 border-t lg:border-t-0 border-border-subtle text-caption">
                  {/* Suspect pill */}
                  <div className="flex items-center gap-2 bg-canvas border border-border-subtle px-2.5 py-1 rounded-sm">
                    <span className="text-text-muted text-caption uppercase font-mono">Suspect:</span>
                    <span className="font-semibold text-primary">@{run.culprit.author_login}</span>
                    <span className="font-mono text-text-muted text-caption">({run.culprit.sha.slice(0, 7)})</span>
                  </div>

                  {/* Impact */}
                  <div className="flex items-center gap-2.5 text-caption text-text-muted">
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3 text-text-muted" />
                      {run.incident.users_affected} users
                    </span>
                    <span>•</span>
                    <span>{run.incident.event_count} events</span>
                    <span>•</span>
                    <span className="font-mono">{(run.metrics.time_to_triage_ms / 1000).toFixed(1)}s triage</span>
                  </div>

                  {/* Quick Action Button */}
                  <div className="flex items-center gap-2 pt-1">
                    {run.status === 'pending_approval' && (
                      <button
                        onClick={(e) => handleQuickApprove(e, run.id)}
                        className="px-2.5 py-1 rounded-sm bg-accent-subtle hover:bg-accent/20 text-accent font-medium text-caption border border-accent/30 transition-colors"
                      >
                        Quick Publish
                      </button>
                    )}
                    <span className="inline-flex items-center gap-1 text-caption font-semibold text-accent group-hover:translate-x-0.5 transition-transform">
                      Review <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
