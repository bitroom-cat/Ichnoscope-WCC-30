'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/primitives/Button';
import { useTheme } from '@/components/ThemeProvider';
import { Sun, Moon, Menu, X, Github, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function MarketingHeader() {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);
  const sheetRef = React.useRef<HTMLDivElement>(null);
  const triggerRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Close mobile menu on route change
  React.useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Focus trap and escape key for mobile sheet
  React.useEffect(() => {
    if (!mobileMenuOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMobileMenuOpen(false);
        triggerRef.current?.focus();
      }
      if (e.key === 'Tab' && sheetRef.current) {
        const focusable = sheetRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          last.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen]);

  const navLinks = [
    { label: 'Product', href: '/#how-it-works' },
    { label: 'Docs', href: '/docs' },
    { label: 'Security', href: '/security' },
    { label: 'About', href: '/about' },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full h-14 bg-canvas/80 backdrop-blur-md border-b border-border-subtle transition-colors">
        <div className="max-w-[1280px] h-full mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <div className="flex items-center gap-6">
            <Logo href="/" />

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Main Navigation">
              {navLinks.map((link) => {
                const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.label}
                    href={link.href}
                    className={cn(
                      'px-3 py-1.5 text-dense font-medium rounded-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring',
                      isActive
                        ? 'text-primary font-semibold'
                        : 'text-text-secondary hover:text-primary hover:bg-hover'
                    )}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Desktop Right Actions */}
          <div className="hidden md:flex items-center gap-2.5">
            {/* GitHub External Link */}
            <a
              href="https://github.com/ichnoscope/ichnoscope"
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded-sm text-text-secondary hover:text-primary hover:bg-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
              aria-label="GitHub Repository"
            >
              <Github className="w-4 h-4" />
            </a>

            {/* Theme Toggle */}
            {mounted && (
              <button
                type="button"
                onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                className="p-1.5 rounded-sm text-text-secondary hover:text-primary hover:bg-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
                aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              >
                {resolvedTheme === 'dark' ? <Sun className="w-4 h-4 text-warning" /> : <Moon className="w-4 h-4 text-info" />}
              </button>
            )}

            {/* Open Dashboard CTA */}
            <Link href="/login">
              <Button variant="primary" size="sm" className="ml-1.5">
                <span>Open dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>

          {/* Mobile Right Controls */}
          <div className="flex md:hidden items-center gap-2">
            <Link href="/login">
              <Button variant="primary" size="sm">
                Dashboard
              </Button>
            </Link>

            <button
              ref={triggerRef}
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-sm text-primary hover:bg-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav-sheet"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer Sheet */}
      {mobileMenuOpen && (
        <div
          id="mobile-nav-sheet"
          ref={sheetRef}
          role="dialog"
          aria-modal="true"
          aria-label="Mobile Navigation"
          className="fixed inset-x-0 top-14 bottom-0 z-40 bg-canvas/95 backdrop-blur-md border-b border-border-subtle p-6 flex flex-col justify-between md:hidden animate-fadeIn"
        >
          <div className="space-y-4">
            <nav className="flex flex-col space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  className="px-3 py-2.5 text-subhead font-medium text-primary hover:bg-hover rounded-sm transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <a
                href="https://github.com/ichnoscope/ichnoscope"
                target="_blank"
                rel="noreferrer"
                className="px-3 py-2.5 text-subhead font-medium text-primary hover:bg-hover rounded-sm transition-colors flex items-center justify-between"
              >
                <span>GitHub Source</span>
                <Github className="w-4 h-4 text-text-muted" />
              </a>
            </nav>
          </div>

          <div className="pt-6 border-t border-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-2 text-caption text-text-muted">
              <span>Theme:</span>
              {mounted && (
                <button
                  type="button"
                  onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                  className="px-2.5 py-1 rounded-sm bg-surface border border-border-subtle text-primary font-medium text-caption flex items-center gap-1.5"
                >
                  {resolvedTheme === 'dark' ? (
                    <>
                      <Sun className="w-3.5 h-3.5 text-warning" /> Dark
                    </>
                  ) : (
                    <>
                      <Moon className="w-3.5 h-3.5 text-info" /> Light
                    </>
                  )}
                </button>
              )}
            </div>
            <Link href="/login">
              <Button variant="primary" size="sm">
                Open dashboard
              </Button>
            </Link>
          </div>
        </div>
      )}
    </>
  );
}
