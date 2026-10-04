import * as React from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/Button';
import { ArrowLeft, BookOpen, Compass } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-canvas text-primary flex flex-col items-center justify-center p-6 text-center">
      {/* Background trace line watermark motif */}
      <div className="relative max-w-md w-full p-8 rounded-lg bg-surface border border-border-subtle shadow-popover space-y-6">
        {/* Footprint trace badge */}
        <div className="mx-auto w-14 h-14 rounded-full bg-accent-subtle border border-accent/20 flex items-center justify-center text-accent">
          <Compass className="w-7 h-7 animate-pulse" />
        </div>

        <div className="space-y-2">
          <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted font-medium">
            404 — Trace Missing
          </span>
          <h1 className="text-title-1 font-semibold text-primary tracking-tight">
            No footprints here.
          </h1>
          <p className="text-body text-text-secondary leading-relaxed">
            The path you requested leaves no trace in version history. It may have been moved or never committed.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/" className="w-full sm:w-auto">
            <Button variant="primary" size="md" className="w-full sm:w-auto">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Home</span>
            </Button>
          </Link>
          <Link href="/docs" className="w-full sm:w-auto">
            <Button variant="secondary" size="md" className="w-full sm:w-auto">
              <BookOpen className="w-4 h-4" />
              <span>Read the Docs</span>
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
