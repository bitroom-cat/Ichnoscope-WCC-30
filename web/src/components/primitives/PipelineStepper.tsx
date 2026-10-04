'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Check, RotateCw, AlertCircle, Clock } from 'lucide-react';

export type PipelineStepName = 'parse' | 'blame' | 'explain' | 'draft' | 'publish';
export type PipelineStepState = 'pending' | 'running' | 'done' | 'failed' | 'skipped';

export interface PipelineStep {
  name: PipelineStepName;
  label?: string;
  state: PipelineStepState;
  ms?: number;
}

export interface PipelineStepperProps {
  steps: PipelineStep[];
  onViewLog?: (stepName: PipelineStepName) => void;
  className?: string;
}

export function PipelineStepper({ steps, onViewLog, className }: PipelineStepperProps) {
  const stepLabels: Record<PipelineStepName, string> = {
    parse: 'Parse stack',
    blame: 'Blame release SHA',
    explain: 'LLM reasoning',
    draft: 'Draft issue',
    publish: 'Publish GitHub',
  };

  return (
    <div className={cn('w-full py-3 overflow-x-auto', className)}>
      <div className="flex items-center min-w-[560px] relative">
        {steps.map((step, idx) => {
          const isLast = idx === steps.length - 1;
          const isDone = step.state === 'done';
          const isRunning = step.state === 'running';
          const isFailed = step.state === 'failed';

          return (
            <React.Fragment key={step.name}>
              {/* Step Node */}
              <div className="flex flex-col items-center gap-1.5 shrink-0 relative z-10">
                <div
                  className={cn(
                    'w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono transition-colors duration-fast border',
                    isDone && 'bg-accent text-on-accent border-accent',
                    isRunning && 'bg-info text-white border-info animate-pulse',
                    isFailed && 'bg-danger text-white border-danger',
                    step.state === 'pending' && 'bg-surface text-text-muted border-border-strong',
                    step.state === 'skipped' && 'bg-hover text-text-muted border-border-subtle'
                  )}
                >
                  {isDone && <Check className="w-4 h-4 stroke-[2.5]" />}
                  {isRunning && <RotateCw className="w-3.5 h-3.5 animate-spin" />}
                  {isFailed && <AlertCircle className="w-4 h-4" />}
                  {step.state === 'pending' && <span className="text-caption">{idx + 1}</span>}
                  {step.state === 'skipped' && <span className="text-caption">-</span>}
                </div>

                <div className="text-center">
                  <span className="text-xs font-medium text-primary block whitespace-nowrap">
                    {step.label || stepLabels[step.name]}
                  </span>
                  <div className="flex items-center justify-center gap-1 text-caption text-text-muted font-mono tabular-nums">
                    {step.ms !== undefined && isDone && <span>{step.ms}ms</span>}
                    {isRunning && <span className="text-info font-medium">Running...</span>}
                    {isFailed && (
                      <button
                        type="button"
                        onClick={() => onViewLog?.(step.name)}
                        className="text-danger hover:underline font-sans cursor-pointer"
                      >
                        View log
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Connecting Line: The Trace Motif */}
              {!isLast && (
                <div className="flex-1 h-0.5 mx-2 -mt-5 relative bg-border-strong rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full transition-all duration-normal',
                      isDone ? 'bg-accent w-full' : isRunning ? 'bg-info w-1/2 animate-pulse' : 'w-0'
                    )}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
