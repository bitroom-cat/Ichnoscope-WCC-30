'use client';

import React, { useState } from 'react';
import { RunItem } from '@/lib/api';
import { Button } from '@/components/primitives/Button';
import {
  Send,
  XCircle,
  RotateCcw,
  Check,
  AlertTriangle,
  ExternalLink,
  X,
} from 'lucide-react';

interface ActionBarProps {
  run: RunItem;
  onApprove: () => Promise<void>;
  onReject: (reason?: string) => Promise<void>;
  onRerun: () => Promise<void>;
  isLoading?: boolean;
}

export function ActionBar({
  run,
  onApprove,
  onReject,
  onRerun,
  isLoading,
}: ActionBarProps) {
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [confirmApprove, setConfirmApprove] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleApprove = async () => {
    try {
      await onApprove();
      setConfirmApprove(false);
      setActionSuccess('Successfully approved and published GitHub issue.');
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (e: any) {
      alert(e?.message || 'Failed to approve');
    }
  };

  const handleReject = async () => {
    try {
      await onReject(rejectReason);
      setRejecting(false);
      setActionSuccess('Draft discarded.');
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (e: any) {
      alert(e?.message || 'Failed to reject');
    }
  };

  return (
    <div className="relative">
      {/* Toast Confirmation */}
      {actionSuccess && (
        <div className="mb-4 flex items-center gap-2 rounded-md bg-success-subtle border border-success/30 p-3 text-caption font-medium text-success animate-fadeIn">
          <Check className="w-4 h-4 text-success" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Main Action Ribbon */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 sm:p-4 rounded-lg bg-surface border border-border-subtle transition-colors">
        <div className="flex items-center gap-3">
          <div className="text-dense">
            <span className="text-text-muted block text-caption">Human Review Gate</span>
            <span className="text-primary font-semibold">
              {run.status === 'pending_approval' && 'Action required: sign off on drafted issue'}
              {run.status === 'approved' && 'Issue published to target repository'}
              {run.status === 'rejected' && 'Draft discarded by reviewer'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {run.status === 'pending_approval' && (
            <>
              {!confirmApprove ? (
                <Button
                  variant="primary"
                  size="sm"
                  disabled={isLoading}
                  onClick={() => setConfirmApprove(true)}
                  className="gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  Approve & Open GitHub Issue
                </Button>
              ) : (
                <div className="flex items-center gap-2 bg-accent-subtle border border-accent/30 p-1 rounded-md">
                  <span className="text-caption text-accent px-2 font-medium">
                    Publish issue now?
                  </span>
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={isLoading}
                    onClick={handleApprove}
                  >
                    Confirm
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setConfirmApprove(false)}
                  >
                    Cancel
                  </Button>
                </div>
              )}

              <Button
                variant="secondary"
                size="sm"
                disabled={isLoading}
                onClick={() => setRejecting(true)}
                className="gap-1.5 text-danger border-danger/30 hover:bg-danger-subtle"
              >
                <XCircle className="w-3.5 h-3.5 text-danger" />
                Reject
              </Button>
            </>
          )}

          {run.status === 'approved' && run.issue_url && (
            <a
              href={run.issue_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-accent-subtle hover:bg-accent/20 text-accent text-dense font-semibold border border-accent/30 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View GitHub Issue GH-{run.issue_url.split('/').pop()}
            </a>
          )}

          <Button
            variant="secondary"
            size="sm"
            disabled={isLoading}
            onClick={onRerun}
            className="gap-1.5"
            title="Re-run deterministic triage pipeline"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Re-run Triage
          </Button>
        </div>
      </div>

      {/* Reject Reason Modal */}
      {rejecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md max-h-[85vh] overflow-y-auto rounded-lg bg-surface border border-border-subtle p-5 sm:p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2 text-danger">
                <AlertTriangle className="w-4.5 h-4.5" />
                <h3 className="font-semibold text-primary text-body">
                  Discard Triage Draft
                </h3>
              </div>
              <button
                onClick={() => setRejecting(false)}
                className="p-1 rounded-md text-text-muted hover:text-primary hover:bg-canvas transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-dense text-secondary leading-relaxed">
              Discarding prevents opening an automated GitHub issue. Record an audit reason for your team:
            </p>

            <textarea
              rows={3}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Expected transient disruption during database maintenance window."
              className="w-full rounded-md bg-canvas border border-border-subtle p-3 text-caption text-primary placeholder-text-muted focus:outline-none focus:border-accent"
            />

            <div className="flex justify-end gap-2 pt-2 border-t border-border-subtle">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRejecting(false)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleReject}
              >
                Confirm Discard
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
