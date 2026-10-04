'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export function Table({
  className,
  children,
  ...props
}: React.TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto border border-border-subtle rounded bg-surface">
      <table className={cn('w-full caption-bottom text-dense border-collapse text-left', className)} {...props}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn(
        'sticky top-0 z-10 bg-canvas/90 backdrop-blur-xs border-b border-border-subtle text-caption uppercase font-semibold tracking-wider text-text-muted select-none',
        className
      )}
      {...props}
    >
      {children}
    </thead>
  );
}

export function TableBody({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={cn('divide-y divide-border-subtle', className)} {...props}>
      {children}
    </tbody>
  );
}

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  severityEdge?: 'P1-Critical' | 'P2-High' | 'P3-Medium';
  isDraftReady?: boolean;
}

export function TableRow({
  className,
  severityEdge,
  isDraftReady = false,
  children,
  ...props
}: TableRowProps) {
  return (
    <tr
      tabIndex={0}
      className={cn(
        'transition-colors duration-fast hover:bg-hover focus-visible:outline-none focus-visible:bg-hover focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-focus-ring relative group cursor-pointer',
        isDraftReady && 'bg-draft-subtle/40',
        severityEdge === 'P1-Critical' && 'border-l-3 border-l-danger',
        severityEdge === 'P2-High' && 'border-l-3 border-l-severity-high',
        severityEdge === 'P3-Medium' && 'border-l-3 border-l-warning',
        className
      )}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHead({
  className,
  children,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={cn('h-8.5 px-3.5 text-left align-middle font-medium font-mono text-caption', className)} {...props}>
      {children}
    </th>
  );
}

export function TableCell({
  className,
  children,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('p-3.5 align-middle text-dense text-primary', className)} {...props}>
      {children}
    </td>
  );
}
