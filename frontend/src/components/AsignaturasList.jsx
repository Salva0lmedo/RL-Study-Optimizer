// ============================================================
// AsignaturasList.jsx
// Lista detallada de todas las asignaturas con su estado
// ============================================================

export default function AsignaturasList({ asignaturas }) {
  if (!asignaturas?.length) return null

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border
                    border-slate-100 dark:border-slate-700/60 shadow-sm
                    overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-4
                      border-b border-slate-100 dark:border-slate-700/60">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          Estado de asignaturas
        </h3>
        <span className="text-[10px] font-semibold uppercase tracking-widest
                         text-slate-400 dark:text-slate-500 bg-slate-100
                         dark:bg-slate-700 px-2.5 py-1 rounded-full">
          {asignaturas.length} materias
        </span>
      </div>

      {/* ── Lista ── */}
      <div className="divide-y divide-slate-50 dark:divide-slate-700/40">
        {asignaturas.map(a => {
          const retencion = Math.exp(
            -a.dias_desde_repaso / Math.max(a.estabilidad, 0.1)
          )
          const urgencia = 1 - retencion

          // Semáforo de retención
          const colorConfig =
            retencion > 0.7
              ? {
                  bar:    "bg-emerald-500",
                  dot:    "bg-emerald-500",
                  pct:    "text-emerald-600 dark:text-emerald-400",
                  badge:  "bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400",
                  label:  "Buena",
                }
              : retencion > 0.4
              ? {
                  bar:    "bg-amber-400",
                  dot:    "bg-amber-400",
                  pct:    "text-amber-600 dark:text-amber-400",
                  badge:  "bg-amber-100 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400",
                  label:  "Repasar",
                }
              : {
                  bar:    "bg-red-500",
                  dot:    "bg-red-500",
                  pct:    "text-red-600 dark:text-red-400",
                  badge:  "bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400",
                  label:  "Urgente",
                }

          const dias       = a.dias_desde_repaso.toFixed(0)
          const dificultad = (a.dificultad * 10).toFixed(0)
          const totalDots  = 5
          const dotsActivos = Math.round(a.dificultad * 10 / 2)

          return (
            <div
              key={a.id}
              className="group flex items-center gap-4 px-5 py-3.5
                         hover:bg-slate-50 dark:hover:bg-slate-700/30
                         transition-colors duration-100"
            >

              {/* Dot de estado */}
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${colorConfig.dot}`} />

              {/* Nombre + barra */}
              <div className="flex-1 min-w-0 space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-800
                                   dark:text-slate-200 truncate">
                    {a.nombre}
                  </span>
                  <span className={`text-[11px] font-bold font-mono flex-shrink-0
                                    ${colorConfig.pct}`}>
                    {(retencion * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Barra de retención */}
                <div className="h-1 w-full bg-slate-100 dark:bg-slate-700
                                rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700
                                ${colorConfig.bar}`}
                    style={{ width: `${retencion * 100}%` }}
                  />
                </div>
              </div>

              {/* Metadatos — visibles siempre en desktop, compactos en mobile */}
              <div className="flex-shrink-0 flex flex-col items-end gap-1.5">

                {/* Badge de estado */}
                <span className={`text-[10px] font-semibold px-2 py-0.5
                                  rounded-full ${colorConfig.badge}`}>
                  {colorConfig.label}
                </span>

                {/* Días + dificultad */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 dark:text-slate-500
                                   font-mono">
                    {dias}d
                  </span>
                  <div className="flex gap-0.5">
                    {Array.from({ length: totalDots }).map((_, i) => (
                      <div
                        key={i}
                        className={`w-1 h-1 rounded-full ${
                          i < dotsActivos
                            ? "bg-indigo-400 dark:bg-indigo-500"
                            : "bg-slate-200 dark:bg-slate-600"
                        }`}
                      />
                    ))}
                  </div>
                </div>

              </div>

            </div>
          )
        })}
      </div>

    </div>
  )
}