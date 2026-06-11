import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { apiClient, ApiError } from "../../lib/api_client";

interface StepTwoProps {
  participationId: string;
  code: string;
}

interface FormFields {
  full_name: string;
  email: string;
  phone: string;
  consent_legal: boolean;
  consent_marketing: boolean;
}

interface FormErrors {
  full_name?: string;
  email?: string;
  consent_legal?: string;
  general?: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function StepTwo({ participationId: _participationId, code }: StepTwoProps) {
  const [fields, setFields] = useState<FormFields>({
    full_name: "",
    email: "",
    phone: "",
    consent_legal: false,
    consent_marketing: false,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function validate(): FormErrors {
    const errs: FormErrors = {};
    if (!fields.full_name.trim()) errs.full_name = "El nombre completo es obligatorio.";
    if (!fields.email.trim()) {
      errs.email = "El email es obligatorio.";
    } else if (!EMAIL_RE.test(fields.email)) {
      errs.email = "Introduce un email válido.";
    }
    if (!fields.consent_legal) {
      errs.consent_legal = "Debes aceptar las bases legales para participar.";
    }
    return errs;
  }

  function set<K extends keyof FormFields>(key: K, value: FormFields[K]) {
    setFields((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined, general: undefined }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient.registerParticipant({
        code,
        full_name: fields.full_name.trim(),
        email: fields.email.trim(),
        phone: fields.phone.trim() || undefined,
        consent_legal: fields.consent_legal,
        consent_marketing: fields.consent_marketing,
      });
      window.location.href = `/ruleta?pid=${res.participation_id}`;
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setErrors({ general: "Este código ya fue registrado con otra cuenta." });
        } else if (err.status === 422) {
          setErrors({ general: "Debes aceptar las bases legales para participar." });
        } else {
          setErrors({ general: "Error al registrar. Inténtalo de nuevo." });
        }
      } else {
        setErrors({ general: "Error de conexión. Comprueba tu internet." });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
      <div>
        <h2 className="text-xl font-bold text-gray-900">Paso 2 — Tus datos</h2>
        <p className="mt-1 text-sm text-gray-500">
          Rellena el formulario para completar tu participación.
        </p>
      </div>

      <Input
        label="Nombre completo"
        id="full_name"
        type="text"
        value={fields.full_name}
        onChange={(e) => set("full_name", e.target.value)}
        error={errors.full_name}
        required
        autoComplete="name"
        maxLength={120}
      />

      <Input
        label="Email"
        id="email"
        type="email"
        value={fields.email}
        onChange={(e) => set("email", e.target.value)}
        error={errors.email}
        required
        autoComplete="email"
        maxLength={120}
      />

      <Input
        label="Teléfono (opcional)"
        id="phone"
        type="tel"
        value={fields.phone}
        onChange={(e) => set("phone", e.target.value)}
        autoComplete="tel"
        maxLength={20}
      />

      <div className="flex flex-col gap-3">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={fields.consent_legal}
            onChange={(e) => set("consent_legal", e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-yellow-500 focus:ring-yellow-500"
            required
          />
          <span className="text-sm text-gray-700">
            Acepto las{" "}
            <a href="/bases-legales" className="underline text-yellow-600 hover:text-yellow-700" target="_blank" rel="noreferrer">
              bases legales
            </a>{" "}
            y la{" "}
            <a href="/privacidad" className="underline text-yellow-600 hover:text-yellow-700" target="_blank" rel="noreferrer">
              política de privacidad
            </a>
            . <span className="text-red-500">*</span>
          </span>
        </label>
        {errors.consent_legal && (
          <p className="text-xs text-red-600" role="alert">{errors.consent_legal}</p>
        )}

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={fields.consent_marketing}
            onChange={(e) => set("consent_marketing", e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-yellow-500 focus:ring-yellow-500"
          />
          <span className="text-sm text-gray-700">
            Acepto recibir comunicaciones comerciales de MainPaper.
          </span>
        </label>
      </div>

      {errors.general && (
        <p className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
          {errors.general}
        </p>
      )}

      <Button type="submit" loading={loading}>
        Completar participación
      </Button>
    </form>
  );
}
