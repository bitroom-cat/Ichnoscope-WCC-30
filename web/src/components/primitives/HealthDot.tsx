'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface HealthDotProps {
  status: 'healthy' | 'degraded' | 'offline' | 'sleeping';
  size?: 'sm' | 'md';
  pulse?: boolean;
  className?: string;
}

export function HealthDot({
  status,
  size = 'md',
  pulse = true,
  className,
}: HealthDotProps) {
  const colorMap = {
    healthy: 'bg-success',
    degraded: 'bg-warning',
    offline: 'bg-danger',
    sleeping: 'bg-info',
  };

  return (
    <span className={cn('relative inline-flex items-center justify-center shrink-0', className)}>
      {pulse && status === 'healthy' && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-40 bg-success" />
      )}
      <span
        className={cn(
          'rounded-full',
          size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5',
          colorMap[status] || 'bg-text-muted'
        )}
      />
    </span>
  );
}
