import * as React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export interface LogoProps {
  className?: string;
  href?: string;
  showWordmark?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function Logo({ className, href = '/', showWordmark = true, size = 'md' }: LogoProps) {
  const iconSizeClass = size === 'lg' ? 'w-9 h-9' : size === 'sm' ? 'w-6 h-6' : 'w-7 h-7';
  const svgSizeClass = size === 'lg' ? 'w-5 h-5' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  const content = (
    <span className={cn('inline-flex items-center gap-2.5 select-none group', className)}>
      <span
        className={cn(
          'relative flex items-center justify-center rounded-sm bg-accent-subtle text-accent border border-accent/20 group-hover:border-accent/40 transition-colors',
          iconSizeClass
        )}
      >
        {/* Footprint trace mark: geometric trackway node + trace vector */}
        <svg
          className={svgSizeClass}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {/* Subtle trace trajectory */}
          <path d="M4 19C7 16 10 17 12 12C14 7 17 8 20 5" strokeDasharray="2 2" className="opacity-40" />
          {/* Main footprint heel and ball pads */}
          <ellipse cx="12" cy="15" rx="3.5" ry="4.5" />
          <circle cx="10" cy="8" r="1" fill="currentColor" />
          <circle cx="12.5" cy="7.5" r="1.1" fill="currentColor" />
          <circle cx="15" cy="8" r="1" fill="currentColor" />
          <circle cx="8" cy="9.5" r="0.8" fill="currentColor" />
          <circle cx="17" cy="9.5" r="0.8" fill="currentColor" />
        </svg>
      </span>
      {showWordmark && (
        <span className="text-subhead font-semibold tracking-tight text-primary">
          Ichnoscope
        </span>
      )}
    </span>
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:rounded-xs">
        {content}
      </Link>
    );
  }

  return content;
}
