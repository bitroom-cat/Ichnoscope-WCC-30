'use client';

import * as React from 'react';
import { useTheme } from 'next-themes';
import {
  Button,
  IconButton,
  Badge,
  StatusBadge,
  SeverityBadge,
  Chip,
  Input,
  Select,
  Switch,
  Tabs,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Avatar,
  Tooltip,
  Dialog,
  Toast,
  Skeleton,
  EmptyState,
  Sparkline,
  CopyField,
  CodeBlock,
  DiffView,
  Kbd,
  HealthDot,
  PipelineStepper,
  LogViewer,
  RunStatus,
  Severity,
} from '@/components/primitives';
import {
  computeContrastRatio,
  formatContrastRatio,
  CONTRAST_PAIRS,
  SURFACE_SWATCHES,
  ACCENT_SWATCH_META,
  type ContrastPair,
} from '@/lib/contrast';
import { Sun, Moon, Check, AlertTriangle, AlertCircle } from 'lucide-react';

export default function StyleguidePage() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('tokens');
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [switchState, setSwitchState] = React.useState(true);
  const [inputValue, setInputValue] = React.useState('services/checkout_service.py');
  const [chipFilter, setChipFilter] = React.useState<string>('all');
  const [computedRatios, setComputedRatios] = React.useState<Record<string, number>>({});

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Compute runtime contrast ratios by inspecting actual CSS variables in DOM
  React.useEffect(() => {
    if (!mounted) return;
    const isDark = resolvedTheme === 'dark';
    const computed: Record<string, number> = {};

    CONTRAST_PAIRS.forEach((pair) => {
      let fg = isDark ? pair.fgFallbackDark : pair.fgFallbackLight;
      let bg = isDark ? pair.bgFallbackDark : pair.bgFallbackLight;

      try {
        const root = document.documentElement;
        const style = getComputedStyle(root);
        const resolvedFg = style.getPropertyValue(pair.fgVar).trim();
        const resolvedBg = style.getPropertyValue(pair.bgVar).trim();
        if (resolvedFg && (resolvedFg.startsWith('#') || resolvedFg.startsWith('rgb'))) fg = resolvedFg;
        if (resolvedBg && (resolvedBg.startsWith('#') || resolvedBg.startsWith('rgb'))) bg = resolvedBg;
      } catch {
        // Fallback to exact token values
      }

      computed[pair.label] = computeContrastRatio(fg, bg);
    });

    setComputedRatios(computed);
  }, [mounted, resolvedTheme, theme]);

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  const sampleSparkline = [2, 5, 8, 3, 6, 12, 18, 24, 30, 42, 60, 45, 30, 15, 8, 4, 3, 2, 2, 5, 9, 14, 22, 38];

  const sampleDiff = `@@ -140,4 +140,6 @@ def process_cart_discounts(cart_context):
     if not cart_context.has_items():
         return None
-    return calculate_standard_discount(cart_context)
+    active_vouchers = cart_context.voucher_list
+    primary_tier = active_vouchers[0].tier_multiplier
+    return calculate_tiered_discount(cart_context, primary_tier)`;

  const sampleCode = `from ichnoscope.blame import find_culprit

def triage_event(incident: Incident) -> RunState:
    culprit = find_culprit(incident.release_sha, incident.file_path, incident.line_number)
    explanation = explain_with_llm(incident, culprit)
    severity = calculate_severity(incident.event_count, incident.users_affected)
    return stage_draft_issue(incident, culprit, explanation, severity)`;

  const sampleLogs = [
    { ts: '14:20:01.012', level: 'info' as const, step: 'gateway', message: 'Accepted Sentry webhook. Verified HMAC-SHA256 signature.' },
    { ts: '14:20:01.085', level: 'info' as const, step: 'dedupe', message: 'Generated fingerprint sha256(IndexError|services/checkout.py|142)[:12] -> e89c314b09f1.' },
    { ts: '14:20:01.320', level: 'info' as const, step: 'blame', message: 'Querying GitHub GraphQL blame at release SHA a89f30b91d29ec49.' },
    { ts: '14:20:01.890', level: 'info' as const, step: 'blame', message: 'Located suspect commit a89f30b by @alexparker in PR-144.' },
    { ts: '14:20:02.450', level: 'warn' as const, step: 'severity', message: 'Rated P1-Critical (production=True, users=67 >= 50, events=148 >= 100).' },
    { ts: '14:20:02.910', level: 'info' as const, step: 'draft', message: 'Prepared draft issue. Awaiting human sign-off.' },
  ];

  const sampleStepper = [
    { name: 'parse' as const, state: 'done' as const, ms: 45 },
    { name: 'blame' as const, state: 'done' as const, ms: 520 },
    { name: 'explain' as const, state: 'running' as const },
    { name: 'draft' as const, state: 'pending' as const },
    { name: 'publish' as const, state: 'pending' as const },
  ];

  if (!mounted) return null;

  const currentTheme = resolvedTheme || 'dark';

  return (
    <div className="min-h-screen bg-canvas text-primary">
      {/* Centered Page Container (max-w 1280px, equal left/right padding) */}
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Ichnoscope Design Foundation
              </span>
              <span className="px-2 py-0.5 rounded-sm text-caption font-mono bg-accent-subtle text-accent font-medium">
                Tokens & Primitives
              </span>
            </div>
            <h1 className="text-title-1 font-semibold text-primary tracking-tight">
              Design System & Component Styleguide
            </h1>
            <p className="text-body text-text-secondary">
              Strict visual verification surface for design tokens, primitive components, runtime WCAG contrast ratios, and theme switching.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="secondary" size="md" onClick={toggleTheme}>
              {currentTheme === 'dark' ? (
                <Sun className="w-3.5 h-3.5 text-warning" />
              ) : (
                <Moon className="w-3.5 h-3.5 text-info" />
              )}
              <span>Theme: {currentTheme === 'dark' ? 'Dark' : 'Light'}</span>
            </Button>

            <Button variant="primary" size="md" onClick={() => setDialogOpen(true)}>
              Open Bounded Dialog
            </Button>
          </div>
        </div>

        {/* Tab Navigation (with edge fade and hidden scrollbar) */}
        <Tabs
          activeTab={activeTab}
          onChange={setActiveTab}
          tabs={[
            { id: 'tokens', label: '1. Design Tokens & Contrast' },
            { id: 'buttons-badges', label: '2. Buttons & Badges' },
            { id: 'forms-cards', label: '3. Forms & Cards' },
            { id: 'data-table', label: '4. Table & Stepper' },
            { id: 'code-diff', label: '5. Diff & Logs' },
            { id: 'feedback', label: '6. Modals & Feedback' },
          ]}
        />

        {/* TAB 1: DESIGN TOKENS & CONTRAST RATIOS */}
        {activeTab === 'tokens' && (
          <div className="space-y-8">
            {/* Color Swatches Grid */}
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Surfaces & Background Tokens
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {SURFACE_SWATCHES.map((token) => (
                  <div key={token.name} className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                    <div className={`h-12 rounded border border-border-subtle ${token.class}`} />
                    <div>
                      <div className="text-dense font-medium text-primary">{token.label}</div>
                      <div className="text-caption text-text-muted font-mono">{token.name}</div>
                      <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? token.darkHex : token.lightHex}</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Accent Swatch - Correctly styled with text-on-accent */}
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Signature Accent & Semantic Status Swatches
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
                {/* Accent Swatch */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-accent text-on-accent border border-accent">
                    text-on-accent
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">Accent</div>
                    <div className="text-caption text-text-muted font-mono">--accent</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.accent.dark : ACCENT_SWATCH_META.accent.light}</div>
                  </div>
                </div>

                {/* Danger P1 */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-danger text-white border border-danger">
                    P1-Critical
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">Danger</div>
                    <div className="text-caption text-text-muted font-mono">--danger</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.danger.dark : ACCENT_SWATCH_META.danger.light}</div>
                  </div>
                </div>

                {/* Severity High P2 */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-severity-high text-white border border-severity-high">
                    P2-High
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">High</div>
                    <div className="text-caption text-text-muted font-mono">--severity-high</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.severityHigh.dark : ACCENT_SWATCH_META.severityHigh.light}</div>
                  </div>
                </div>

                {/* Warning P3 */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-warning text-white border border-warning">
                    P3-Medium
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">Warning</div>
                    <div className="text-caption text-text-muted font-mono">--warning</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.warning.dark : ACCENT_SWATCH_META.warning.light}</div>
                  </div>
                </div>

                {/* Success */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-success text-white border border-success">
                    Published
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">Success</div>
                    <div className="text-caption text-text-muted font-mono">--success</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.success.dark : ACCENT_SWATCH_META.success.light}</div>
                  </div>
                </div>

                {/* Draft Ready */}
                <div className="p-3 rounded bg-surface border border-border-subtle space-y-2">
                  <div className="h-11 rounded flex items-center justify-center font-mono text-caption font-semibold bg-draft text-white border border-draft">
                    Draft Ready
                  </div>
                  <div>
                    <div className="text-dense font-medium text-primary">Draft</div>
                    <div className="text-caption text-text-muted font-mono">--draft</div>
                    <div className="text-caption text-text-secondary font-mono">{currentTheme === 'dark' ? ACCENT_SWATCH_META.draft.dark : ACCENT_SWATCH_META.draft.light}</div>
                  </div>
                </div>
              </div>
            </section>

            {/* Computed Runtime WCAG 2.1 Contrast Ratios */}
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                  Runtime Computed WCAG Contrast Ratios ({currentTheme.toUpperCase()} THEME)
                </h2>
                <span className="text-caption text-text-muted font-mono">Target: ≥ 4.5:1 text, ≥ 3.0:1 UI</span>
              </div>
              <Card>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Pair Label</TableHead>
                      <TableHead>Foreground Variable</TableHead>
                      <TableHead>Background Variable</TableHead>
                      <TableHead>Target</TableHead>
                      <TableHead className="text-right">Computed Ratio</TableHead>
                      <TableHead className="text-right">WCAG AA Result</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {CONTRAST_PAIRS.map((pair) => {
                      const ratio = computedRatios[pair.label] || 4.5;
                      const passes = ratio >= pair.minRatio;

                      return (
                        <TableRow key={pair.label}>
                          <TableCell className="font-medium text-primary">{pair.label}</TableCell>
                          <TableCell className="font-mono text-caption text-text-secondary">{pair.fgVar}</TableCell>
                          <TableCell className="font-mono text-caption text-text-secondary">{pair.bgVar}</TableCell>
                          <TableCell className="font-mono text-caption text-text-muted">{pair.minRatio}:1</TableCell>
                          <TableCell className="text-right font-mono text-dense font-semibold tabular-nums">
                            {formatContrastRatio(ratio)}
                          </TableCell>
                          <TableCell className="text-right">
                            {passes ? (
                              <span className="inline-flex items-center gap-1 text-caption text-success font-semibold font-mono tabular-nums">
                                <Check className="w-3.5 h-3.5" /> {formatContrastRatio(ratio)}
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-caption text-danger font-bold font-mono tabular-nums">
                                <AlertCircle className="w-3.5 h-3.5" /> {formatContrastRatio(ratio)} (Fail &lt; {pair.minRatio}:1)
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </Card>
            </section>

            {/* Semantic Typography Scale */}
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Semantic Typography Scale (Restored Defaults + Named Tokens)
              </h2>
              <Card>
                <CardContent className="space-y-4">
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-title-1 font-semibold text-primary">text-title-1 (32px / 40px, weight 600)</span>
                    <code className="text-caption font-mono text-text-muted">text-title-1</code>
                  </div>
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-title-2 font-semibold text-primary">text-title-2 (24px / 32px, weight 600)</span>
                    <code className="text-caption font-mono text-text-muted">text-title-2</code>
                  </div>
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-title-3 font-semibold text-primary">text-title-3 (20px / 28px, weight 600)</span>
                    <code className="text-caption font-mono text-text-muted">text-title-3</code>
                  </div>
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-subhead font-medium text-primary">text-subhead (16px / 24px, weight 500)</span>
                    <code className="text-caption font-mono text-text-muted">text-subhead</code>
                  </div>
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-body text-primary">text-body (14px / 20px, weight 400) — Default body copy</span>
                    <code className="text-caption font-mono text-text-muted">text-body</code>
                  </div>
                  <div className="flex items-baseline justify-between border-b border-border-subtle pb-2">
                    <span className="text-dense font-mono tabular-nums text-primary">text-dense (13px / 18px) — Tables, code context, tabular numbers</span>
                    <code className="text-caption font-mono text-text-muted">text-dense</code>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                      text-caption (12px / 16px) — Section overlines (Inter, tracking 0.04em)
                    </span>
                    <code className="text-caption font-mono text-text-muted">text-caption</code>
                  </div>
                </CardContent>
              </Card>
            </section>
          </div>
        )}

        {/* TAB 2: BUTTONS & BADGES */}
        {activeTab === 'buttons-badges' && (
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Button Primitive Variants & States
              </h2>
              <Card>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <Button variant="primary" size="md">Primary</Button>
                    <Button variant="secondary" size="md">Secondary</Button>
                    <Button variant="ghost" size="md">Ghost</Button>
                    <Button variant="danger" size="md">Danger</Button>
                    <Button variant="draft" size="md">Draft Action</Button>
                    <Button variant="primary" size="md" loading>Loading</Button>
                    <Button variant="secondary" size="md" disabled>Disabled</Button>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-border-subtle">
                    <span className="text-caption font-mono text-text-muted mr-2">Size sm (h-7):</span>
                    <Button variant="primary" size="sm">Primary</Button>
                    <Button variant="secondary" size="sm">Secondary</Button>
                    <Button variant="ghost" size="sm">Ghost</Button>
                    <Button variant="danger" size="sm">Danger</Button>
                  </div>
                </CardContent>
              </Card>
            </section>

            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                  StatusBadge (All 9 Pipeline States)
                </h2>
                <span className="text-caption text-text-muted">Mandatory Icon + Label + Color</span>
              </div>
              <Card>
                <CardContent>
                  <div className="flex flex-wrap gap-2.5">
                    {(['received', 'parsing', 'blaming', 'explaining', 'draft_ready', 'published', 'rejected', 'suppressed', 'failed'] as RunStatus[]).map((st) => (
                      <StatusBadge key={st} status={st} />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                SeverityBadge (Deterministic Mapping)
              </h2>
              <Card>
                <CardContent>
                  <div className="flex flex-wrap gap-3">
                    {(['P1-Critical', 'P2-High', 'P3-Medium'] as Severity[]).map((sev) => (
                      <SeverityBadge key={sev} severity={sev} />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Filter Chips (Interactive with Tabular Counts)
              </h2>
              <Card>
                <CardContent className="flex flex-wrap gap-2">
                  <Chip active={chipFilter === 'all'} onClick={() => setChipFilter('all')} count={12}>
                    All runs
                  </Chip>
                  <Chip active={chipFilter === 'draft'} onClick={() => setChipFilter('draft')} variant="draft" count={3}>
                    Needs approval
                  </Chip>
                  <Chip active={chipFilter === 'p1'} onClick={() => setChipFilter('p1')} count={4}>
                    P1-Critical
                  </Chip>
                  <Chip active={chipFilter === 'published'} onClick={() => setChipFilter('published')} count={5}>
                    Published
                  </Chip>
                  <Chip active={chipFilter === 'failed'} onClick={() => setChipFilter('failed')} count={1}>
                    Failed
                  </Chip>
                </CardContent>
              </Card>
            </section>
          </div>
        )}

        {/* TAB 3: FORMS & CARDS */}
        {activeTab === 'forms-cards' && (
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Form Primitives (Input, Select, Switch)
              </h2>
              <Card>
                <CardContent className="space-y-4 max-w-xl">
                  <div>
                    <label className="text-dense font-medium text-primary block mb-1">Standard Input</label>
                    <Input value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="services/file.py..." />
                  </div>

                  <div>
                    <label className="text-dense font-medium text-primary block mb-1">Select Dropdown</label>
                    <Select defaultValue="gemini">
                      <option value="gemini">Gemini 1.5 Flash (Default)</option>
                      <option value="groq">Groq (Llama-3-70B)</option>
                      <option value="openrouter">OpenRouter (Free Tier)</option>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-border-subtle">
                    <div>
                      <span className="text-dense font-semibold text-primary block">Dry-Run Mode</span>
                      <span className="text-caption text-text-muted">Print drafted issues without publishing to GitHub</span>
                    </div>
                    <Switch checked={switchState} onCheckedChange={setSwitchState} id="dry-run-switch" />
                  </div>
                </CardContent>
              </Card>
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Card Structure & Surface Depth
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Service Telemetry</CardTitle>
                    <Badge variant="accent">Online</Badge>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <p className="text-dense">Dense surface container with 1px border depth. No soft gradient washes.</p>
                    <div className="flex items-center gap-2 pt-2">
                      <HealthDot status="healthy" />
                      <span className="text-caption font-mono text-primary">Sentry Gateway active</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Suspect Commit Meta</CardTitle>
                    <Avatar name="Alex Parker" login="alexparker" size="sm" />
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <CopyField value="a89f30b91d29ec49b168" label="commit: a89f30b" />
                    <p className="text-text-muted text-caption">Committed 2 hours ago (within 24h regression window)</p>
                  </CardContent>
                </Card>
              </div>
            </section>
          </div>
        )}

        {/* TAB 4: TABLE & PIPELINE STEPPER */}
        {activeTab === 'data-table' && (
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Pipeline Stepper (&quot;The Trace&quot; Signature Line Motif)
              </h2>
              <Card>
                <CardContent>
                  <PipelineStepper steps={sampleStepper} />
                </CardContent>
              </Card>
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Dense Issue Stream Table (3px Left Severity Edge)
              </h2>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-28">Status</TableHead>
                    <TableHead>Error & Location</TableHead>
                    <TableHead className="w-36">Suspect</TableHead>
                    <TableHead className="w-32">24h Timeline</TableHead>
                    <TableHead className="w-20 text-right">Age</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow severityEdge="P1-Critical" isDraftReady={true}>
                    <TableCell>
                      <StatusBadge status="draft_ready" />
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-primary text-dense">IndexError: list index out of range</div>
                      <div className="font-mono text-caption text-text-muted">services/checkout_service.py:142</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Avatar name="Alex Parker" login="alexparker" />
                        <span className="font-medium text-dense">@alexparker</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Sparkline data={sampleSparkline} color="var(--danger)" />
                        <span className="font-mono text-caption tabular-nums text-text-muted">148</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-caption text-text-muted">
                      12m ago
                    </TableCell>
                  </TableRow>

                  <TableRow severityEdge="P2-High">
                    <TableCell>
                      <StatusBadge status="published" />
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-primary text-dense">AttributeError: &apos;NoneType&apos; object</div>
                      <div className="font-mono text-caption text-text-muted">payments/subscription_sync.py:94</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Avatar name="Sarah Chen" login="sarahchen" />
                        <span className="font-medium text-dense">@sarahchen</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Sparkline data={[2, 1, 0, 4, 2, 8, 12, 10, 6, 2, 1, 0, 0, 0, 0, 1, 2, 3, 5, 8, 12, 16, 24, 38]} color="var(--severity-high)" />
                        <span className="font-mono text-caption tabular-nums text-text-muted">38</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-caption text-text-muted">
                      1h ago
                    </TableCell>
                  </TableRow>

                  <TableRow severityEdge="P3-Medium">
                    <TableCell>
                      <StatusBadge status="explaining" />
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-primary text-dense">TimeoutError: Connection timed out</div>
                      <div className="font-mono text-caption text-text-muted">core/db_pool.py:67</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Avatar name="Marcus Vasquez" login="m-vasquez" />
                        <span className="font-medium text-dense">@m-vasquez</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Sparkline data={[1, 1, 2, 1, 0, 0, 1, 2, 3, 1, 4, 6, 8, 12, 15, 20, 18, 12, 8, 5, 4, 3, 2, 1]} color="var(--warning)" />
                        <span className="font-mono text-caption tabular-nums text-text-muted">24</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-caption text-text-muted">
                      3h ago
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </section>
          </div>
        )}

        {/* TAB 5: DIFF & LOGS */}
        {activeTab === 'code-diff' && (
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                DiffView Primitive (Using exact --diff-add-bg & --diff-del-bg)
              </h2>
              <DiffView diff={sampleDiff} sha="a89f30b" message="feat(checkout): add promotional tier multipliers (PR-144)" />
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                CodeBlock Primitive (Line numbers & highlighted failing frame)
              </h2>
              <CodeBlock code={sampleCode} filename="ichnoscope/pipeline.py" highlightLine={4} />
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                LogViewer Primitive (Render-style with follow-tail, search, and download)
              </h2>
              <LogViewer logs={sampleLogs} />
            </section>
          </div>
        )}

        {/* TAB 6: MODALS & FEEDBACK */}
        {activeTab === 'feedback' && (
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Toast Notifications
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Toast type="success" title="Published Issue GH-145" message="Assigned to @alexparker in owner/repo." action={{ label: 'View on GitHub', onClick: () => {} }} />
                <Toast type="error" title="Pipeline Error" message="GitHub API rate limit exceeded. Retry in 14s." />
                <Toast type="info" title="Replay Fixture Completed" message="Parsed sentry-evt-99014 in 1.4s." />
              </div>
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                EmptyState Primitive (With &quot;The Trace&quot; Motif)
              </h2>
              <EmptyState
                title="No incident runs matching this filter"
                description="All production exceptions are currently acknowledged. You can simulate an incident from a saved fixture."
                actionLabel="Replay a fixture"
                onAction={() => alert('Replay clicked')}
              />
            </section>

            <section className="space-y-3">
              <h2 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted">
                Keyboard Shortcuts (Kbd Primitive)
              </h2>
              <Card>
                <CardContent className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-1.5"><Kbd>⌘</Kbd><Kbd>K</Kbd> <span className="text-dense text-text-secondary">Command palette</span></div>
                  <div className="flex items-center gap-1.5"><Kbd>j</Kbd><Kbd>k</Kbd> <span className="text-dense text-text-secondary">Navigate rows</span></div>
                  <div className="flex items-center gap-1.5"><Kbd>a</Kbd> <span className="text-dense text-text-secondary">Approve</span></div>
                  <div className="flex items-center gap-1.5"><Kbd>r</Kbd> <span className="text-dense text-text-secondary">Reject</span></div>
                  <div className="flex items-center gap-1.5"><Kbd>/</Kbd> <span className="text-dense text-text-secondary">Focus search</span></div>
                </CardContent>
              </Card>
            </section>
          </div>
        )}

        {/* Test Bounded Dialog */}
        <Dialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          title="Confirm Issue Publication"
          description="Review target repository and assignee before dispatching to GitHub."
        >
          <div className="space-y-3">
            <p className="text-body text-secondary">
              This will publish an issue to <code className="font-mono text-accent font-semibold">ichnoscope/wcc-demo-service</code> with labels <code className="font-mono text-primary">[ichnoscope, P1-Critical, backend]</code> and assign to <code className="font-mono text-primary">@alexparker</code>.
            </p>
            <div className="p-3 rounded bg-inset border border-border-subtle text-caption font-mono text-text-muted">
              Fingerprint: e89c314b09f1 • Release SHA: a89f30b91d29ec49
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-border-subtle">
              <Button variant="secondary" size="sm" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={() => { alert('Published!'); setDialogOpen(false); }}>
                Confirm & Publish
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </div>
  );
}
