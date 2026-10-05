'use client';

import React, { useState, useEffect } from 'react';
import { api, SystemSettings } from '@/lib/api';
import { Button } from '@/components/primitives/Button';
import {
  Settings,
  Save,
  Check,
  GitBranch,
  Cpu,
  Bell,
  Sliders,
  Send,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
} from 'lucide-react';

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [testingSlack, setTestingSlack] = useState(false);
  const [slackFeedback, setSlackFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showAdminToken, setShowAdminToken] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const s = await api.getSettings();
        setSettings(s);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    await api.updateSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleTestSlack = async () => {
    if (!settings) return;
    setTestingSlack(true);
    setSlackFeedback(null);
    try {
      const res = await api.testSlackWebhook(settings.slack_webhook_url);
      setSlackFeedback({ type: 'success', message: res.message || 'Test notification sent to Slack successfully!' });
    } catch (err: any) {
      setSlackFeedback({
        type: 'error',
        message: err.message || 'Failed to dispatch Slack test alert. Please verify your Webhook URL.',
      });
    } finally {
      setTestingSlack(false);
    }
  };

  if (loading || !settings) {
    return (
      <div className="py-20 text-center text-text-muted text-dense">
        Loading configuration...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
        <div>
          <h1 className="text-title-2 font-semibold text-primary tracking-tight flex items-center gap-2">
            <Settings className="w-5 h-5 text-accent" />
            Pipeline & Provider Settings
          </h1>
          <p className="text-dense text-secondary mt-1">
            Configure triage heuristics, severity thresholds, and model integrations.
          </p>
        </div>

        {saved && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-success-subtle border border-success/30 text-success text-caption font-medium animate-fadeIn">
            <Check className="w-4 h-4 text-success" />
            Configuration saved
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Section 1: GitHub */}
        <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs space-y-4">
          <div className="border-b border-border-subtle pb-3">
            <h2 className="text-dense font-semibold text-primary flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-accent" />
              Repository Scoping
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-dense">
            <div>
              <label className="text-secondary block font-medium mb-1">
                Target Repository (<code className="font-mono text-accent">GITHUB_REPOSITORY</code>)
              </label>
              <input
                type="text"
                value={settings.github_repo}
                onChange={(e) => setSettings({ ...settings, github_repo: e.target.value })}
                className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono focus:outline-none focus:border-accent"
              />
              <span className="text-caption text-text-muted mt-1 block">Format: owner/repo</span>
            </div>

            <div>
              <label className="text-secondary block font-medium mb-1">
                Fallback Assignee (<code className="font-mono text-accent">FALLBACK_ASSIGNEE</code>)
              </label>
              <input
                type="text"
                value={settings.fallback_assignee}
                onChange={(e) => setSettings({ ...settings, fallback_assignee: e.target.value })}
                className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono focus:outline-none focus:border-accent"
              />
              <span className="text-caption text-text-muted mt-1 block">Assigned if author is not in repo assignees</span>
            </div>

            <div>
              <label className="text-secondary block font-medium mb-1">
                Path Prefix Strip (<code className="font-mono text-accent">PATH_PREFIX_STRIP</code>)
              </label>
              <input
                type="text"
                value={settings.path_prefix_strip}
                onChange={(e) => setSettings({ ...settings, path_prefix_strip: e.target.value })}
                className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono focus:outline-none focus:border-accent"
              />
              <span className="text-caption text-text-muted mt-1 block">e.g. /app/ to convert container path to repo-relative</span>
            </div>

            <div>
              <label className="text-secondary block font-medium mb-1">
                Regression Window (<code className="font-mono text-accent">WINDOW_HOURS</code>)
              </label>
              <input
                type="number"
                value={settings.window_hours}
                onChange={(e) => setSettings({ ...settings, window_hours: Number(e.target.value) })}
                className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono focus:outline-none focus:border-accent"
              />
              <span className="text-caption text-text-muted mt-1 block">Hours since commit to mark as regression (default: 24h)</span>
            </div>
          </div>
        </div>

        {/* Section 2: Severity */}
        <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs space-y-4">
          <div className="border-b border-border-subtle pb-3">
            <h2 className="text-dense font-semibold text-primary flex items-center gap-2">
              <Sliders className="w-4 h-4 text-warning" />
              Deterministic Severity Rules
            </h2>
            <p className="text-caption text-secondary mt-0.5">
              Calculated strictly from event and user counts. The LLM never sets severity.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-dense">
            <div className="p-3 bg-canvas border border-border-subtle rounded-md space-y-1">
              <span className="font-semibold text-danger block">P1 Users</span>
              <input
                type="number"
                value={settings.p1_users}
                onChange={(e) => setSettings({ ...settings, p1_users: Number(e.target.value) })}
                className="w-full bg-surface border border-border-subtle rounded px-2 py-1 text-primary font-mono text-dense"
              />
              <span className="text-caption text-text-muted block">≥ 50 in prod</span>
            </div>

            <div className="p-3 bg-canvas border border-border-subtle rounded-md space-y-1">
              <span className="font-semibold text-danger block">P1 Events</span>
              <input
                type="number"
                value={settings.p1_events}
                onChange={(e) => setSettings({ ...settings, p1_events: Number(e.target.value) })}
                className="w-full bg-surface border border-border-subtle rounded px-2 py-1 text-primary font-mono text-dense"
              />
              <span className="text-caption text-text-muted block">≥ 100 in prod</span>
            </div>

            <div className="p-3 bg-canvas border border-border-subtle rounded-md space-y-1">
              <span className="font-semibold text-warning block">P2 Users</span>
              <input
                type="number"
                value={settings.p2_users}
                onChange={(e) => setSettings({ ...settings, p2_users: Number(e.target.value) })}
                className="w-full bg-surface border border-border-subtle rounded px-2 py-1 text-primary font-mono text-dense"
              />
              <span className="text-caption text-text-muted block">≥ 10 in prod</span>
            </div>

            <div className="p-3 bg-canvas border border-border-subtle rounded-md space-y-1">
              <span className="font-semibold text-warning block">P2 Events</span>
              <input
                type="number"
                value={settings.p2_events}
                onChange={(e) => setSettings({ ...settings, p2_events: Number(e.target.value) })}
                className="w-full bg-surface border border-border-subtle rounded px-2 py-1 text-primary font-mono text-dense"
              />
              <span className="text-caption text-text-muted block">≥ 20 in prod</span>
            </div>
          </div>
        </div>

        {/* Section 3: LLM */}
        <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs space-y-4">
          <div className="border-b border-border-subtle pb-3">
            <h2 className="text-dense font-semibold text-primary flex items-center gap-2">
              <Cpu className="w-4 h-4 text-accent" />
              LLM Explanation Provider
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-dense">
            <div>
              <label className="text-secondary block font-medium mb-1">
                Primary Model Provider
              </label>
              <select
                value={settings.llm_provider}
                onChange={(e) => setSettings({ ...settings, llm_provider: e.target.value as any })}
                className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono text-dense focus:outline-none focus:border-accent"
              >
                <option value="gemini-1.5-flash">Gemini 1.5 Flash (Structured Outputs)</option>
                <option value="groq-llama3">Groq (Llama-3-70B)</option>
                <option value="openrouter">OpenRouter (Free tier fallback)</option>
                <option value="pollinations">Pollinations API</option>
              </select>
              <span className="text-caption text-text-muted mt-1 block">
                Evidence context bounded to 4,096 tokens max.
              </span>
            </div>

            <div className="flex items-center gap-2 pt-6">
              <label className="flex items-center gap-2 cursor-pointer text-secondary">
                <input
                  type="checkbox"
                  checked={settings.dry_run}
                  onChange={(e) => setSettings({ ...settings, dry_run: e.target.checked })}
                  className="rounded border-border-subtle text-accent focus:ring-accent h-4 w-4"
                />
                <span className="text-dense font-medium">
                  Dry-run mode (<code className="font-mono text-accent">DRY_RUN=true</code>)
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Section 4: Notifications */}
        <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs space-y-5">
          <div className="border-b border-border-subtle pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-dense font-semibold text-primary flex items-center gap-2">
                <Bell className="w-4 h-4 text-success" />
                Slack Notifications & Webhook Dispatch
              </h2>
              <p className="text-caption text-secondary mt-0.5">
                Dispatch automated incident summaries to Slack channels when regressions are triaged.
              </p>
            </div>
            {settings.slack_webhook_url && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-caption font-medium bg-success-subtle text-success border border-success/20">
                <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                Webhook Configured
              </span>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-secondary block font-medium mb-1 text-dense">
                Slack Incoming Webhook URL (<code className="font-mono text-accent">SLACK_WEBHOOK_URL</code>)
              </label>
              <div className="flex flex-col sm:flex-row gap-2.5">
                <input
                  type="password"
                  value={settings.slack_webhook_url || ''}
                  onChange={(e) => setSettings({ ...settings, slack_webhook_url: e.target.value })}
                  placeholder="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
                  className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono text-dense focus:outline-none focus:border-accent"
                />
                <Button
                  type="button"
                  variant="secondary"
                  disabled={testingSlack || (!settings.slack_webhook_url && !settings.slack_enabled)}
                  onClick={handleTestSlack}
                  className="gap-2 whitespace-nowrap shrink-0"
                >
                  {testingSlack ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Testing Dispatch...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 text-accent" />
                      Send Test Alert
                    </>
                  )}
                </Button>
              </div>
              <span className="text-caption text-text-muted mt-1 block">
                Incoming webhook generated in your Slack workspace apps directory. Click &quot;Send Test Alert&quot; to verify live connectivity immediately.
              </span>
            </div>

            {slackFeedback && (
              <div
                className={`p-3.5 rounded-md border flex items-start gap-2.5 text-dense animate-fadeIn ${
                  slackFeedback.type === 'success'
                    ? 'bg-success-subtle/50 border-success/30 text-success'
                    : 'bg-danger-subtle/50 border-danger/30 text-danger'
                }`}
              >
                {slackFeedback.type === 'success' ? (
                  <Check className="w-4 h-4 text-success shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-danger shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="font-medium text-caption">
                    {slackFeedback.type === 'success' ? 'Alert Delivered' : 'Delivery Failed'}
                  </p>
                  <p className="text-caption opacity-90 mt-0.5">{slackFeedback.message}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-dense pt-1">
              <div>
                <label className="text-secondary block font-medium mb-1">
                  Slack Channel Name
                </label>
                <input
                  type="text"
                  value={settings.slack_channel}
                  onChange={(e) => setSettings({ ...settings, slack_channel: e.target.value })}
                  placeholder="#eng-incidents"
                  className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-primary font-mono focus:outline-none focus:border-accent"
                />
                <span className="text-caption text-text-muted mt-1 block">Default display channel name</span>
              </div>

              <div className="space-y-2.5 pt-2">
                <label className="flex items-center gap-2 cursor-pointer text-secondary">
                  <input
                    type="checkbox"
                    checked={settings.slack_enabled}
                    onChange={(e) => setSettings({ ...settings, slack_enabled: e.target.checked })}
                    className="rounded border-border-subtle text-accent focus:ring-accent h-4 w-4"
                  />
                  <span className="text-dense">Post triage summary to Slack automatically</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-secondary">
                  <input
                    type="checkbox"
                    checked={settings.auto_comment_duplicates}
                    onChange={(e) => setSettings({ ...settings, auto_comment_duplicates: e.target.checked })}
                    className="rounded border-border-subtle text-accent focus:ring-accent h-4 w-4"
                  />
                  <span className="text-dense">Suppress repeat events (max 1 comment per 15 min)</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Section 5: Security & Admin Authentication */}
        <div className="p-5 sm:p-6 rounded-lg border border-border-subtle bg-surface shadow-xs space-y-4">
          <div className="border-b border-border-subtle pb-3">
            <h2 className="text-dense font-semibold text-primary flex items-center gap-2">
              <Lock className="w-4 h-4 text-warning" />
              Security &amp; Admin Token
            </h2>
            <p className="text-caption text-secondary mt-0.5">
              Secure administrative operations, settings updates, and triage manual overrides.
            </p>
          </div>

          <div className="text-dense">
            <label className="text-secondary block font-medium mb-1">
              Admin Access Token (<code className="font-mono text-accent">ADMIN_TOKEN</code>)
            </label>
            <div className="relative max-w-lg">
              <input
                type={showAdminToken ? 'text' : 'password'}
                value={settings.admin_token || ''}
                onChange={(e) => setSettings({ ...settings, admin_token: e.target.value })}
                placeholder="ichnoscope-secret-admin-token"
                className="w-full bg-canvas border border-border-subtle rounded-md pl-3 pr-10 py-2 text-primary font-mono focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={() => setShowAdminToken(!showAdminToken)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-primary transition-colors"
                title={showAdminToken ? 'Hide token' : 'Show token'}
              >
                {showAdminToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <span className="text-caption text-text-muted mt-1.5 block">
              Set or rotate the authentication token used for API route authorization and administrative operations.
            </span>
          </div>
        </div>

        {/* Save Bar */}
        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="primary"
            className="gap-2"
          >
            <Save className="w-4 h-4" />
            Save Configuration
          </Button>
        </div>
      </form>
    </div>
  );
}
