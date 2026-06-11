import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { apiClient, ApiError } from "../../lib/api_client";

interface StepOneProps {
  onSuccess: (participationId: string, code: string) => void;
}

const ERROR_MESSAGES: Record<number, string> = {
  404: "Código no encontrado. Verifica e inténtalo de nuevo.",
  409: "Este código ya fue utilizado.",
  429: "Demasiados intentos. Espera unos minutos.",
};

export function StepOne({ onSuccess }: StepOneProps) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) {
      setError("Introduce tu código de billete.");
      return;
    }
    setError(undefined);
    setLoading(true);
    try {
      const res = await apiClient.validateCode(trimmed);
      if (res.valid) {
        onSuccess(res.participation_id, trimmed);
      } else {
        setError("Código inválido. Comprueba que lo has escrito correctamente.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(ERROR_MESSAGES[err.status] ?? "Error al validar el código. Inténtalo de nuevo.");
      } else {
        setError("Error de conexión. Comprueba tu internet e inténtalo de nuevo.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
      <div>
        <h2 className="text-xl font-bold text-gray-900">Paso 1 — Valida tu código</h2>
        <p className="mt-1 text-sm text-gray-500">
          Introduce el código que encontraste en tu billete.
        </p>
      </div>

      <Input
        label="Código del billete"
        id="code"
        type="text"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Ej: MP-2026-ABCD"
        error={error}
        required
        autoComplete="off"
        autoFocus
        maxLength={32}
      />

      <Button type="submit" loading={loading}>
        Validar código
      </Button>
    </form>
  );
}
