import type { SpinResult } from "../types/api";

interface Props {
  result: SpinResult;
}

export function ResultCard({ result }: Props) {
  if (result.won) {
    return (
      <div className="w-full max-w-md text-center">
        <div className="rounded-2xl border-2 border-yellow-400 bg-yellow-50 p-8 shadow-lg">
          <div className="text-6xl mb-4" role="img" aria-label="Trofeo">
            🏆
          </div>
          <h1 className="text-3xl font-extrabold text-yellow-600 mb-2">
            ¡Enhorabuena!
          </h1>
          <p className="text-gray-600 mb-6 text-sm">
            Has ganado un premio en el sorteo MP Billete Dorado 2026.
          </p>

          <div className="rounded-xl bg-white border border-yellow-200 p-5 mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-yellow-500 mb-1">
              Tu premio
            </p>
            <p className="text-xl font-bold text-gray-900">{result.prize_name}</p>
            {result.prize_description && (
              <p className="mt-2 text-sm text-gray-500">{result.prize_description}</p>
            )}
          </div>

          <p className="text-xs text-gray-400 mb-6">
            Recibirás un email con las instrucciones para canjear tu premio.
          </p>

          <a
            href="/"
            className="inline-block rounded-lg bg-yellow-500 hover:bg-yellow-600 text-white font-semibold px-6 py-3 transition-colors"
          >
            Volver al inicio
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md text-center">
      <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="text-6xl mb-4" role="img" aria-label="Estrella">
          ⭐
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-2">
          ¡Gracias por participar!
        </h1>
        <p className="text-gray-500 mb-6">
          Esta vez no ha sido, pero seguimos contando contigo para próximas ediciones de MP Billete Dorado.
        </p>

        <div className="rounded-xl bg-gray-50 border border-gray-100 p-4 mb-6">
          <p className="text-sm text-gray-600">
            Comparte tu experiencia y anima a tus amigos a participar en el sorteo.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a
            href="/"
            className="inline-block rounded-lg bg-yellow-500 hover:bg-yellow-600 text-white font-semibold px-6 py-3 transition-colors text-sm"
          >
            Volver al inicio
          </a>
          <a
            href="/bases-legales"
            className="inline-block rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 font-semibold px-6 py-3 transition-colors text-sm"
          >
            Bases legales
          </a>
        </div>
      </div>
    </div>
  );
}
