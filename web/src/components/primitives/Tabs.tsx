'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    let nextIndex = currentIndex;
    if (e.key === 'ArrowRight') {
      nextIndex = (currentIndex + 1) % tabs.length;
      e.preventDefault();
    } else if (e.key === 'ArrowLeft') {
      nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      e.preventDefault();
    } else if (e.key === 'Home') {
      nextIndex = 0;
      e.preventDefault();
    } else if (e.key === 'End') {
      nextIndex = tabs.length - 1;
      e.preventDefault();
    } else {
      return;
    }

    const nextTab = tabs[nextIndex];
    if (nextTab) {
      onChange(nextTab.id);
      const buttons = containerRef.current?.querySelectorAll<HTMLButtonElement>('button[role="tab"]');
      buttons?.[nextIndex]?.focus();
    }
  };

  return (
    <div className={cn('relative w-full border-b border-border-subtle group', className)}>
      {/* Edge Fades for overflow indicator */}
      <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-canvas to-transparent z-10 opacity-70" />

      {/* Tabs list with hidden scrollbar */}
      <div
        ref={containerRef}
        role="tablist"
        aria-orientation="horizontal"
        className="flex items-center gap-1 overflow-x-auto no-scrollbar scroll-smooth pr-6"
      >
        {tabs.map((tab, idx) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              tabIndex={isActive ? 0 : -1}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              onClick={() => onChange(tab.id)}
              className={cn(
                'inline-flex items-center gap-2 px-3.5 py-2.5 text-caption font-medium border-b-2 -mb-px transition-colors duration-normal select-none whitespace-nowrap shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:rounded-xs',
                isActive
                  ? 'border-accent text-accent font-semibold'
                  : 'border-transparent text-secondary hover:text-primary hover:border-border-strong'
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={cn(
                    'px-1.5 py-0.2 rounded-full text-caption font-mono tabular-nums',
                    isActive ? 'bg-accent/20 text-accent font-semibold' : 'bg-hover text-text-muted'
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
