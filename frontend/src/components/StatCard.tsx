import React from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  hint?: string;
  band?: 'critical' | 'high' | 'medium' | 'low' | 'clean';
}

export function StatCard({ title, value, hint, band }: StatCardProps) {
  const isAlert = band === 'critical';
  return (
    <div
      className={cn(
        'relative bg-surface border border-border rounded-[var(--r-card)] p-[16px_18px] overflow-hidden',
        isAlert && 'border-risk-critical/30'
      )}
    >
      {isAlert && (
        <span className="absolute left-0 top-0 bottom-0 w-[3px] bg-risk-critical" />
      )}
      <h3 className="text-[11px] font-medium text-text-muted uppercase tracking-wide">{title}</h3>
      <div className={cn('num text-[30px] font-medium mt-2 tracking-tight', isAlert && 'text-risk-critical')}>
        {value}
      </div>
      {hint && <div className="text-[12px] text-text-muted/80 mt-0.5">{hint}</div>}
    </div>
  );
}
