// ============================================================
// Header.jsx
// Cabecera de la aplicación
// ============================================================

export default function Header({ retencionMedia }) {

  // ── Sistema de colores semáforo ───────────────────────────
  const colorConfig =
    retencionMedia > 0.7
      ? {
          bar:   "bg-emerald-500",
          text:  "text-emerald-500 dark:text-emerald-400",
          badge: "bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400",
          label: "Buena",
        }
      : retencionMedia > 0.4
      ? {
          bar:   "bg-amber-400",
          text:  "text-amber-500 dark:text-amber-400",
          badge: "bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400",
          label: "Atención",
        }
      : {
          bar:   "bg-red-500",
          text:  "text-red-500 dark:text-red-400",
          badge: "bg-red-100 dark:bg-red-950/50 text-red-700 dark:text-red-400",
          label: "Urgente",
        }

  const pct = (retencionMedia * 100).toFixed(0)

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80
                       backdrop-blur-md border-b border-slate-100
                       dark:border-slate-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16
                      flex items-center justify-between gap-4">

        {/* ── Logo + título ── */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center
                          justify-center bg-indigo-600 dark:bg-indigo-500
                          text-white text-xs font-bold tracking-tight
                          shadow-sm select-none">
            RL
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200
                          leading-none tracking-tight">
              Study Optimizer
            </p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500
                          uppercase tracking-widest mt-0.5 leading-none">
              Reinforcement Learning · PPO
            </p>
          </div>
        </div>

        {/* ── Indicador retención media ── */}
        <div className="flex items-center gap-4">

          {/* Badge de estado */}
          <span className={`hidden sm:inline-flex items-center gap-1.5 px-2.5
                            py-1 rounded-full text-[11px] font-semibold
                            ${colorConfig.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${colorConfig.bar}`} />
            {colorConfig.label}
          </span>

          {/* Retención + barra */}
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-baseline gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-widest
                               text-slate-400 dark:text-slate-500">
                Retención media
              </span>
              <span className={`text-sm font-bold font-mono tabular-nums
                                ${colorConfig.text}`}>
                {pct}%
              </span>
            </div>
            <div className="w-28 sm:w-36 h-1 bg-slate-100 dark:bg-slate-800
                            rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700
                             ${colorConfig.bar}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

        </div>

      </div>
    </header>
  )
}