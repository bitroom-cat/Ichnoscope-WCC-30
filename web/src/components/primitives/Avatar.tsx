'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface AvatarProps {
  name: string;
  login?: string | null;
  size?: 'sm' | 'md';
  className?: string;
}

export function Avatar({ name, login, size = 'sm', className }: AvatarProps) {
  const initials = (login || name || '??')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div
      title={login ? `@${login} (${name})` : name}
      className={cn(
        'inline-flex items-center justify-center rounded-full bg-elevated text-secondary border border-border-strong font-mono font-medium select-none shrink-0',
        size === 'sm' ? 'w-5.5 h-5.5 text-caption' : 'w-7 h-7 text-caption',
        className
      )}
    >
      <span>{initials}</span>
    </div>
  );
}
