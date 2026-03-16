// ============================================================
// RetentionChart.jsx
// Gráfica de barras con la retención estimada por asignatura
// Usa Recharts para renderizar la visualización
// ============================================================

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from "recharts"

// ── Tooltip personalizado ─────────────────────────────────────
function TooltipPersonalizado({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200
                    dark:border-slate-700 rounded-xl shadow-lg p-3 space-y-1">
      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
        {d.nombre}
      </p>
      <div className="w-full h-px bg-slate-100 dark:bg-slate-700" />
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Retención{" "}
        <span className="font-bold text-indigo-600 dark:text-indigo-400">
          {(d.retencion * 100).toFixed(1)}%
        </span>
      </p>
      <p className="text-xs text-slate-400 dark:text-slate-500">
        Dificultad · {(d.dificultad * 10).toFixed(0)}/10
      </p>
      <p className="text-xs text-slate-400 dark:text-slate-500">
        {d.dias.toFixed(0)}d sin repasar
      </p>
    </div>
  )
}

export default function RetentionChart({ asignaturas }) {
  if (!asignaturas?.length) return null

  // ── Preparar datos (lógica sin cambios) ───────────────────
  const datos = asignaturas.map(a => {
    const retencion = Math.exp(-a.dias_desde_repaso / Math.max(a.estabilidad, 0.1))
    return {
      nombre:        a.nombre.length > 10 ? a.nombre.substring(0, 10) + "…" : a.nombre,
      nombreCompleto: a.nombre,
      retencion:     parseFloat(retencion.toFixed(3)),
      dificultad:    a.dificultad,
      dias:          a.dias_desde_repaso
    }
  }).sort((a, b) => a.retencion - b.retencion)

  const getColor = (retencion) => {
    if (retencion > 0.7) return "#10b981"
    if (retencion > 0.4) return "#f59e0b"
    return "#ef4444"
  }

  const leyenda = [
    { color: "#10b981", label: "Bien",      rango: ">70%"    },
    { color: "#f59e0b", label: "Atención",  rango: "40–70%"  },
    { color: "#ef4444", label: "Urgente",   rango: "<40%"    },
  ]

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border
                    border-slate-100 dark:border-slate-700/60 shadow-sm
                    overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-start justify-between px-5 pt-5 pb-4
                      border-b border-slate-100 dark:border-slate-700/60">
        <div className="space-y-0.5">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Retención por asignatura
          </h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">
            R(t) = e<sup>(-t/S)</sup> · orden ascendente
          </p>
        </div>

        {/* Leyenda compacta en header */}
        <div className="flex items-center gap-3">
          {leyenda.map(({ color, label, rango }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="text-[10px] font-medium text-slate-400
                               dark:text-slate-500 hidden sm:inline">
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Gráfica ── */}
      <div className="px-2 pt-4 pb-3">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={datos}
            margin={{ top: 4, right: 16, left: -18, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(148,163,184,0.15)"
              vertical={false}
            />
            <XAxis
              dataKey="nombre"
              tick={{ fontSize: 11, fill: "#94a3b8", fontWeight: 500 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={v => `${(v * 100).toFixed(0)}%`}
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
              tickCount={5}
            />
            <ReferenceLine
              y={0.5}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{
                value: "50%",
                position: "right",
                fontSize: 10,
                fill: "#94a3b8",
                fontWeight: 600
              }}
            />
            <Tooltip
              content={<TooltipPersonalizado />}
              cursor={{ fill: "rgba(99,102,241,0.06)", radius: 6 }}
            />
            <Bar dataKey="retencion" radius={[5, 5, 0, 0]} maxBarSize={40}>
              {datos.map((entry, index) => (
                <Cell key={index} fill={getColor(entry.retencion)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Leyenda inferior ── */}
      <div className="flex items-center justify-center gap-5 px-5 pb-4">
        {leyenda.map(({ color, label, rango }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="text-[11px] text-slate-400 dark:text-slate-500">
              <span className="font-medium text-slate-600 dark:text-slate-400">
                {label}
              </span>
              {" "}·{" "}{rango}
            </span>
          </div>
        ))}
      </div>

    </div>
  )
}