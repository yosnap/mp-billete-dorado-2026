import { useState, useEffect, useCallback } from "react";
import type { AdminStats } from "../../types/api";

const POLL_INTERVAL_MS = 30_000;

async function fetchStats(): Promise<AdminStats> {
  const res = await fetch("/api/v1/admin/stats", { credentials: "include" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<AdminStats>;
}

interface StatCardProps {
  label: string;
  value: number | string;
  accent?: boolean;
}

function StatCard({ label, value, accent = false }: StatCardProps) {
  return (
    <div className={`rounded-xl p-4 flex flex-col gap-1 ${accent ? "bg-yellow-50 border border-yellow-200" : "bg-white border border-gray-200"}`}>
      <span className="text-xs font-semibold uppercase tracking-widest text-gray-500">{label}</span>
      <span className={`text-2xl font-extrabold tabular-nums ${accent ? "text-yellow-600" : "text-gray-900"}`}>
        {value}
      </span>
    </div>
  );
}

export function StatsBar() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchStats();
      setStats(data);
      setLastUpdated(new Date());
      setError(null);
    } catch {
      setError("No se pudieron cargar las estadísticas.");
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}{" "}
        <button
          onClick={load}
          className="underline font-medium hover:text-red-800 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl bg-gray-200 h-20" />
        ))}
      </div>
    );
  }

  const categoryEntries = Object.entries(stats.winners_by_category);

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total participaciones" value={stats.total_participations} />
        <StatCard label="Total ganadores" value={stats.total_winners} accent />
        <StatCard label="Premios restantes" value={stats.total_prizes_remaining} />
        <StatCard
          label="Tasa de ganadores"
          value={
            stats.total_participations > 0
              ? `${((stats.total_winners / stats.total_participations) * 100).toFixed(1)}%`
              : "—"
          }
        />
      </div>

      {categoryEntries.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {categoryEntries.map(([category, count]) => (
            <span
              key={category}
              className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 text-yellow-800 px-3 py-1 text-xs font-medium"
            >
              <span className="font-bold">{count}</span>
              <span>{category}</span>
            </span>
          ))}
        </div>
      )}

      {lastUpdated && (
        <p className="text-xs text-gray-400 text-right">
          Actualizado: {lastUpdated.toLocaleTimeString("es-ES")}
        </p>
      )}
    </div>
  );
}
