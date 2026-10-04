'use client';

import React, { useState } from 'react';
import { DependencyHealth } from '@/lib/api';
import { HealthDot } from '@/components/primitives/HealthDot';
import { CheckCircle2, AlertTriangle, XCircle, Moon, Activity, RefreshCw } from 'lucide-react';

interface HealthCardProps {
  health: DependencyHealth;
  onPing: (key: string) => Promise<void>;
}

export function HealthCard({ health, onPing }: HealthCardProps) {
  const [pinging, setPinging] = useState(false);

  const handlePing = async () => {
    setPinging(true);
    try {
      await onPing(health.key);
    } finally {
      setPinging(false);
    }
  };

  const statusConfigMap: Record<string, { badge: string; icon: React.ReactNode; label: string; dotStatus: 'healthy' | 'degraded' | 'offline' | 'sleeping' }> = {
    healthy: {
      badge: 'bg-success-subtle text-success border-success/30',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-success" />,
      label: 'Operational',
      dotStatus: 'healthy',
    },
    degraded: {
      badge: 'bg-warning-subtle text-warning border-warning/30',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-warning" />,
      label: 'Degraded',
      dotStatus: 'degraded',
    },
    offline: {
      badge: 'bg-danger-subtle text-danger border-danger/30',
      icon: <XCircle className="w-3.5 h-3.5 text-danger" />,
      label: 'Offline',
      dotStatus: 'offline',
    },
    sleeping: {
      badge: 'bg-surface text-secondary border-border-subtle',
      icon: <Moon className="w-3.5 h-3.5 text-secondary" />,
      label: 'Standby',
      dotStatus: 'sleeping',
    },
  };

  const statusConfig = statusConfigMap[health.status] || {
    badge: 'bg-surface text-secondary border-border-subtle',
    icon: <Activity className="w-3.5 h-3.5 text-text-muted" />,
    label: health.status,
    dotStatus: 'sleeping' as const,
  };

  return (
    <div className="rounded-lg border border-border-subtle bg-surface p-4 sm:p-5 transition-colors hover:border-border-strong">
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <HealthDot status={statusConfig.dotStatus} size="sm" />
            <h3 className="font-semibold text-primary text-dense">{health.name}</h3>
          </div>
          <p className="text-caption text-secondary leading-relaxed">{health.details}</p>
        </div>

        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-sm text-caption font-mono border ${statusConfig.badge}`}>
          {statusConfig.icon}
          {statusConfig.label}
        </span>
      </div>

      {health.meta && (
        <div className="mt-3.5 pt-3 border-t border-border-subtle grid grid-cols-1 sm:grid-cols-2 gap-2 text-caption">
          {Object.entries(health.meta).map(([key, value]) => (
            <div
              key={key}
              className="bg-canvas rounded-sm px-2.5 py-1.5 border border-border-subtle"
            >
              <span className="text-text-muted block text-caption uppercase font-mono">{key}</span>
              <span className="text-primary font-medium font-mono text-caption truncate block" title={String(value)}>
                {String(value)}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3.5 pt-3 border-t border-border-subtle flex items-center justify-between text-caption">
        <div className="flex items-center gap-2 text-text-muted font-mono text-caption">
          <span>Latency: <strong className="text-primary">{health.latency_ms}ms</strong></span>
          <span>•</span>
          <span>Checked {health.last_check}</span>
        </div>

        <button
          onClick={handlePing}
          disabled={pinging}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm bg-surface text-secondary hover:text-primary hover:bg-canvas text-caption font-medium border border-border-subtle transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${pinging ? 'animate-spin text-accent' : ''}`} />
          <span>{pinging ? 'Checking...' : 'Probe'}</span>
        </button>
      </div>
    </div>
  );
}
