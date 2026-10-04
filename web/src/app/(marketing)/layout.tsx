import * as React from 'react';
import { MarketingHeader } from '@/components/marketing/MarketingHeader';
import { MarketingFooter } from '@/components/marketing/MarketingFooter';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-canvas text-primary">
      {/* Accessible skip link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-3.5 focus:py-1.5 focus:bg-surface focus:border focus:border-border-strong focus:rounded-xs focus:text-dense focus:font-medium focus:text-primary focus:shadow-popover"
      >
        Skip to main content
      </a>

      <MarketingHeader />

      <main id="main-content" className="flex-1">
        {children}
      </main>

      <MarketingFooter />
    </div>
  );
}
