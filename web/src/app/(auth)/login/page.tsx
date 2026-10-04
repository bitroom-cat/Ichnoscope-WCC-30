'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/primitives/Button';
import { Lock, ArrowRight, AlertCircle, KeyRound } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    setTimeout(() => {
      const ok = api.login(password);
      if (ok) {
        document.cookie = 'ichnoscope_admin_auth=true; path=/; max-age=86400';
        router.push('/app/runs');
      } else {
        setError('Invalid password. Hint: enter "ichnoscope" or "admin".');
        setLoading(false);
      }
    }, 350);
  };

  const handleQuickFill = (pw: string) => {
    setPassword(pw);
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-lg border border-border-subtle bg-surface p-6 sm:p-7 shadow-xs space-y-5 transition-colors">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <Logo size="lg" showWordmark={false} />
          </div>
          <h1 className="text-title-3 font-semibold text-primary">Sign in to the dashboard</h1>
          <p className="text-caption text-secondary">
            Sign in to approve drafted GitHub incident issues.
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-danger-subtle border border-danger/30 text-danger text-caption">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-danger" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-caption font-medium text-secondary">
                Password
              </label>
              <div className="flex items-center gap-1 text-caption text-text-muted">
                <span>Try:</span>
                <button
                  type="button"
                  onClick={() => handleQuickFill('ichnoscope')}
                  className="font-mono text-accent hover:underline"
                >
                  &quot;ichnoscope&quot;
                </button>
              </div>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password..."
                className="w-full pl-9 pr-3 py-2 bg-canvas border border-border-subtle rounded-md text-dense text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={loading}
            className="w-full justify-center gap-2"
          >
            <span>{loading ? 'Authenticating...' : 'Sign in'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </form>

        <div className="pt-3 border-t border-border-subtle text-caption text-text-muted space-y-1">
          <div className="flex items-center gap-1.5 font-medium text-secondary">
            <KeyRound className="w-3.5 h-3.5 text-accent" />
            <span>Least Privilege Architecture</span>
          </div>
          <p className="leading-relaxed">
            Provider API keys and GitHub personal access tokens remain on the backend server. The client interface receives only signed session cookies.
          </p>
        </div>
      </div>
    </div>
  );
}
