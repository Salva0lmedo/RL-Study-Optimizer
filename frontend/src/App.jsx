// ============================================================
// App.jsx
// Componente principal — orquesta todo el dashboard
//
// ¿Qué hace este archivo?
// Carga los datos del backend, los pasa a los componentes hijos
// y gestiona el estado global de la aplicación.
// ============================================================

import { useState, useEffect, useCallback } from "react"
import axios from "axios"

import Header            from "./components/Header"
import RecomendacionCard from "./components/RecomendacionCard"
import RetentionChart    from "./components/RetentionChart"
import AsignaturasList   from "./components/AsignaturasList"
import SessionModal      from "./components/SessionModal"

const API        = "http://localhost:8000"
const USUARIO_ID = 1   // ← tu ID de usuario

export default function App() {
  // ── Estado de la aplicación ──────────────────────────────────────────────
  const [recomendacion, setRecomendacion] = useState(null)
  const [estadisticas,  setEstadisticas]  = useState(null)
  const [mostrarModal,  setMostrarModal]  = useState(false)
  const [cargando,      setCargando]      = useState(true)
  const [error,         setError]         = useState(null)
  const [avanzando,     setAvanzando]     = useState(false)  // ← AÑADIDO

  // ── Cargar datos del backend ─────────────────────────────────────────────
  const cargarDatos = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      // Llamadas paralelas al backend para mayor velocidad
      const [resRec, resStats] = await Promise.all([
        axios.get(`${API}/api/usuarios/${USUARIO_ID}/recomendar`),
        axios.get(`${API}/api/usuarios/${USUARIO_ID}/estadisticas`)
      ])
      setRecomendacion(resRec.data)
      setEstadisticas(resStats.data)
    } catch (e) {
      setError("No se pudo conectar con el backend. ¿Está arrancado el servidor?")
    } finally {
      setCargando(false)
    }
  }, [])

  // ── Avanzar día ──────────────────────────────────────────────────────────
  const avanzarDia = async () => {          // ← AÑADIDO
    setAvanzando(true)
    try {
      await axios.post(`${API}/api/usuarios/${USUARIO_ID}/avanzar-dia`)
      await cargarDatos()  // Recargar el dashboard tras avanzar
    } catch (e) {
      console.error("Error al avanzar día", e)
    } finally {
      setAvanzando(false)
    }
  }

  // Cargar datos al montar el componente
  useEffect(() => {
    cargarDatos()
  }, [cargarDatos])

  // ── Renderizado ──────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-100">

      {/* Cabecera */}
      <Header retencionMedia={estadisticas?.retencion_media ?? 0} />

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">

        {/* Error de conexión */}
        {error && (
          <div className="bg-red-50 border border-red-300 rounded-2xl p-4 text-red-700">
            ⚠️ {error}
          </div>
        )}

        {/* Indicador de carga */}
        {cargando && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-3">🤖</p>
            <p>El agente está pensando…</p>
          </div>
        )}

        {!cargando && !error && (
          <>
            {/* Tarjeta de recomendación del agente */}
            <RecomendacionCard
              recomendacion={recomendacion}
              onIniciarSesion={() => setMostrarModal(true)}
            />

            {/* Fila de dos columnas: gráfica + lista */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <RetentionChart
                asignaturas={estadisticas?.asignaturas}
              />
              <AsignaturasList
                asignaturas={estadisticas?.asignaturas}
              />
            </div>

            {/* Botón avanzar día */}
            <div className="flex justify-end">
              <button
                onClick={avanzarDia}
                disabled={avanzando}
                className="bg-gray-700 hover:bg-gray-600 text-white text-sm font-semibold
                           px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
              >
                {avanzando ? "Avanzando…" : "⏭️ Simular día siguiente"}
              </button>
            </div>

            {/* Resumen numérico */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Sesiones totales",   valor: estadisticas?.total_sesiones       ?? 0,   unidad: "" },
                { label: "Minutos estudiados",  valor: estadisticas?.minutos_totales      ?? 0,   unidad: "min" },
                { label: "Más urgente",         valor: estadisticas?.asignatura_mas_urgente ?? "—", unidad: "" }
              ].map(({ label, valor, unidad }) => (
                <div key={label}
                  className="bg-white rounded-2xl shadow p-4 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                    {label}
                  </p>
                  <p className="text-2xl font-bold text-blue-800">
                    {valor}{unidad && <span className="text-sm ml-1">{unidad}</span>}
                  </p>
                </div>
              ))}
            </div>
          </>
        )}

      </main>

      {/* Modal de registro de sesión */}
      {mostrarModal && recomendacion && (
        <SessionModal
          recomendacion={recomendacion}
          usuarioId={USUARIO_ID}
          onCerrar={() => setMostrarModal(false)}
          onSesionGuardada={cargarDatos}
        />
      )}

    </div>
  )
}