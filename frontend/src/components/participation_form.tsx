import { useState } from "react";
import { StepOne } from "./form/step_one";
import { StepTwo } from "./form/step_two";

export function ParticipationForm() {
  const [step, setStep] = useState<1 | 2>(1);
  const [participationId, setParticipationId] = useState("");
  const [validatedCode, setValidatedCode] = useState("");

  function handleStepOneSuccess(pid: string, code: string) {
    setParticipationId(pid);
    setValidatedCode(code);
    setStep(2);
  }

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Indicador de pasos */}
      <div className="flex items-center gap-2 mb-8">
        {([1, 2] as const).map((n) => (
          <div key={n} className="flex items-center gap-2">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                step === n
                  ? "bg-yellow-500 text-white"
                  : step > n
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-500"
              }`}
            >
              {step > n ? "✓" : n}
            </span>
            <span className={`text-sm ${step === n ? "font-semibold text-gray-900" : "text-gray-400"}`}>
              {n === 1 ? "Código" : "Tus datos"}
            </span>
            {n < 2 && <span className="mx-1 text-gray-300">›</span>}
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        {step === 1 ? (
          <StepOne onSuccess={handleStepOneSuccess} />
        ) : (
          <StepTwo participationId={participationId} code={validatedCode} />
        )}
      </div>
    </div>
  );
}
