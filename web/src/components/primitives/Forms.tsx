'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, disabled, ...props }, ref) => {
    return (
      <input
        ref={ref}
        disabled={disabled}
        className={cn(
          'w-full h-8.5 px-3 rounded-sm bg-surface text-primary border border-border-subtle text-xs placeholder:text-text-muted transition-colors duration-fast disabled:opacity-50 disabled:bg-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1 focus-visible:ring-offset-canvas',
          error && 'border-danger focus-visible:ring-danger',
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, disabled, children, ...props }, ref) => {
    return (
      <div className="relative inline-block w-full">
        <select
          ref={ref}
          disabled={disabled}
          className={cn(
            'w-full h-8.5 pl-3 pr-8 rounded-sm bg-surface text-primary border border-border-subtle text-xs appearance-none cursor-pointer transition-colors duration-fast disabled:opacity-50 disabled:bg-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1 focus-visible:ring-offset-canvas',
            error && 'border-danger focus-visible:ring-danger',
            className
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown className="w-3.5 h-3.5 text-text-muted absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
    );
  }
);
Select.displayName = 'Select';

export interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  id?: string;
  label?: string;
}

export function Switch({ checked, onCheckedChange, disabled = false, id, label }: SwitchProps) {
  return (
    <label htmlFor={id} className={cn('inline-flex items-center gap-2 cursor-pointer select-none', disabled && 'opacity-50 cursor-not-allowed')}>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onCheckedChange(!checked)}
        className={cn(
          'w-9 h-5 rounded-full p-0.5 transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1 focus-visible:ring-offset-canvas relative',
          checked ? 'bg-accent' : 'bg-border-strong'
        )}
      >
        <span
          className={cn(
            'block w-4 h-4 rounded-full bg-white transition-transform duration-fast shadow-xs',
            checked ? 'translate-x-4' : 'translate-x-0'
          )}
        />
      </button>
      {label && <span className="text-xs text-primary font-medium">{label}</span>}
    </label>
  );
}
