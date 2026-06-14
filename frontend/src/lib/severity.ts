export type RiskBand = "critical" | "high" | "medium" | "low" | "none";

interface BandConfig {
  label: string;
  varSolid: string;
  varSoft: string;
}

export const severityConfig: Record<string, BandConfig> = {
  critical: { label: "CRITICAL", varSolid: "var(--risk-critical)", varSoft: "var(--risk-critical-soft)" },
  high: { label: "HIGH", varSolid: "var(--risk-high)", varSoft: "var(--risk-high-soft)" },
  medium: { label: "MEDIUM", varSolid: "var(--risk-medium)", varSoft: "var(--risk-medium-soft)" },
  low: { label: "LOW", varSolid: "var(--risk-low)", varSoft: "var(--risk-low-soft)" },
  none: { label: "CLEAN", varSolid: "var(--risk-clean)", varSoft: "var(--risk-clean-soft)" },
};
