// ============================================================
// SessionModal.jsx
// Modal para registrar el score tras una sesión de estudio
// El alumno indica del 0 al 10 cómo le fue en la sesión
// ============================================================

import { useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

export default function SessionModal({ recomendacion, usuarioId, onCerrar, onSesionGuardada }) {
  const [score,     setScore]     = useState(5)
  const [guardando, setGuardando] = useState(false)
  const [error,     setError]     = useState(null)

  const guardarSesion = async () => {
    setGuardando(true)
    setError(null)
    try {
      await axios.post(`${API}/api/sesiones`, {
        usuario_id:    usuarioId,
        asignatura_id: recomendacion.asignatura_id,
        duracion_min:  recomendacion.duracion_minutos,
        score:         score
      })
      onSesionGuardada()
      onCerrar()
    } catch (e) {
      setError("Error al guardar la sesión. Inténtalo de nuevo.")
    } finally {
      setGuardando(false)
    }
  }

  // ── Config visual según score ────────────────────────────
  const getScoreConfig = (s) => {
    if (s >= 8) return {
      emoji:  "🌟",
      label:  "Excelente",
      color:  "text-emerald-600 dark:text-emerald-400",
      bar:    "bg-emerald-500",
      bg:     "bg-emerald-50 dark:bg-emerald-950/40",
      border: "border-emerald-200 dark:border-emerald-900/60",
    }
    if (s >= 6) return {
      emoji:  "😊",
      label:  "Bien",
      color:  "text-indigo-600 dark:text-indigo-400",
      bar:    "bg-indigo-500",
      bg:     "bg-indigo-50 dark:bg-indigo-950/40",
      border: "border-indigo-200 dark:border-indigo-900/60",
    }
    if (s >= 4) return {
      emoji:  "😐",
      label:  "Regular",
      color:  "text-amber-600 dark:text-amber-400",
      bar:    "bg-amber-400",
      bg:     "bg-amber-50 dark:bg-amber-950/40",
      border: "border-amber-200 dark:border-amber-900/60",
    }
    return {
      emoji:  "😓",
      label:  "Difícil",
      color:  "text-red-600 dark:text-red-400",
      bar:    "bg-red-500",
      bg:     "bg-red-50 dark:bg-red-950/40",
      border: "border-red-200 dark:border-red-900/60",
    }
  }

  const cfg = getScoreConfig(score)

  return (
    // ── Backdrop ──────────────────────────────────────────
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4
                 bg-slate-900/60 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onCerrar()}
    >

      <div className="bg-white dark:bg-slate-800 rounded-2xl border
                      border-slate-200 dark:border-slate-700/60
                      shadow-2xl w-full max-w-md overflow-hidden">

        {/* ── Barra de acento superior ── */}
        <div className={`h-1 w-full transition-colors duration-300 ${cfg.bar}`} />

        <div className="p-7 space-y-6">

          {/* ── Header ── */}
          <div className="flex items-start justify-between">
            <div className="space-y-0.5">
              <h2 className="text-xl font-bold tracking-tight text-slate-900
                             dark:text-slate-50">
                ¿Cómo fue la sesión?
              </h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">
                {recomendacion.nombre_asignatura}
                <span className="mx-1.5 text-slate-300 dark:text-slate-600">·</span>
                {recomendacion.duracion_minutos} min
              </p>
            </div>
            <button
              onClick={onCerrar}
              className="w-8 h-8 rounded-lg flex items-center justify-center
                         text-slate-400 hover:text-slate-600 dark:hover:text-slate-300
                         hover:bg-slate-100 dark:hover:bg-slate-700
                         transition-colors text-lg leading-none"
              aria-label="Cerrar"
            >
              ×
            </button>
          </div>

          {/* ── Score display ── */}
          <div className={`rounded-xl border p-5 text-center transition-colors
                           duration-300 ${cfg.bg} ${cfg.border}`}>
            <p className="text-4xl mb-3 leading-none">{cfg.emoji}</p>
            <p className={`text-5xl font-bold leading-none tracking-tight
                           transition-colors duration-300 ${cfg.color}`}>
              {score}
              <span className="text-xl font-medium text-slate-400
                               dark:text-slate-500 ml-1">
                /10
              </span>
            </p>
            <p className={`text-sm font-semibold mt-2 transition-colors
                           duration-300 ${cfg.color}`}>
              {cfg.label}
            </p>
          </div>

          {/* ── Slider ── */}
          <div className="space-y-3">
            <input
              type="range"
              min="0" max="10" step="0.5"
              value={score}
              onChange={e => setScore(parseFloat(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />

            {/* Marcas del slider */}
            <div className="flex justify-between">
              {[0, 2, 4, 6, 8, 10].map(n => (
                <button
                  key={n}
                  onClick={() => setScore(n)}
                  className={`text-[10px] font-mono font-semibold transition-colors
                               cursor-pointer
                               ${score === n
                                 ? "text-indigo-600 dark:text-indigo-400"
                                 : "text-slate-300 dark:text-slate-600 hover:text-slate-400"
                               }`}
                >
                  {n}
                </button>
              ))}
            </div>

            <div className="flex justify-between text-[10px] text-slate-400
                            dark:text-slate-500">
              <span>No entendí nada</span>
              <span>Perfecto</span>
            </div>
          </div>

          {/* ── Error ── */}
          {error && (
            <div className="rounded-xl bg-red-50 dark:bg-red-950/40 border
                            border-red-200 dark:border-red-900/60 px-4 py-3">
              <p className="text-xs font-semibold text-red-600 dark:text-red-400
                             text-center">
                {error}
              </p>
            </div>
          )}

          {/* ── Botones ── */}
          <div className="flex gap-3 pt-1">
            <button
              onClick={onCerrar}
              className="flex-1 py-2.5 rounded-xl border border-slate-200
                         dark:border-slate-700 text-slate-600 dark:text-slate-400
                         text-sm font-semibold hover:bg-slate-50
                         dark:hover:bg-slate-700/50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={guardarSesion}
              disabled={guardando}
              className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500
                         dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white
                         text-sm font-semibold transition-all duration-150
                         disabled:opacity-40 disabled:cursor-not-allowed
                         shadow-sm hover:shadow-md active:scale-[0.98]
                         inline-flex items-center justify-center gap-2"
            >
              {guardando ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/40
                                  border-t-white rounded-full animate-spin" />
                  Guardando…
                </>
              ) : (
                "Guardar sesión"
              )}
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}