// ============================================================
// App.jsx — RL Study Optimizer
// DISEÑO ACTUALIZADO — con navegación Dashboard / Dominios
// ============================================================

import { useState, useEffect, useCallback } from "react"
import axios from "axios"

import Header            from "./components/Header"
import RecomendacionCard from "./components/RecomendacionCard"
import RetentionChart    from "./components/RetentionChart"
import AsignaturasList   from "./components/AsignaturasList"
import SessionModal      from "./components/SessionModal"
import Dominios          from "./pages/Dominios"

const API = "http://localhost:8000"

export default function App() {
  const [usuarioId,     setUsuarioId]     = useState(null)
  const [recomendacion, setRecomendacion] = useState(null)
  const [estadisticas,  setEstadisticas]  = useState(null)
  const [mostrarModal,  setMostrarModal]  = useState(false)
  const [cargando,      setCargando]      = useState(true)
  const [error,         setError]         = useState(null)
  const [avanzando,     setAvanzando]     = useState(false)
  const [paginaActual,  setPaginaActual]  = useState("dashboard")

  // ── Al montar: leer usuario_id ────────────────────────────────────────────
  useEffect(() => {
    const inicializar = async () => {
      try {
        const idGuardado = localStorage.getItem("usuario_id")
        if (idGuardado) {
          try {
            await axios.get(`${API}/api/usuarios/${idGuardado}`)
            setUsuarioId(parseInt(idGuardado))
            return
          } catch {
            localStorage.removeItem("usuario_id")
          }
        }
        const res = await axios.get("/usuario_id.json")
        const id  = res.data.usuario_id
        localStorage.setItem("usuario_id", id)
        setUsuarioId(id)
      } catch (e) {
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

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300">

      <Header retencionMedia={estadisticas?.retencion_media ?? 0} />

      {/* ── Navegación ── */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200
                      dark:border-slate-700 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex gap-1 py-2">
          <button
            onClick={() => setPaginaActual("dashboard")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors
              ${paginaActual === "dashboard"
                ? "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
              }`}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => setPaginaActual("dominios")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors
              ${paginaActual === "dominios"
                ? "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
              }`}
          >
            🧠 Dominios
          </button>
        </div>
      </div>

      {/* ── Página de Dominios ── */}
      {paginaActual === "dominios" && usuarioId && (
        <Dominios usuarioId={usuarioId} />
      )}

      {/* ── Página de Dashboard ── */}
      {paginaActual === "dashboard" && (
        <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">

          {/* ── Estado de error ── */}
          {error && (
            <div className="rounded-2xl border border-red-200 dark:border-red-900
                            bg-red-50 dark:bg-red-950/40 p-6">
              <p className="text-sm font-semibold text-red-600 dark:text-red-400 mb-1">
                Error de configuración
              </p>
              <p className="text-base font-bold text-red-700 dark:text-red-300 mb-3">
                {error}
              </p>
              <code className="text-xs bg-red-100 dark:bg-red-900/50 text-red-600
                               dark:text-red-400 px-3 py-1.5 rounded-lg font-mono">
                python configurar_asignaturas.py
              </code>
              <p className="text-xs text-red-400 dark:text-red-500 mt-3">
                Una vez ejecutado el script, recarga esta página.
              </p>
            </div>
          )}

          {/* ── Estado de carga ── */}
          {cargando && !error && (
            <div className="flex flex-col items-center justify-center py-24 gap-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-100 dark:bg-indigo-900/40
                              flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent
                                rounded-full animate-spin" />
              </div>
              <p className="text-sm text-slate-400 dark:text-slate-500">
                El agente está calculando la recomendación…
              </p>
            </div>
          )}

          {/* ── Dashboard principal ── */}
          {!cargando && !error && (
            <>
              {/* Fila superior: Recomendación + Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Recomendación ocupa 2 columnas en desktop */}
                <div className="lg:col-span-2">
                  <RecomendacionCard
                    recomendacion={recomendacion}
                    onIniciarSesion={() => setMostrarModal(true)}
                  />
                </div>

                {/* Stats verticales en desktop, grid 2x2 en mobile */}
                <div className="grid grid-cols-2 lg:grid-cols-1 gap-3">
                  {[
                    {
                      label: "Retención media",
                      valor: `${estadisticas?.retencion_media ?? 0}%`,
                      accent: "text-indigo-600 dark:text-indigo-400"
                    },
                    {
                      label: "Sesiones totales",
                      valor: estadisticas?.total_sesiones ?? 0,
                      accent: "text-violet-600 dark:text-violet-400"
                    },
                    {
                      label: "Minutos estudiados",
                      valor: estadisticas?.minutos_totales ?? 0,
                      accent: "text-slate-800 dark:text-slate-200"
                    },
                    {
                      label: "Más urgente",
                      valor: estadisticas?.asignatura_mas_urgente ?? "—",
                      accent: "text-red-500 dark:text-red-400"
                    }
                  ].map(({ label, valor, accent }) => (
                    <div
                      key={label}
                      className="bg-white dark:bg-slate-800 rounded-2xl border
                                 border-slate-100 dark:border-slate-700/60
                                 shadow-sm p-4 flex flex-col gap-1"
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-widest
                                    text-slate-400 dark:text-slate-500">
                        {label}
                      </p>
                      <p className={`text-xl font-bold leading-tight truncate ${accent}`}>
                        {valor}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fila inferior: Chart + Lista */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <RetentionChart asignaturas={estadisticas?.asignaturas} />
                <AsignaturasList asignaturas={estadisticas?.asignaturas} />
              </div>

              {/* Acción: Simular día */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={avanzarDia}
                  disabled={avanzando}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl
                             bg-slate-800 dark:bg-slate-700 hover:bg-slate-700
                             dark:hover:bg-slate-600 text-white text-sm font-semibold
                             transition-all duration-150 disabled:opacity-40
                             disabled:cursor-not-allowed shadow-sm hover:shadow-md
                             active:scale-95"
                >
                  {avanzando ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/40
                                      border-t-white rounded-full animate-spin" />
                      Avanzando…
                    </>
                  ) : (
                    <>
                      <span className="text-base">⏭</span>
                      Simular día siguiente
                    </>
                  )}
                </button>
              </div>
            </>
          )}

        </main>
      )}

      {/* ── Modal de sesión ── */}
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