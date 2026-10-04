'use client';

import * as React from 'react';
import Link from 'next/link';
import { Logo } from '@/components/Logo';
import { useTheme } from '@/components/ThemeProvider';
import { Sun, Moon } from 'lucide-react';

export function MarketingFooter() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const columns = [
    {
      title: 'Product',
      links: [
        { label: 'How it works', href: '/#how-it-works' },
        { label: 'Live run sample', href: '/#live-run' },
        { label: 'Architecture', href: '/#architecture' },
        { label: 'Comparison', href: '/#comparison' },
      ],
    },
    {
      title: 'Docs',
      links: [
        { label: 'Quickstart', href: '/docs' },
        { label: 'Connect Sentry', href: '/docs' },
        { label: 'GitHub PAT scope', href: '/docs' },
        { label: 'Configuration', href: '/docs' },
      ],
    },
    {
      title: 'Company',
      links: [
        { label: 'About Ichnoscope', href: '/about' },
        { label: 'Security & Privacy', href: '/security' },
        { label: 'Principles', href: '/about#principles' },
        { label: 'GitHub Repository', href: 'https://github.com/ichnoscope/ichnoscope' },
      ],
    },
    {
      title: 'Legal',
      links: [
        { label: 'Read-only Guarantee', href: '/security' },
        { label: 'Privacy Principles', href: '/security#privacy' },
        { label: 'License (MIT)', href: 'https://github.com/ichnoscope/ichnoscope' },
        { label: 'Security Advisory', href: '/security#advisory' },
      ],
    },
  ];

  return (
    <footer className="w-full bg-canvas border-t border-border-subtle pt-16 pb-12 transition-colors">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Top Section: Brand + Columns */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand info column */}
          <div className="col-span-2 space-y-4">
            <Logo href="/" />
            <p className="text-dense text-text-secondary max-w-sm leading-relaxed">
              Read-only incident triage that finds the commit behind the failing line, explains it with an LLM, and drafts the GitHub issue for human review.
            </p>
            <div className="pt-1 flex items-center gap-3">
              {mounted && (
                <button
                  type="button"
                  onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                  className="inline-flex items-center gap-2 px-2.5 py-1 rounded-sm bg-surface border border-border-subtle text-caption text-text-secondary hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
                  aria-label="Toggle visual theme"
                >
                  {resolvedTheme === 'dark' ? (
                    <>
                      <Sun className="w-3.5 h-3.5 text-warning" />
                      <span>Theme: Dark</span>
                    </>
                  ) : (
                    <>
                      <Moon className="w-3.5 h-3.5 text-info" />
                      <span>Theme: Light</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* 4 Link columns */}
          {columns.map((col) => (
            <div key={col.title} className="space-y-3">
              <h3 className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted font-semibold">
                {col.title}
              </h3>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith('http') ? (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noreferrer"
                        className="text-caption text-text-secondary hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
                      >
                        {link.label}
                      </a>
                    ) : (
                      <Link
                        href={link.href}
                        className="text-caption text-text-secondary hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section: Name story & Launchpad credit */}
        <div className="pt-8 border-t border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-caption text-text-muted">
          <p className="max-w-xl">
            <span className="font-semibold text-text-secondary">Name origin:</span> <em>ichnos</em> is Greek for &ldquo;footprint&rdquo;; every failure leaves a trace in version history, and Ichnoscope reads it.
          </p>
          <div className="flex items-center gap-4">
            <span>Built for WCC Launchpad 30</span>
            <span>•</span>
            <span>MIT License</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
