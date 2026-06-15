import React from 'react';
import { ShieldAlert, ArrowLeftRight, Tags, Gavel, FileText } from 'lucide-react';
import { BAND, RiskBand } from '@/lib/severity';
import Link from 'next/link';

interface AnalyzerCardProps {
  analyzer: 'aml' | 'reconciliation' | 'categorization' | 'disputes' | 'reporting';
  count: number;
  metricLabel: string;
  metricValue: string | number;
  topBand?: RiskBand;
}

const ICONS = {
  aml: ShieldAlert,
  reconciliation: ArrowLeftRight,
  categorization: Tags,
  disputes: Gavel,
  reporting: FileText,
};

const NAMES = {
  aml: 'AML',
  reconciliation: 'Reconciliation',
  categorization: 'Categorization',
  disputes: 'Disputes',
  reporting: 'Reporting',
};

export function AnalyzerCard({ analyzer, count, metricLabel, metricValue, topBand }: AnalyzerCardProps) {
  const Icon = ICONS[analyzer];
  const band = topBand ?? 'clean';
  const bandData = BAND[band];

  return (
    <Link
      href={`/findings?analyzer=${analyzer}`}
      className="group block bg-surface border border-border rounded-[var(--r-card)] overflow-hidden hover:-translate-y-0.5 hover:shadow-[0_6px_18px_rgba(21,33,59,0.08)] transition-all"
    >
      {/* risk spine — the signature element */}
      <div className="h-[3px] w-full" style={{ backgroundColor: bandData.solid }} />

      <div className="p-4">
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2 text-text-muted group-hover:text-brand transition-colors">
            <Icon className="w-[15px] h-[15px]" />
            <h3 className="font-medium text-[13px]">{NAMES[analyzer]}</h3>
          </div>
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: bandData.solid }}
            title={`Worst current risk: ${bandData.label}`}
          />
        </div>

        <div>
          <div className="num text-[34px] leading-none font-medium text-text tracking-tight">
            {count.toLocaleString()}
          </div>
          <div className="text-[10.5px] font-medium text-text-muted uppercase tracking-wide mt-1.5">
            open findings
          </div>
        </div>

        <div className="mt-3.5 pt-3 border-t border-border flex justify-between items-center">
          <span className="text-[12px] text-text-muted">{metricLabel}</span>
          <span className="num text-[13px] font-medium text-text">{metricValue}</span>
        </div>
      </div>
    </Link>
  );
}
