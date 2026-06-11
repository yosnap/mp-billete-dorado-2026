import { useEffect, useRef, useState } from "react";
import type { SpinResult } from "../types/api";

interface Props {
  spinResult: SpinResult;
  redirectDelay?: number; // ms tras completar animación antes de redirigir
}

// Segmentos visuales de la ruleta (decorativos; el segmento ganador viene del backend)
const SEGMENTS = [
  { label: "Premio", color: "#f59e0b" },
  { label: "Suerte", color: "#3b82f6" },
  { label: "Premio", color: "#10b981" },
  { label: "Suerte", color: "#f59e0b" },
  { label: "Premio", color: "#8b5cf6" },
  { label: "Suerte", color: "#3b82f6" },
  { label: "Premio", color: "#ef4444" },
  { label: "Suerte", color: "#10b981" },
];

const TOTAL_SEGMENTS = SEGMENTS.length;
const SEG_ANGLE = 360 / TOTAL_SEGMENTS; // 45° por segmento

/**
 * Calcula los grados finales del giro para que el segmento ganador
 * quede apuntando a la flecha (arriba, 0°/360°).
 * Añade 5+ vueltas completas para efecto visual.
 */
function calcFinalDegrees(segmentIndex: number): number {
  const targetAngle = segmentIndex * SEG_ANGLE;
  const fullRotations = 360 * 6; // 6 vueltas completas
  // El segmento 0 empieza en 0°; para que quede arriba, rotamos su negativo
  return fullRotations + (360 - targetAngle);
}

function drawWheel(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const size = canvas.width;
  const center = size / 2;
  const radius = center - 4;

  ctx.clearRect(0, 0, size, size);

  SEGMENTS.forEach((seg, i) => {
    const startAngle = ((i * SEG_ANGLE - 90) * Math.PI) / 180;
    const endAngle = (((i + 1) * SEG_ANGLE - 90) * Math.PI) / 180;

    // Sector
    ctx.beginPath();
    ctx.moveTo(center, center);
    ctx.arc(center, center, radius, startAngle, endAngle);
    ctx.closePath();
    ctx.fillStyle = seg.color;
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Etiqueta
    const labelAngle = startAngle + (endAngle - startAngle) / 2;
    const labelRadius = radius * 0.68;
    ctx.save();
    ctx.translate(
      center + labelRadius * Math.cos(labelAngle),
      center + labelRadius * Math.sin(labelAngle),
    );
    ctx.rotate(labelAngle + Math.PI / 2);
    ctx.fillStyle = "#fff";
    ctx.font = `bold ${Math.floor(size / 22)}px system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(seg.label, 0, 0);
    ctx.restore();
  });

  // Centro decorativo
  ctx.beginPath();
  ctx.arc(center, center, size / 12, 0, 2 * Math.PI);
  ctx.fillStyle = "#fff";
  ctx.fill();
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 3;
  ctx.stroke();
}

export function RouletteWheel({ spinResult, redirectDelay = 3500 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wheelRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<"idle" | "spinning" | "done">("idle");
  const [reducedMotion, setReducedMotion] = useState(false);

  // Detectar preferencia de movimiento reducido
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
  }, []);

  // Dibujar la rueda en el canvas
  useEffect(() => {
    if (!canvasRef.current) return;
    drawWheel(canvasRef.current);
  }, []);

  // Arrancar animación al montar
  useEffect(() => {
    const segmentIndex = spinResult.segment_index ?? 0;

    if (reducedMotion) {
      // Sin animación: mostrar resultado directo y redirigir
      setPhase("done");
      const timer = setTimeout(() => {
        window.location.href = `/resultado/${spinResult.spin_id}`;
      }, 1200);
      return () => clearTimeout(timer);
    }

    // Pequeño delay para que el usuario vea la rueda antes de girar
    const startTimer = setTimeout(() => {
      if (!wheelRef.current) return;
      const finalDeg = calcFinalDegrees(segmentIndex);
      wheelRef.current.style.transition =
        "transform 4s cubic-bezier(0.17, 0.67, 0.12, 1.0)";
      wheelRef.current.style.transform = `rotate(${finalDeg}deg)`;
      setPhase("spinning");
    }, 600);

    return () => clearTimeout(startTimer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reducedMotion]);

  // Escuchar fin de transición CSS
  useEffect(() => {
    const el = wheelRef.current;
    if (!el || reducedMotion) return;

    function onTransitionEnd() {
      setPhase("done");
      setTimeout(() => {
        window.location.href = `/resultado/${spinResult.spin_id}`;
      }, redirectDelay);
    }

    el.addEventListener("transitionend", onTransitionEnd, { once: true });
    return () => el.removeEventListener("transitionend", onTransitionEnd);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reducedMotion, redirectDelay]);

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Indicador de flecha */}
      <div className="relative w-full flex justify-center">
        <svg
          viewBox="0 0 24 24"
          className="absolute -top-3 z-10 h-8 w-8 fill-yellow-500 drop-shadow"
          aria-hidden="true"
        >
          <path d="M12 2L6 10h12L12 2z" />
        </svg>
      </div>

      {/* Ruleta */}
      <div className="relative">
        <div
          ref={wheelRef}
          className="rounded-full shadow-2xl will-change-transform"
          style={{ width: 300, height: 300 }}
          role="img"
          aria-label="Ruleta girando"
        >
          <canvas
            ref={canvasRef}
            width={300}
            height={300}
            className="rounded-full"
          />
        </div>

        {/* Overlay cuando terminó */}
        {phase === "done" && (
          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40">
            <span className="text-white text-2xl font-extrabold drop-shadow">
              {spinResult.won ? "¡Ganaste!" : "¡Suerte!"}
            </span>
          </div>
        )}
      </div>

      {/* Mensaje de estado */}
      <p
        className="text-sm text-gray-500 animate-pulse"
        aria-live="polite"
        aria-atomic="true"
      >
        {phase === "idle" && "Preparando la ruleta..."}
        {phase === "spinning" && "¡Girando!"}
        {phase === "done" && "Redirigiendo a tu resultado..."}
      </p>
    </div>
  );
}
