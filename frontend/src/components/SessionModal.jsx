// ============================================================
// SessionModal.jsx
// Modal para registrar el score tras una sesión de estudio
// El alumno indica del 0 al 10 cómo le fue en la sesión
// ============================================================

import { useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

export default function SessionModal({ recomendacion, usuarioId, onCerrar, onSesionGuardada }) {
  const [score, setScore]       = useState(5)
  const [guardando, setGuardando] = useState(false)
  const [error, setError]       = useState(null)

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
      onSesionGuardada()  // Recargar datos en el dashboard
      onCerrar()
    } catch (e) {
      setError("Error al guardar la sesión. Inténtalo de nuevo.")
    } finally {
      setGuardando(false)
    }
  }

  // Emoji y color según el score
  const getEmojiScore = (s) => {
    if (s >= 8) return "🌟"
    if (s >= 6) return "😊"
    if (s >= 4) return "😐"
    return "😓"
  }

  return (
    // Fondo oscuro
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center
                    justify-center z-50 px-4">

      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">

        {/* Cabecera */}
        <h2 className="text-2xl font-bold text-gray-800 mb-1">
          ¿Cómo fue la sesión?
        </h2>
        <p className="text-gray-500 text-sm mb-6">
          {recomendacion.nombre_asignatura} ·{" "}
          {recomendacion.duracion_minutos} minutos
        </p>

        {/* Selector de score */}
        <div className="text-center mb-6">
          <p className="text-6xl mb-3">{getEmojiScore(score)}</p>
          <p className="text-5xl font-bold text-blue-800 mb-1">{score}</p>
          <p className="text-gray-500 text-sm">sobre 10</p>

          {/* Slider */}
          <input
            type="range"
            min="0" max="10" step="0.5"
            value={score}
            onChange={e => setScore(parseFloat(e.target.value))}
            className="w-full mt-4 accent-blue-800"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0 — No entendí nada</span>
            <span>10 — Perfecto</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <p className="text-red-500 text-sm text-center mb-4">{error}</p>
        )}

        {/* Botones */}
        <div className="flex gap-3">
          <button
            onClick={onCerrar}
            className="flex-1 py-3 rounded-xl border border-gray-300
                       text-gray-600 hover:bg-gray-50 transition-colors font-semibold"
          >
            Cancelar
          </button>
          <button
            onClick={guardarSesion}
            disabled={guardando}
            className="flex-1 py-3 rounded-xl bg-blue-800 hover:bg-blue-700
                       text-white font-bold transition-colors disabled:opacity-50"
          >
            {guardando ? "Guardando…" : "Guardar sesión"}
          </button>
        </div>

      </div>
    </div>
  )
}