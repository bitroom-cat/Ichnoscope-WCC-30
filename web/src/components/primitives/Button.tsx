'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const buttonVariants = cva(
  'inline-flex items-center justify-center font-medium transition-all duration-fast select-none disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 focus-visible:ring-offset-canvas rounded',
  {
    variants: {
      variant: {
        primary: 'bg-accent text-accent-foreground hover:bg-accent-hover shadow-xs',
        secondary: 'bg-surface text-primary border border-border-subtle hover:bg-hover hover:border-border-strong shadow-xs',
        ghost: 'bg-transparent text-secondary hover:text-primary hover:bg-hover',
        danger: 'bg-danger text-white hover:opacity-90 shadow-xs',
        draft: 'bg-draft text-white hover:opacity-90 shadow-xs',
      },
      size: {
        sm: 'h-7 px-2.5 text-caption gap-1.5',
        md: 'h-8.5 px-3.5 text-dense gap-2',
        lg: 'h-10 px-4 text-body gap-2.5',
      },
    },
    defaultVariants: {
      variant: 'secondary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading = false, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      >
        {loading && <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0 text-current" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  size?: 'sm' | 'md';
  variant?: 'secondary' | 'ghost' | 'primary' | 'danger';
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, label, size = 'md', variant = 'ghost', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        aria-label={label}
        title={label}
        className={cn(
          'inline-flex items-center justify-center transition-all duration-fast disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 focus-visible:ring-offset-canvas rounded',
          size === 'sm' ? 'w-7 h-7 text-xs' : 'w-8.5 h-8.5 text-sm',
          variant === 'ghost' && 'bg-transparent text-secondary hover:text-primary hover:bg-hover',
          variant === 'secondary' && 'bg-surface text-primary border border-border-subtle hover:bg-hover hover:border-border-strong',
          variant === 'primary' && 'bg-accent text-accent-foreground hover:bg-accent-hover',
          variant === 'danger' && 'bg-danger text-white hover:opacity-90',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
IconButton.displayName = 'IconButton';
