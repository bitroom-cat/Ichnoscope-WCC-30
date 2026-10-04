'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface KbdProps extends React.HTMLAttributes<HTMLElement> {}

export function Kbd({ className, children, ...props }: KbdProps) {
  return (
    <kbd
      className={cn(
        'inline-flex items-center justify-center px-1.5 py-0.5 rounded-sm bg-elevated text-text-secondary border border-border-strong text-caption font-mono shadow-xs select-none min-w-[20px] text-center',
        className
      )}
      {...props}
    >
      {children}
    </kbd>
  );
}
