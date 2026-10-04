// Purpose: Typed dashboard API client with a single flag for mock vs real backend.
// In accordance with Section 1 and Section 9 of the Frontend Build Prompt.

import { MOCK_RUNS, RunDetail, RunSummary, RunStatus } from './mock';

export type { RunDetail, RunSummary, RunStatus };

export type Severity = 'P1-Critical' | 'P2-High' | 'P3-Medium' | 'high' | 'medium' | 'low';
export type Domain = 'backend' | 'frontend' | 'database' | 'infra';

export interface RunLogEntry {
  timestamp?: string;
  ts?: string;
  step: string;
  level: string;
  message: string;
}

export interface DependencyHealth {
  key: string;
  name: string;
  status: 'healthy' | 'degraded' | 'offline' | 'sleeping';
  description: string;
  details?: string;
  latency_ms: number;
  last_check: string;
  meta?: Record<string, string>;
}

export interface SystemSettings {
  github_repo: string;
  fallback_assignee: string;
  path_prefix_strip: string;
  window_hours: number;
  p1_users: number;
  p1_events: number;
  p2_users: number;
  p2_events: number;
  llm_provider: string;
  dry_run: boolean;
  slack_channel: string;
  slack_enabled: boolean;
  auto_comment_duplicates: boolean;
}

export interface RunItem {
  id: string;
  status: any;
  severity: any;
  fingerprint: string;
  is_regression: boolean;
  issue_url?: string;
  incident: {
    exception_type: string;
    error_message: string;
    file_path: string;
    line_number: number;
    users_affected: number;
    event_count: number;
    sentry_issue_id: string;
    first_seen: string;
    last_seen: string;
    environment?: string;
    release_sha?: string;
    stack_trace: string;
    stack_excerpt?: string;
  };
  explanation: {
    root_cause_hypothesis: string;
    confidence_level: 'high' | 'low';
    domain: Domain;
    checklist: string[];
    suggested_fix?: string;
  };
  culprit: {
    author_login: string;
    author_name: string;
    sha: string;
    message: string;
    committed_date: string;
    diff: string;
    pr_number?: number;
    within_window?: boolean;
    confidence: 'high' | 'low';
  };
  metrics: {
    time_to_triage_ms: number;
    tokens_used: number;
    suppressed_duplicates?: number;
    llm_provider?: string;
  };
  logs: RunLogEntry[];
  published_issue_url?: string;
  created_at: string;
  updated_at: string;
}

export const USE_MOCK_API = true; // Switch to false when backend FastAPI is attached

const STORAGE_KEY = 'ichnoscope_runs_v2';

function getStoredRuns(): RunDetail[] {
  if (typeof window === 'undefined') return MOCK_RUNS;
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(MOCK_RUNS));
      return MOCK_RUNS;
    }
    return JSON.parse(data);
  } catch {
    return MOCK_RUNS;
  }
}

function saveStoredRuns(runs: RunDetail[]) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(runs));
  } catch (err) {
    console.error('Failed to persist runs', err);
  }
}

function toRunItem(r: RunDetail): RunItem {
  return {
    id: r.id,
    status: r.status === 'draft_ready' ? 'pending_approval' : r.status === 'published' ? 'approved' : r.status,
    severity: r.severity,
    fingerprint: r.fingerprint,
    is_regression: true,
    issue_url: r.issueUrl,
    incident: {
      exception_type: r.exceptionType,
      error_message: r.errorMessage,
      file_path: r.filePath,
      line_number: r.lineNumber,
      users_affected: Math.floor(r.eventCount * 0.4) + 1,
      event_count: r.eventCount,
      sentry_issue_id: `SEN-${r.id.slice(0, 4)}`,
      first_seen: r.createdAt,
      last_seen: r.updatedAt,
      environment: r.environment || 'production',
      release_sha: r.releaseSha,
      stack_trace: `${r.exceptionType}: ${r.errorMessage}\n  at ${r.filePath}:${r.lineNumber}`,
      stack_excerpt: r.stackFrames.map((f) => `${f.file}:${f.line} in ${f.fn}`).join('\n'),
    },
    explanation: {
      root_cause_hypothesis: r.explanation?.hypothesis || 'Potential regression in recent commits',
      confidence_level: r.confidence,
      domain: ((r.explanation?.domain as Domain) || 'backend') as Domain,
      checklist: r.explanation?.checklist || ['Verify stack trace', 'Check commit diff'],
    },
    culprit: {
      author_login: r.suspect?.login || 'unknown',
      author_name: r.suspect?.name || 'Developer',
      sha: r.culprit?.sha || r.releaseSha,
      message: r.culprit?.message || 'fix: update handler implementation',
      committed_date: r.culprit?.committedAt || r.createdAt,
      diff: r.culprit?.diff || `--- a/${r.filePath}\n+++ b/${r.filePath}\n@@ -${r.lineNumber},3 +${r.lineNumber},4 @@\n-    old_call()\n+    new_call()`,
      within_window: r.culprit?.withinWindow ?? true,
      confidence: r.confidence,
    },
    metrics: {
      time_to_triage_ms: 1200,
      tokens_used: 1240,
      suppressed_duplicates: 0,
      llm_provider: 'llama-3.3-70b-versatile',
    },
    logs: r.logs.map((l) => ({
      timestamp: l.ts,
      ts: l.ts,
      step: l.step,
      level: l.level,
      message: l.message,
    })),
    created_at: r.createdAt,
    updated_at: r.updatedAt,
  };
}

