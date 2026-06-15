import React from 'react';
import Link from 'next/link';
import { SeverityBadge } from './SeverityBadge';
import { AnalyzerBadge } from './AnalyzerBadge';
import { ScorePill } from './ScorePill';
import { BAND, RiskBand } from '@/lib/severity';
import { FindingResponse } from '@/lib/api';

function relativeTime(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

export function FindingsTable({ findings }: { findings: FindingResponse[] }) {
  if (!findings || findings.length === 0) {
    return null; // Handled by EmptyState upstream
  }

  return (
    <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden">
      <table className="w-full text-left text-sm table-fixed">
        <colgroup>
          <col className="w-[3px]" />
          <col className="w-[116px]" />
          <col className="w-[132px]" />
          <col className="w-[150px]" />
          <col className="w-[78px]" />
          <col className="w-[118px]" />
          <col />
          <col className="w-[96px]" />
        </colgroup>
        <thead className="bg-surface-sunken border-b border-border">
          <tr className="text-[10.5px] uppercase tracking-wide text-text-muted">
            <th></th>
            <th className="px-4 py-3 font-medium">Severity</th>
            <th className="px-4 py-3 font-medium">Analyzer</th>
            <th className="px-4 py-3 font-medium">Entity</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Summary</th>
            <th className="px-4 py-3 font-medium text-right">Time</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => {
            const band = (f.band && f.band in BAND ? f.band : 'medium') as RiskBand;
            return (
              <tr key={f.id} className="border-b border-border last:border-0 hover:bg-surface-sunken/40 transition-colors group">
                {/* risk spine */}
                <td className="p-0">
                  <div className="w-[3px] h-11" style={{ backgroundColor: BAND[band].solid }} />
                </td>
                <td className="px-4 py-3">
                  <SeverityBadge band={f.band as any} />
                </td>
                <td className="px-4 py-3">
                  <AnalyzerBadge analyzer={f.analyzer} />
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/findings/${f.id}`}
                    className="num text-text-muted hover:text-brand block truncate"
                    title={f.entity_id}
                  >
                    {f.entity_id}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <ScorePill score={f.score || 0} band={f.band as any} />
                </td>
                <td className="px-4 py-3">
                  <span className="capitalize text-text-muted text-xs font-medium border border-border px-2 py-0.5 rounded-[var(--r-control)] bg-canvas whitespace-nowrap">
                    {f.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link href={`/findings/${f.id}`} className="block truncate text-text-muted group-hover:text-text transition-colors" title={f.summary}>
                    {f.summary}
                  </Link>
                </td>
                <td className="px-4 py-3 num text-text-muted text-xs text-right whitespace-nowrap">
                  {relativeTime(f.created_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
