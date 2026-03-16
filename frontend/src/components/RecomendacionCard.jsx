// ============================================================
// RecomendacionCard.jsx
// Tarjeta principal con la recomendación del agente PPO
// Muestra qué estudiar hoy y cuánto tiempo
// ============================================================

export default function RecomendacionCard({ recomendacion, onIniciarSesion }) {

  // ── Skeleton de carga ─────────────────────────────────────
  if (!recomendacion) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl border
                      border-slate-100 dark:border-slate-700/60 shadow-sm p-6
                      animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full w-1/3" />
          <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded-full w-16" />
        </div>
        <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-2/3" />
        <div className="grid grid-cols-3 gap-3">
          {[1,2,3].map(i => (
            <div key={i} className="h-16 bg-slate-100 dark:bg-slate-700/60 rounded-xl" />
          ))}
        </div>
        <div className="h-12 bg-slate-200 dark:bg-slate-700 rounded-xl" />
      </div>
    )
  }

  const urgencia  = recomendacion.urgencia
  const retencion = recomendacion.retencion_estimada

  // ── Sistema de colores semáforo ───────────────────────────
  const urgenciaConfig =
    urgencia > 0.6
      ? {
          badge:    "bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400",
          bar:      "bg-red-500",
          label:    "Urgente",
          dot:      "bg-red-500",
          accentBorder: "border-red-200 dark:border-red-900/60",
        }
      : urgencia > 0.3
      ? {
          badge:    "bg-amber-100 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400",
          bar:      "bg-amber-400",
          label:    "Moderada",
          dot:      "bg-amber-400",
          accentBorder: "border-amber-200 dark:border-amber-900/60",
        }
      : {
          badge:    "bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400",
          bar:      "bg-emerald-500",
          label:    "Normal",
          dot:      "bg-emerald-500",
          accentBorder: "border-emerald-200 dark:border-emerald-900/60",
        }

  const urgenciaPct = (urgencia * 100).toFixed(0)
  const retencionPct = (retencion * 100).toFixed(1)
  const dificultad  = (recomendacion.dificultad * 10).toFixed(0)

  // ── Dots de dificultad (escala 1–10 → 5 puntos) ──────────
  const totalDots = 5
  const dotsActivos = Math.round(recomendacion.dificultad * 10 / 2)

  return (
    <div className={`bg-white dark:bg-slate-800 rounded-2xl shadow-sm overflow-hidden
                     border ${urgenciaConfig.accentBorder}`}>

      {/* Barra de acento superior */}
      <div className={`h-1 w-full ${urgenciaConfig.bar}`} />

      <div className="p-6 space-y-5">

        {/* ── Cabecera ── */}
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold uppercase tracking-widest
                        text-slate-400 dark:text-slate-500">
            Recomendación del agente
          </p>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1
                            rounded-full text-[11px] font-semibold
                            ${urgenciaConfig.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${urgenciaConfig.dot}`} />
            {urgenciaConfig.label} · {urgenciaPct}%
          </span>
        </div>

        {/* ── Asignatura ── */}
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900
                         dark:text-slate-50 leading-none mb-1">
            {recomendacion.nombre_asignatura}
          </h2>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Agente PPO · sesión recomendada para hoy
          </p>
        </div>

        {/* ── Métricas ── */}
        <div className="grid grid-cols-3 gap-3">

          {/* Duración */}
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-3 space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-widest
                          text-slate-400 dark:text-slate-500">
              Duración
            </p>
            <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400
                          leading-none">
              {recomendacion.duracion_minutos}
            </p>
            <p className="text-[11px] text-slate-400">minutos</p>
          </div>

          {/* Retención */}
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-3 space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-widest
                          text-slate-400 dark:text-slate-500">
              Retención
            </p>
            <p className="text-2xl font-bold text-violet-600 dark:text-violet-400
                          leading-none">
              {retencionPct}
            </p>
            <p className="text-[11px] text-slate-400">% estimada</p>
          </div>

          {/* Dificultad */}
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-3 space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-widest
                          text-slate-400 dark:text-slate-500">
              Dificultad
            </p>
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-200
                          leading-none">
              {dificultad}
              <span className="text-sm font-medium text-slate-400">/10</span>
            </p>
            <div className="flex gap-0.5 mt-0.5">
              {Array.from({ length: totalDots }).map((_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-colors ${
                    i < dotsActivos
                      ? "bg-indigo-500 dark:bg-indigo-400"
                      : "bg-slate-200 dark:bg-slate-600"
                  }`}
                />
              ))}
            </div>
          </div>

        </div>

        {/* ── Barra de urgencia ── */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-semibold uppercase tracking-widest
                             text-slate-400 dark:text-slate-500">
              Nivel de urgencia
            </span>
            <span className="text-[11px] font-semibold text-slate-500
                             dark:text-slate-400 font-mono">
              {urgenciaPct}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-700 rounded-full
                          overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700
                          ${urgenciaConfig.bar}`}
              style={{ width: `${urgenciaPct}%` }}
            />
          </div>
        </div>

        {/* ── Botón ── */}
        <button
          onClick={onIniciarSesion}
          className="w-full py-3 px-6 rounded-xl font-semibold text-sm text-white
                     bg-indigo-600 hover:bg-indigo-500 dark:bg-indigo-500
                     dark:hover:bg-indigo-400 transition-all duration-150
                     shadow-sm hover:shadow-md active:scale-[0.98]
                     tracking-wide"
        >
          Iniciar sesión de estudio
        </button>

      </div>
    </div>
  )
}