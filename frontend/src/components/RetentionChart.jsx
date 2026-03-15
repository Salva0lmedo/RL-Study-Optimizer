// ============================================================
// RetentionChart.jsx
// Gráfica de barras con la retención estimada por asignatura
// Usa Recharts para renderizar la visualización
// ============================================================

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from "recharts"

// Tooltip personalizado que muestra más información al pasar el ratón
function TooltipPersonalizado({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-sm">
      <p className="font-bold text-gray-800 mb-1">{d.nombre}</p>
      <p className="text-blue-700">Retención: <b>{(d.retencion * 100).toFixed(1)}%</b></p>
      <p className="text-gray-500">Dificultad: {(d.dificultad * 10).toFixed(0)}/10</p>
      <p className="text-gray-500">Días sin repasar: {d.dias.toFixed(0)}d</p>
    </div>
  )
}

export default function RetentionChart({ asignaturas }) {
  if (!asignaturas?.length) return null

  // Preparar datos para Recharts
  const datos = asignaturas.map(a => {
    const retencion = Math.exp(-a.dias_desde_repaso / Math.max(a.estabilidad, 0.1))
    return {
      nombre: a.nombre.length > 10 ? a.nombre.substring(0, 10) + "…" : a.nombre,
      nombreCompleto: a.nombre,
      retencion: parseFloat(retencion.toFixed(3)),
      dificultad: a.dificultad,
      dias: a.dias_desde_repaso
    }
  }).sort((a, b) => a.retencion - b.retencion) // Ordenar de menor a mayor retención

  // Color de cada barra según retención
  const getColor = (retencion) => {
    if (retencion > 0.7) return "#22c55e"  // verde
    if (retencion > 0.4) return "#eab308"  // amarillo
    return "#ef4444"                        // rojo
  }

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1">
        Retención por asignatura
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        Ordenadas de más olvidada a más fresca · Ebbinghaus R(t) = e^(-t/S)
      </p>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={datos} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="nombre"
            tick={{ fontSize: 11, fill: "#6b7280" }}
          />
          <YAxis
            tickFormatter={v => `${(v * 100).toFixed(0)}%`}
            domain={[0, 1]}
            tick={{ fontSize: 11, fill: "#6b7280" }}
          />
          {/* Línea de referencia en el 50% */}
          <ReferenceLine y={0.5} stroke="#94a3b8" strokeDasharray="4 4"
            label={{ value: "50%", position: "right", fontSize: 10, fill: "#94a3b8" }} />
          <Tooltip content={<TooltipPersonalizado />} />
          <Bar dataKey="retencion" radius={[6, 6, 0, 0]}>
            {datos.map((entry, index) => (
              <Cell key={index} fill={getColor(entry.retencion)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Leyenda */}
      <div className="flex gap-4 mt-2 justify-center text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500 inline-block" />
          Bien (&gt;70%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" />
          Atención (40-70%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
          Urgente (&lt;40%)
        </span>
      </div>
    </div>
  )
}