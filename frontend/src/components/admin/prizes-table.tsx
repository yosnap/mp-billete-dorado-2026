import { useState, useEffect, useCallback } from "react";
import type { AdminPrize } from "../../types/api";

async function fetchPrizes(): Promise<AdminPrize[]> {
  const res = await fetch("/api/v1/admin/prizes", { credentials: "include" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<AdminPrize[]>;
}

async function togglePrize(id: string, isActive: boolean): Promise<AdminPrize> {
  const res = await fetch(`/api/v1/admin/prizes/${id}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<AdminPrize>;
}

interface ToggleButtonProps {
  prize: AdminPrize;
  onToggle: (id: string, next: boolean) => Promise<void>;
}

function ToggleButton({ prize, onToggle }: ToggleButtonProps) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    try {
      await onToggle(prize.id, !prize.is_active);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      aria-label={prize.is_active ? "Desactivar premio" : "Activar premio"}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-500 focus-visible:ring-offset-2 disabled:opacity-50 ${
        prize.is_active ? "bg-yellow-500" : "bg-gray-200"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          prize.is_active ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

export function PrizesTable() {
  const [prizes, setPrizes] = useState<AdminPrize[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggleError, setToggleError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchPrizes();
      setPrizes(data);
      setError(null);
    } catch {
      setError("No se pudieron cargar los premios.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleToggle(id: string, isActive: boolean) {
    setToggleError(null);
    try {
      const updated = await togglePrize(id, isActive);
      setPrizes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch {
      setToggleError("Error al actualizar el premio. Inténtalo de nuevo.");
    }
  }

  if (loading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 rounded-lg bg-gray-200" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
        <span>{error}</span>
        <button onClick={load} className="underline font-medium hover:text-red-800">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {toggleError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
          {toggleError}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">Premio</th>
              <th className="px-4 py-3">Categoría</th>
              <th className="px-4 py-3 text-right">Stock total</th>
              <th className="px-4 py-3 text-right">Restante</th>
              <th className="px-4 py-3 text-center">Activo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {prizes.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No hay premios configurados.
                </td>
              </tr>
            )}
            {prizes.map((prize) => (
              <tr key={prize.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900">{prize.name}</p>
                  {prize.description && (
                    <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{prize.description}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="inline-block rounded-full bg-blue-100 text-blue-700 px-2.5 py-0.5 text-xs font-medium">
                    {prize.category}
                  </span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">
                  {prize.stock_total}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className={prize.stock_remaining === 0 ? "text-red-600 font-semibold" : "text-gray-700"}>
                    {prize.stock_remaining}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <ToggleButton prize={prize} onToggle={handleToggle} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 text-right">{prizes.length} premios en total</p>
    </div>
  );
}
