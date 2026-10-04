import * as React from 'react';
import Link from 'next/link';
import { ArrowLeft, BookOpen, Terminal, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/primitives/Button';
import { CodeBlock } from '@/components/primitives/CodeBlock';

export default function DocsSlugPage({ params }: { params: { slug: string } }) {
  const slug = params.slug || 'quickstart';

  const quickstartSample = `# 1. Clone repository & install dependencies
git clone https://github.com/ichnoscope/ichnoscope.git
cd ichnoscope
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Replay a sample production incident with zero network calls
python -m ichnoscope.replay fixtures/payment_index_error.json --dry-run`;

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sidebar Nav */}
        <aside className="md:col-span-1 space-y-6 border-b md:border-b-0 md:border-r border-border-subtle pb-6 md:pb-0 md:pr-6">
          <div className="space-y-1">
            <span className="text-caption font-sans uppercase tracking-[0.04em] text-text-muted font-medium">
              Documentation
            </span>
            <div className="text-subhead font-semibold text-primary">Getting Started</div>
          </div>
          <nav className="space-y-1">
            {[
              { title: 'Quickstart', href: '/docs/quickstart', active: slug === 'quickstart' },
              { title: 'How it works', href: '/docs/how-it-works', active: slug === 'how-it-works' },
              { title: 'Connect Sentry', href: '/docs/connect-sentry', active: slug === 'connect-sentry' },
              { title: 'GitHub PAT scope', href: '/docs/github-token', active: slug === 'github-token' },
              { title: 'Configuration', href: '/docs/configuration', active: slug === 'configuration' },
            ].map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className={`block px-3 py-2 text-dense rounded-sm transition-colors ${
                  item.active
                    ? 'bg-accent-subtle text-accent font-semibold'
                    : 'text-text-secondary hover:text-primary hover:bg-hover'
                }`}
              >
                {item.title}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Content Column */}
        <div className="md:col-span-3 max-w-[720px] space-y-8">
          <div className="space-y-2 border-b border-border-subtle pb-6">
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm bg-accent-subtle text-accent text-caption font-mono font-medium">
              <Terminal className="w-3.5 h-3.5" />
              <span>docs/{slug}</span>
            </div>
            <h1 className="text-title-1 font-semibold text-primary tracking-tight">
              {slug === 'quickstart' ? 'Quickstart Guide' : `Documentation: ${slug}`}
            </h1>
            <p className="text-body text-text-secondary leading-relaxed">
              Set up Ichnoscope locally, configure your monitoring webhook, and test incident triage in dry-run mode.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-title-3 font-semibold text-primary">1. Clone & Replay Fixture</h2>
            <p className="text-dense text-text-secondary leading-relaxed">
              Verify your local Python and Node environments by replaying a bundled production error fixture. This runs the full pipeline with no live GitHub or Sentry credentials required.
            </p>
            <CodeBlock code={quickstartSample} language="bash" />
          </div>

          <div className="p-4 rounded-md bg-surface border border-border-subtle space-y-2">
            <div className="flex items-center gap-2 text-subhead font-semibold text-primary">
              <CheckCircle2 className="w-4 h-4 text-accent" />
              <span>Read-only Safety Principle</span>
            </div>
            <p className="text-dense text-text-secondary leading-relaxed">
              Ichnoscope only reads git history and drafts issues for human approval. It never pushes commits, modifies branches, or initiates automated rollbacks.
            </p>
          </div>

          <div className="pt-4 flex items-center gap-3">
            <Link href="/login">
              <Button variant="primary" size="md">
                Open dashboard
              </Button>
            </Link>
            <Link href="/">
              <Button variant="secondary" size="md">
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
