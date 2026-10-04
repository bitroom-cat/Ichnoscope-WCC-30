import * as React from 'react';
import { MarketingHeader } from '@/components/marketing/MarketingHeader';
import { MarketingFooter } from '@/components/marketing/MarketingFooter';

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-canvas text-primary">
      <MarketingHeader />
      <div className="flex-1">
        {children}
      </div>
      <MarketingFooter />
    </div>
  );
}
