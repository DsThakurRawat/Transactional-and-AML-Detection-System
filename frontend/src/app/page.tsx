import { fetchStats, fetchTopFindings } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { AnalyzerCard } from '@/components/AnalyzerCard';
import { FindingsTable } from '@/components/FindingsTable';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { Database } from 'lucide-react';

export const revalidate = 10;
export const dynamic = 'force-dynamic';

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 text-[11px] uppercase tracking-wide text-text-muted/70 font-medium mb-3">
      {children}
      <span className="flex-1 h-px bg-border" />
    </div>
  );
}

export default async function OverviewPage() {
  try {
    const [stats, topFindings] = await Promise.all([
      fetchStats(),
      fetchTopFindings(5),
    ]);

    const isSystemEmpty = stats.total === 0;
    const critical = stats.by_band['critical'] || 0;

    return (
      <div className="flex flex-col max-w-7xl mx-auto">
        <div className="flex flex-col gap-1.5 mb-7">
          <h1 className="text-xl font-semibold text-text">Platform overview</h1>
          <p className="text-sm text-text-muted">Unified compliance queue across all five analyzers.</p>
        </div>

        {/* 1. Posture — stat cards (now fully wired, no more "--") */}
        <Eyebrow>Posture</Eyebrow>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 mb-8">
          <StatCard
            title="Transactions"
            value={stats.total_transactions.toLocaleString()}
            hint={`across ${stats.accounts_monitored} accounts`}
          />
          <StatCard
            title="Open findings"
            value={stats.total.toLocaleString()}
            hint="all analyzers"
          />
          <StatCard
            title="Critical risk"
            value={critical.toLocaleString()}
            band="critical"
            hint="needs action now"
          />
          <StatCard
            title="Accounts monitored"
            value={stats.accounts_monitored.toLocaleString()}
            hint="in current dataset"
          />
        </div>

        {/* 2. The five analyzers — the centerpiece */}
        <Eyebrow>Analyzer triage</Eyebrow>
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5 mb-8">
          <AnalyzerCard
            analyzer="aml"
            count={stats.by_analyzer['aml'] || 0}
            metricLabel="Critical structuring"
            metricValue={critical}
            topBand={(stats.by_analyzer['aml'] || 0) > 0 ? 'critical' : 'clean'}
          />
          <AnalyzerCard
            analyzer="reconciliation"
            count={stats.by_analyzer['reconciliation'] || 0}
            metricLabel="Open breaks"
            metricValue={stats.by_analyzer['reconciliation'] || 0}
            topBand={(stats.by_analyzer['reconciliation'] || 0) > 0 ? 'high' : 'clean'}
          />
          <AnalyzerCard
            analyzer="categorization"
            count={stats.by_analyzer['categorization'] || 0}
            metricLabel="Needs review"
            metricValue={stats.by_analyzer['categorization'] || 0}
            topBand={(stats.by_analyzer['categorization'] || 0) > 0 ? 'medium' : 'clean'}
          />
          <AnalyzerCard
            analyzer="disputes"
            count={stats.by_analyzer['disputes'] || 0}
            metricLabel="Deadlines ≤ 7d"
            metricValue={stats.by_analyzer['disputes'] || 0}
            topBand={(stats.by_analyzer['disputes'] || 0) > 0 ? 'high' : 'clean'}
          />
          <AnalyzerCard
            analyzer="reporting"
            count={stats.by_analyzer['reporting'] || 0}
            metricLabel="SARs pending"
            metricValue={stats.by_analyzer['reporting'] || 0}
            topBand={(stats.by_analyzer['reporting'] || 0) > 0 ? 'medium' : 'clean'}
          />
        </div>

        {/* 3. Review queue */}
        <Eyebrow>Review queue · highest risk first</Eyebrow>
        {isSystemEmpty ? (
          <EmptyState
            icon={Database}
            title="Awaiting data"
            hint="The database is empty. Run the analyzers to populate the queue."
          />
        ) : (
          <FindingsTable findings={topFindings} />
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <ErrorState message="Can't reach the backend — it may be waking up from idle. Retry in a moment." />
      </div>
    );
  }
}
