// ============================================================
// App.jsx
// Componente principal — dashboard directo sin onboarding
//
// ¿Qué hace este archivo?
// Lee el usuario_id desde /usuario_id.json generado por
// configurar_asignaturas.py. Si no existe, muestra error
// indicando que hay que ejecutar el script primero.
// ============================================================

import { useState, useEffect, useCallback } from "react"
import axios from "axios"

import Header            from "./components/Header"
import RecomendacionCard from "./components/RecomendacionCard"
import RetentionChart    from "./components/RetentionChart"
import AsignaturasList   from "./components/AsignaturasList"
import SessionModal      from "./components/SessionModal"

const API = "http://localhost:8000"

export default function App() {
  const [usuarioId,     setUsuarioId]     = useState(null)
  const [recomendacion, setRecomendacion] = useState(null)
  const [estadisticas,  setEstadisticas]  = useState(null)
  const [mostrarModal,  setMostrarModal]  = useState(false)
  const [cargando,      setCargando]      = useState(true)
  const [error,         setError]         = useState(null)
  const [avanzando,     setAvanzando]     = useState(false)

  // ── Al montar: leer usuario_id generado por configurar_asignaturas.py ────
  useEffect(() => {
    const inicializar = async () => {
      try {
        // Primero intentar leer desde localStorage (sesiones anteriores)
        const idGuardado = localStorage.getItem("usuario_id")

        if (idGuardado) {
          // Verificar que el usuario sigue existiendo en la BD
          try {
            await axios.get(`${API}/api/usuarios/${idGuardado}`)
            setUsuarioId(parseInt(idGuardado))
            return
          } catch {
            // El usuario ya no existe en la BD — borrar localStorage
            // y leer desde el archivo JSON
            localStorage.removeItem("usuario_id")
          }
        }

        // Leer el usuario_id generado por configurar_asignaturas.py
        // El archivo está en frontend/public/usuario_id.json
        const res = await axios.get("/usuario_id.json")
        const id  = res.data.usuario_id

        // Guardarlo en localStorage para las próximas visitas
        localStorage.setItem("usuario_id", id)
        setUsuarioId(id)

      } catch (e) {
        // El archivo usuario_id.json no existe todavía
        setError(
          "No se encontró ningún usuario configurado. " +
          "Ejecuta primero: python configurar_asignaturas.py"
        )
        setCargando(false)
      }
    }
    inicializar()
  }, [])

  // ── Cargar datos del backend ──────────────────────────────────────────────
  const cargarDatos = useCallback(async () => {
    if (!usuarioId) return
    setCargando(true)
    setError(null)
    try {
      const [resRec, resStats] = await Promise.all([
        axios.get(`${API}/api/usuarios/${usuarioId}/recomendar`),
        axios.get(`${API}/api/usuarios/${usuarioId}/estadisticas`)
      ])
      setRecomendacion(resRec.data)
      setEstadisticas(resStats.data)
    } catch (e) {
      setError("No se pudo conectar con el backend. ¿Está arrancado el servidor?")
    } finally {
      setCargando(false)
    }
  }, [usuarioId])

  useEffect(() => {
    if (usuarioId) cargarDatos()
  }, [usuarioId, cargarDatos])

  // ── Avanzar día ───────────────────────────────────────────────────────────
  const avanzarDia = async () => {
    setAvanzando(true)
    try {
      await axios.post(`${API}/api/usuarios/${usuarioId}/avanzar-dia`)
      await cargarDatos()
    } catch (e) {
      console.error("Error al avanzar día", e)
    } finally {
      setAvanzando(false)
    }
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-100">

      <Header retencionMedia={estadisticas?.retencion_media ?? 0} />

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">

        {/* Error — incluye instrucción clara si falta configuración */}
        {error && (
          <div className="bg-red-50 border border-red-300 rounded-2xl p-6 text-red-700">
            <p className="font-bold text-lg mb-2">⚠️ {error}</p>
            <p className="text-sm text-red-500">
              Una vez ejecutado el script, recarga esta página.
            </p>
          </div>
        )}

        {cargando && !error && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-3">🤖</p>
            <p>El agente está pensando…</p>
          </div>
        )}

        {!cargando && !error && (
          <>
            <RecomendacionCard
              recomendacion={recomendacion}
              onIniciarSesion={() => setMostrarModal(true)}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <RetentionChart asignaturas={estadisticas?.asignaturas} />
              <AsignaturasList asignaturas={estadisticas?.asignaturas} />
            </div>

            <div className="flex justify-end">
              <button
                onClick={avanzarDia}
                disabled={avanzando}
                className="bg-gray-700 hover:bg-gray-600 text-white text-sm
                           font-semibold px-4 py-2 rounded-xl transition-colors
                           disabled:opacity-50"
              >
                {avanzando ? "Avanzando…" : "⏭️ Simular día siguiente"}
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Sesiones totales",   valor: estadisticas?.total_sesiones        ?? 0,   unidad: "" },
                { label: "Minutos estudiados",  valor: estadisticas?.minutos_totales       ?? 0,   unidad: "min" },
                { label: "Más urgente",         valor: estadisticas?.asignatura_mas_urgente ?? "—", unidad: "" }
              ].map(({ label, valor, unidad }) => (
                <div key={label} className="bg-white rounded-2xl shadow p-4 text-center">
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

      {mostrarModal && recomendacion && (
        <SessionModal
          recomendacion={recomendacion}
          usuarioId={usuarioId}
          onCerrar={() => setMostrarModal(false)}
          onSesionGuardada={cargarDatos}
        />
      )}

    </div>
  )
}