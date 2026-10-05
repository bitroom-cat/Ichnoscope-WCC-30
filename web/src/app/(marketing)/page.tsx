import * as React from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/primitives/Card';
import { ArrowRight, BookOpen, Layers, UserCheck, FileText, CheckCircle2, GitCommit, ShieldCheck } from 'lucide-react';

export default function MarketingHomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Background Grid & Soft Radial Glow */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(to_right,var(--border-subtle)_1px,transparent_1px),linear-gradient(to_bottom,var(--border-subtle)_1px,transparent_1px)] bg-[size:24px_24px] opacity-40"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 -z-10 w-[640px] h-[360px] rounded-full bg-accent-subtle blur-[100px] opacity-60"
        aria-hidden="true"
      />

      {/* 1. HERO SECTION */}
      <section className="pt-20 sm:pt-28 pb-16 sm:pb-24">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl space-y-6">
            {/* Eyebrow chip */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-subtle border border-accent/20 text-accent text-caption font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              <span>Read-only incident triage</span>
            </div>

            {/* H1 */}
            <h1 className="text-title-1 sm:text-5xl sm:leading-tight font-semibold text-primary tracking-tight">
              Every bug leaves footprints. Ichnoscope reads them.
            </h1>

            {/* Sub-copy */}
            <p className="text-subhead sm:text-title-3 text-text-secondary leading-relaxed max-w-2xl font-normal">
              When production breaks, Ichnoscope finds the commit behind the failing line, explains why it likely failed, and drafts the GitHub issue for you to approve.
            </p>

            {/* CTAs */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link href="/login">
                <Button variant="primary" size="lg">
                  <span>Open dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/docs">
                <Button variant="secondary" size="lg">
                  <BookOpen className="w-4 h-4" />
                  <span>Read the docs</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* DEMO VIDEO SHOWCASE */}
      <section className="pb-16 sm:pb-24 -mt-6">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative mx-auto max-w-5xl rounded-xl border border-border-subtle bg-surface/80 p-2 sm:p-4 shadow-2xl backdrop-blur-sm">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border-subtle mb-3">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-danger/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-warning/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-success/80 inline-block" />
                <span className="text-caption font-mono text-text-muted ml-2">ichnoscope-demo-walkthrough</span>
              </div>
              <span className="text-caption font-mono text-accent">Product Demo & Guide</span>
            </div>
            <div className="relative w-full aspect-video overflow-hidden rounded-lg bg-black">
              <iframe
                width="1059"
                height="595"
                src="https://www.youtube.com/embed/NsmXi0lnl7Y"
                title="ichnoscope"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerPolicy="strict-origin-when-cross-origin"
                allowFullScreen
                className="w-full h-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 2. THE PROBLEM STRIP */}
      <section className="py-16 border-t border-border-subtle bg-surface/50">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="space-y-1">
            <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted font-medium">
              Triage Bottlenecks
            </span>
            <h2 className="text-title-2 font-semibold text-primary tracking-tight">
              Why incident triage drains engineering hours
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <div className="w-9 h-9 rounded-sm bg-accent-subtle text-accent flex items-center justify-center mb-2">
                  <Layers className="w-4 h-4" />
                </div>
                <CardTitle>Context is scattered</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-dense text-text-secondary leading-relaxed">
                  Stack traces live in your monitoring tool, blame lives in git, and pull request discussion lives in GitHub. Reconstructing the trail takes 20 minutes before a ticket can even be written.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-9 h-9 rounded-sm bg-accent-subtle text-accent flex items-center justify-center mb-2">
                  <UserCheck className="w-4 h-4" />
                </div>
                <CardTitle>Ownership is guesswork</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-dense text-text-secondary leading-relaxed">
                  On-call engineers route by hunch or service directory. If the service directory is out of date, issues bounce between teams while users encounter the same exception.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-9 h-9 rounded-sm bg-accent-subtle text-accent flex items-center justify-center mb-2">
                  <FileText className="w-4 h-4" />
                </div>
                <CardTitle>Tickets arrive empty</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-dense text-text-secondary leading-relaxed">
                  Alert notifications contain only the error string. They have no hypothesis, no diff snippet, and no verification checklist for the engineer assigned to investigate.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* 3. HOW IT WORKS SUMMARY STRIP */}
      <section id="how-it-works" className="py-20 border-t border-border-subtle">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="space-y-1">
            <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted font-medium">
              Pipeline Architecture
            </span>
            <h2 className="text-title-2 font-semibold text-primary tracking-tight">
              Code gathers evidence. The LLM only explains it.
            </h2>
            <p className="text-body text-text-secondary max-w-xl">
              Deterministic git analysis pinpoints the commit in the deployed version. Language models synthesize the findings without write access.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                step: '01',
                title: 'Receive',
                desc: 'An error event arrives via webhook from your monitoring platform with stack trace and release metadata.',
                icon: <CheckCircle2 className="w-4 h-4 text-accent" />,
              },
              {
                step: '02',
                title: 'Blame',
                desc: 'The failing frame is traced to its commit at the deployed release SHA using GitHub blame.',
                icon: <GitCommit className="w-4 h-4 text-accent" />,
              },
              {
                step: '03',
                title: 'Explain',
                desc: 'An LLM analyzes the diff and exception evidence to synthesize a technical hypothesis and checklist.',
                icon: <Layers className="w-4 h-4 text-accent" />,
              },
              {
                step: '04',
                title: 'Review',
                desc: 'You inspect the drafted GitHub issue with suggested assignee and approve publication in one click.',
                icon: <ShieldCheck className="w-4 h-4 text-accent" />,
              },
            ].map((item) => (
              <div key={item.step} className="p-5 rounded-md bg-surface border border-border-subtle space-y-3">
                <div className="flex items-center justify-between text-caption font-mono text-text-muted">
                  <span>{item.step}</span>
                  {item.icon}
                </div>
                <div className="text-subhead font-semibold text-primary">{item.title}</div>
                <p className="text-dense text-text-secondary leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* CTA Band */}
          <div className="p-8 rounded-lg bg-surface border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="space-y-1">
              <h3 className="text-title-3 font-semibold text-primary">Ready to triage your first incident?</h3>
              <p className="text-dense text-text-secondary">Open the dashboard to explore sample error runs or connect your repository.</p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <Link href="/login">
                <Button variant="primary" size="md">
                  <span>Open dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