const DEFAULT_SETTINGS: SystemSettings = {
  github_repo: 'ichnoscope/wcc-demo-service',
  fallback_assignee: 'octocat',
  path_prefix_strip: 'src/',
  window_hours: 48,
  p1_users: 100,
  p1_events: 500,
  p2_users: 25,
  p2_events: 100,
  llm_provider: 'groq/llama-3.3-70b-versatile',
  dry_run: false,
  slack_channel: '#eng-incidents',
  slack_enabled: true,
  auto_comment_duplicates: true,
};

const DEFAULT_HEALTH: DependencyHealth[] = [
  {
    key: 'sentry',
    name: 'Sentry Webhooks',
    status: 'healthy',
    description: 'Ingesting error events from production sentry cluster',
    details: 'Webhook listener active on /api/webhooks/sentry',
    latency_ms: 42,
    last_check: 'Just now',
    meta: { endpoint: 'api.sentry.io/v0', queue_depth: '0 events' },
  },
  {
    key: 'github',
    name: 'GitHub API & Apps',
    status: 'healthy',
    description: 'Blame lookup and draft issue creation access',
    details: 'OAuth App authorized with repo permissions',
    latency_ms: 128,
    last_check: '1m ago',
    meta: { app_id: 'ichnoscope-bot', rate_limit: '4,892 / 5,000' },
  },
  {
    key: 'groq',
    name: 'Groq LLM Inference',
    status: 'healthy',
    description: 'Llama 3.3 70B Versatile for root-cause synthesis',
    details: 'Fast inference endpoint via Groq cloud',
    latency_ms: 310,
    last_check: '30s ago',
    meta: { model: 'llama-3.3-70b-versatile', speed: '240 t/s' },
  },
  {
    key: 'slack',
    name: 'Slack Incoming Webhook',
    status: 'healthy',
    description: 'Channel notifications for pending and approved runs',
    details: 'Incoming webhook delivering to #eng-incidents',
    latency_ms: 88,
    last_check: '2m ago',
    meta: { channel: '#eng-incidents', auth: 'webhook-verified' },
  },
];

