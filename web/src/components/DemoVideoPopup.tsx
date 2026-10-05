'use client';

import * as React from 'react';
import { Play, ExternalLink, X, Video, BookOpen, ChevronUp } from 'lucide-react';

export function DemoVideoPopup() {
  const [mounted, setMounted] = React.useState(false);
  const [isOpen, setIsOpen] = React.useState(true);
  const [showModal, setShowModal] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    // Optional: check session storage if closed previously in same session
    const dismissed = sessionStorage.getItem('ichnoscope_demo_popup_dismissed');
    if (dismissed === 'true') {
      setIsOpen(false);
    }
  }, []);

  const handleDismiss = () => {
    setIsOpen(false);
    sessionStorage.setItem('ichnoscope_demo_popup_dismissed', 'true');
  };

  const handleOpenModal = () => {
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  if (!mounted) return null;

  return (
    <>
      {/* 1. FLOATING MINIMIZED PILL (when card is dismissed/collapsed) */}
      {!isOpen && !showModal && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-5 right-5 z-40 inline-flex items-center gap-2.5 px-3.5 py-2 rounded-full bg-surface border border-accent/40 text-primary shadow-xl hover:bg-hover hover:border-accent transition-all duration-200 group active:scale-95"
          aria-label="Open Demo Guide"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent"></span>
          </span>
          <span className="text-dense font-medium flex items-center gap-1.5">
            <Video className="w-3.5 h-3.5 text-accent" />
            <span>Guide & Demo Video</span>
          </span>
          <ChevronUp className="w-3.5 h-3.5 text-text-muted group-hover:text-primary transition-colors" />
        </button>
      )}

      {/* 2. FLOATING GUIDE & DEMO POPUP CARD */}
      {isOpen && !showModal && (
        <div
          role="dialog"
          aria-label="Demo Video & Guide Popup"
          className="fixed bottom-5 right-5 z-40 w-[92vw] sm:w-[380px] rounded-xl bg-surface/95 backdrop-blur-md border border-accent/30 p-4 shadow-2xl transition-all duration-300 animate-in fade-in slide-in-from-bottom-5"
        >
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 text-accent flex items-center justify-center shrink-0">
                <Video className="w-4 h-4 text-accent" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-dense font-semibold text-primary">Website Guide & Demo</h4>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium uppercase bg-accent-subtle text-accent border border-accent/20">
                    Live
                  </span>
                </div>
                <p className="text-[11px] text-text-muted">Ichnoscope Incident Triage Walkthrough</p>
              </div>
            </div>

            <button
              onClick={handleDismiss}
              className="text-text-muted hover:text-primary p-1 rounded hover:bg-surface-elevated transition-colors"
              title="Minimize guide popup"
              aria-label="Minimize popup"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body message */}
          <p className="mt-3 text-dense text-text-secondary leading-relaxed">
            Welcome to Ichnoscope! Watch our quick product walkthrough video to explore how automated incident triage connects Sentry errors to GitHub blame at the release commit.
          </p>

          {/* Action buttons */}
          <div className="mt-4 pt-3 border-t border-border-subtle flex items-center gap-2">
            <button
              onClick={handleOpenModal}
              className="flex-1 inline-flex items-center justify-center gap-1.5 h-8 px-3 rounded-md bg-accent text-accent-foreground text-caption font-medium hover:bg-accent-hover transition-colors shadow-xs active:scale-[0.98]"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Watch Video</span>
            </button>

            <a
              href="https://www.youtube.com/watch?v=NsmXi0lnl7Y"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1.5 h-8 px-2.5 rounded-md bg-surface text-text-secondary border border-border-subtle hover:text-primary hover:bg-hover text-caption font-medium transition-colors"
              title="Open video on YouTube"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>YouTube</span>
            </a>

            <button
              onClick={handleDismiss}
              className="h-8 px-2.5 rounded-md text-text-muted hover:text-primary hover:bg-hover text-caption transition-colors"
            >
              Later
            </button>
          </div>
        </div>
      )}

      {/* 3. FULL INTERACTIVE VIDEO MODAL */}
      {showModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200"
        >
          <div className="relative w-full max-w-4xl rounded-2xl bg-surface border border-border-subtle shadow-2xl overflow-hidden flex flex-col">
            {/* Modal Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle bg-surface-elevated">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse" />
                <span className="text-dense font-semibold text-primary">Ichnoscope — Product Guide & Demo</span>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href="https://www.youtube.com/watch?v=NsmXi0lnl7Y"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-caption text-text-secondary hover:text-accent mr-2"
                >
                  <span>Open in YouTube</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <button
                  onClick={handleCloseModal}
                  className="p-1 rounded-md text-text-muted hover:text-primary hover:bg-hover transition-colors"
                  aria-label="Close video modal"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Video Container */}
            <div className="relative w-full aspect-video bg-black">
              <iframe
                className="w-full h-full"
                width="1059"
                height="595"
                src="https://www.youtube.com/embed/NsmXi0lnl7Y?autoplay=1"
                title="ichnoscope"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerPolicy="strict-origin-when-cross-origin"
                allowFullScreen
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
