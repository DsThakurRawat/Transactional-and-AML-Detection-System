const API_BASE = 'http://127.0.0.1:8000';

export interface StatsResponse {
  total_flagged: number;
  by_rule: Record<string, number>;
  by_band: Record<string, number>;
  explanations_generated: number;
}

export interface TopTransaction {
  transaction_id: string;
  account_id: string;
  score: number;
  band: string;
}

export interface TopAccount {
  account_id: string;
  total_score: number;
  critical_flags: number;
}

export interface FlagResponse {
  rule_name: string;
  reason: string;
  severity: string;
}

export interface ExplanationResponse {
  explanation: string;
  suggested_action: string;
  model_used: string;
}

export interface BaselineResponse {
  tx_count: number;
  amount_median: number;
  amount_mad: number;
  seen_countries: string[];
  seen_mccs: string[];
}

export interface TransactionDetail {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  merchant: string;
  merchant_category: string;
  country: string;
  channel: string;
  counterparty_account: string | null;
  score: number;
  band: string;
  flags: FlagResponse[];
  explanation: ExplanationResponse | null;
  baseline: BaselineResponse | null;
}

export interface TransactionList {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  merchant: string;
  counterparty_account: string | null;
  score: number;
  band: string;
  flags: string[];
}

export interface GraphNode {
  id: string;
  score: number;
  risk_band: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  amount: number;
  transaction_id: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/stats`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchTopTransactions(limit = 10): Promise<TopTransaction[]> {
  const res = await fetch(`${API_BASE}/transactions/top?limit=${limit}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error('Failed to fetch top transactions');
  return res.json();
}

export async function fetchTopAccounts(limit = 50): Promise<TopAccount[]> {
  const res = await fetch(`${API_BASE}/accounts/top?limit=${limit}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error('Failed to fetch top accounts');
  return res.json();
}

export async function fetchTransactions(limit = 50, offset = 0, band?: string, account_id?: string): Promise<TransactionList[]> {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
  if (band) params.append('band', band);
  if (account_id) params.append('account_id', account_id);
  
  const res = await fetch(`${API_BASE}/transactions/flagged?${params.toString()}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error('Failed to fetch transactions');
  return res.json();
}

export async function fetchTransactionDetail(id: string): Promise<TransactionDetail> {
  const res = await fetch(`${API_BASE}/transactions/${id}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch transaction detail');
  return res.json();
}

export async function fetchGraphData(limit = 500): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph?limit=${limit}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch graph data');
  return res.json();
}