export const api = {
  getRuns: async (): Promise<any[]> => {
    if (USE_MOCK_API) {
      const runs = getStoredRuns();
      return runs.map(toRunItem);
    }

    const res = await fetch('/api/runs');
    if (!res.ok) throw new Error('Failed to fetch runs');
    return res.json();
  },

  getRunById: async (id: string): Promise<any | null> => {
    if (USE_MOCK_API) {
      const runs = getStoredRuns();
      const r = runs.find((item) => item.id === id);
      if (!r) return null;
      return toRunItem(r);
    }

    const res = await fetch(`/api/runs/${id}`);
    if (!res.ok) return null;
    return res.json();
  },

  approveRun: async (id: string): Promise<any> => {
    if (USE_MOCK_API) {
      const runs = getStoredRuns();
      const idx = runs.findIndex((r) => r.id === id);
      if (idx === -1) throw new Error('Run not found');

      const issueNum = Math.floor(145 + Math.random() * 20);
      const updated: RunDetail = {
        ...runs[idx],
        status: 'published',
        issueUrl: `https://github.com/ichnoscope/wcc-demo-service/issues/${issueNum}`,
        updatedAt: new Date().toISOString(),
        steps: runs[idx].steps.map((s) => (s.name === 'publish' ? { ...s, state: 'done', ms: 195 } : s)),
        logs: [
          ...runs[idx].logs,
          {
            ts: new Date().toLocaleTimeString(),
            level: 'info',
            step: 'publish',
            message: `Human reviewer approved draft. Issue #${issueNum} opened in ichnoscope/wcc-demo-service and assigned to @${runs[idx].suspect?.login || 'assignee'}.`,
          },
        ],
      };
      runs[idx] = updated;
      saveStoredRuns(runs);
      return toRunItem(updated);
    }

    const res = await fetch(`/api/runs/${id}/approve`, { method: 'POST' });
    if (!res.ok) throw new Error('Approval failed');
    return res.json();
  },

  rejectRun: async (id: string, reason?: string): Promise<any> => {
    if (USE_MOCK_API) {
      const runs = getStoredRuns();
      const idx = runs.findIndex((r) => r.id === id);
      if (idx === -1) throw new Error('Run not found');

      const updated: RunDetail = {
        ...runs[idx],
        status: 'rejected',
        updatedAt: new Date().toISOString(),
        steps: runs[idx].steps.map((s) => (s.name === 'publish' ? { ...s, state: 'skipped' } : s)),
        logs: [
          ...runs[idx].logs,
          {
            ts: new Date().toLocaleTimeString(),
            level: 'warn',
            step: 'draft',
            message: `Reviewer discarded draft. Reason: "${reason || 'No reason provided'}". Issue will not be opened in GitHub.`,
          },
        ],
      };
      runs[idx] = updated;
      saveStoredRuns(runs);
      return toRunItem(updated);
    }

    const res = await fetch(`/api/runs/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error('Rejection failed');
    return res.json();
  },

  rerunTriage: async (id: string): Promise<any> => {
    if (USE_MOCK_API) {
      const runs = getStoredRuns();
      const idx = runs.findIndex((r) => r.id === id);
      if (idx === -1) throw new Error('Run not found');

      const updated: RunDetail = {
        ...runs[idx],
        status: 'draft_ready',
        updatedAt: new Date().toISOString(),
        logs: [
          ...runs[idx].logs,
          {
            ts: new Date().toLocaleTimeString(),
            level: 'info',
            step: 'gateway',
            message: 'Manual triage rerun triggered by reviewer.',
          },
        ],
      };
      runs[idx] = updated;
      saveStoredRuns(runs);
      return toRunItem(updated);
    }

    const res = await fetch(`/api/runs/${id}/rerun`, { method: 'POST' });
    if (!res.ok) throw new Error('Rerun failed');
    return res.json();
  },

  getHealth: async (): Promise<DependencyHealth[]> => {
    return DEFAULT_HEALTH;
  },

  pingHealth: async (key: string): Promise<DependencyHealth[]> => {
    return DEFAULT_HEALTH.map((h) =>
      h.key === key ? { ...h, last_check: 'Just now', latency_ms: Math.floor(25 + Math.random() * 50) } : h
    );
  },

  getSettings: async (): Promise<SystemSettings> => {
    if (typeof window === 'undefined') return DEFAULT_SETTINGS;
    try {
      const s = localStorage.getItem('ichnoscope_settings');
      return s ? JSON.parse(s) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  updateSettings: async (settings: SystemSettings): Promise<SystemSettings> => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('ichnoscope_settings', JSON.stringify(settings));
    }
    return settings;
  },

  isAuthenticated: (): boolean => {
    if (typeof window === 'undefined') return true;
    return document.cookie.includes('ichnoscope_admin_auth=true');
  },

  login: (password: string): boolean => {
    return password === 'ichnoscope' || password === 'admin';
  },

  logout: (): void => {
    if (typeof window !== 'undefined') {
      document.cookie = 'ichnoscope_admin_auth=; Max-Age=0; path=/;';
    }
  },

  replaySavedFixture: async (_fixture: string): Promise<any> => {
    const runs = getStoredRuns();
    const newRun = {
      ...runs[0],
      id: `run-${Date.now().toString(36)}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    runs.unshift(newRun);
    saveStoredRuns(runs);
    return toRunItem(newRun);
  },
};
