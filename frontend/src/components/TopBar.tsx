'use client';
import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

type Health = 'connecting' | 'live' | 'offline';

export function TopBar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<Health>('connecting');
  const [syncedAt, setSyncedAt] = useState<Date | null>(null);

  useEffect(() => {
    let failures = 0;
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    const API_BASE = rawUrl.replace(/\/+$/, '');

    const checkHealth = async () => {
      try {
        // Tolerate cold starts: a sleeping backend can take 30-50s to wake,
        // so we only flip to "offline" after repeated failures, not the first.
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 8000);
        const res = await fetch(`${API_BASE}/health`, { signal: ctrl.signal, cache: 'no-store' });
        clearTimeout(timer);
        if (res.ok) {
          failures = 0;
          setHealth('live');
          setSyncedAt(new Date());
        } else {
          throw new Error('not ok');
        }
      } catch {
        failures += 1;
        // Don't alarm on a single miss (likely a cold start) — show "connecting".
        setHealth(failures >= 2 ? 'offline' : 'connecting');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const getTitle = () => {
    if (pathname === '/') return 'Platform overview';
    if (pathname.startsWith('/findings')) return 'Review findings';
    if (pathname.startsWith('/graph')) return 'Network graph';
    if (pathname.startsWith('/accounts')) return 'Account risk';
    return 'Dashboard';
  };

  const config = {
    live: { dot: 'bg-risk-clean', text: 'text-risk-clean', bg: 'bg-risk-clean-soft', label: 'Live' },
    connecting: { dot: 'bg-risk-medium', text: 'text-risk-medium', bg: 'bg-risk-medium-soft', label: 'Reconnecting' },
    offline: { dot: 'bg-risk-critical', text: 'text-risk-critical', bg: 'bg-risk-critical-soft', label: 'Backend asleep' },
  }[health];

  const synced = syncedAt
    ? `synced ${Math.max(1, Math.round((Date.now() - syncedAt.getTime()) / 1000))}s ago`
    : 'waking the backend…';

  return (
    <header className="h-[60px] bg-surface border-b border-border flex items-center justify-between px-7 shrink-0">
      <h1 className="text-base font-semibold text-text">{getTitle()}</h1>
      <div
        className={`flex items-center gap-2 ${config.bg} ${config.text} px-3 py-1 rounded-full text-[11.5px] font-medium`}
        title={health === 'offline' ? 'The free-tier backend spins down when idle. The first request wakes it (~30s).' : 'API connection healthy'}
      >
        <span className={`w-[7px] h-[7px] rounded-full ${config.dot}`}></span>
        {config.label}
        {health === 'live' && <span className="text-text-muted font-normal">· {synced}</span>}
      </div>
    </header>
  );
}
