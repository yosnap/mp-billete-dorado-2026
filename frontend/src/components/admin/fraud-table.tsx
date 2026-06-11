import { useState, useEffect, useCallback } from "react";
import type { FraudFlag, FraudListResponse } from "../../types/api";

const PAGE_SIZE = 20;

async function fetchFraudFlags(page: number): Promise<FraudListResponse> {
  const res = await fetch(
    `/api/v1/admin/fraud?page=${page}&page_size=${PAGE_SIZE}`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<FraudListResponse>;
}

async function invalidateFlag(flagId: string): Promise<void> {
  const res = await fetch(`/api/v1/admin/fraud/${flagId}/invalidate`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface RowProps {
  flag: FraudFlag;
  onInvalidate: (id: string) => Promise<void>;
}

function FraudRow({ flag, onInvalidate }: RowProps) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(flag.invalidated);
  const [rowError, setRowError] = useState<string | null>(null);

  async function handleInvalidate() {
    setLoading(true);
    setRowError(null);
    try {
      await onInvalidate(flag.id);
      setDone(true);
    } catch {
      setRowError("Error al invalidar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <tr className={`hover:bg-gray-50 transition-colors ${done ? "opacity-50" : ""}`}>
      <td className="px-4 py-3">
        <p className="font-medium text-gray-900 text-sm">{flag.participant_name}</p>
        <p className="text-xs text-gray-400">{flag.participant_email}</p>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs">
        <span className="line-clamp-2">{flag.reason}</span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
        {formatDate(flag.created_at)}
      </td>
      <td className="px-4 py-3 text-center">
        {done ? (
          <span className="inline-block rounded-full bg-green-100 text-green-700 px-2.5 py-0.5 text-xs font-medium">
            Invalidada
          </span>
        ) : (
          <div className="flex flex-col items-center gap-1">
            <button
              onClick={handleInvalidate}
              disabled={loading}
              className="rounded-lg bg-red-500 hover:bg-red-600 text-white text-xs font-semibold px-3 py-1.5 transition-colors disabled:opacity-50"
            >
              {loading ? "..." : "Invalidar"}
            </button>
            {rowError && (
              <span className="text-xs text-red-600">{rowError}</span>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

export function FraudTable() {
  const [data, setData] = useState<FraudListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchFraudFlags(p);
      setData(res);
    } catch {
      setError("No se pudieron cargar los flags de fraude.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  async function handleInvalidate(flagId: string) {
    await invalidateFlag(flagId);
    // Marcar localmente — la fila ya gestiona su estado visual
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  if (loading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-14 rounded-lg bg-gray-200" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
        <span>{error}</span>
        <button onClick={() => load(page)} className="underline font-medium hover:text-red-800">
          Reintentar
        </button>
      </div>
    );
  }

  const items: FraudFlag[] = data?.items ?? [];

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">Participante</th>
              <th className="px-4 py-3">Motivo</th>
              <th className="px-4 py-3">Fecha</th>
              <th className="px-4 py-3 text-center">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  No hay flags de fraude en esta página.
                </td>
              </tr>
            )}
            {items.map((flag) => (
              <FraudRow key={flag.id} flag={flag} onInvalidate={handleInvalidate} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">
            Página {page} de {totalPages} · {data?.total ?? 0} flags totales
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
