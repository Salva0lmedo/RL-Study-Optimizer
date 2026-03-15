// ============================================================
// AsignaturasList.jsx
// Lista detallada de todas las asignaturas con su estado
// ============================================================

export default function AsignaturasList({ asignaturas }) {
  if (!asignaturas?.length) return null

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">
        Estado de todas las asignaturas
      </h3>

      <div className="space-y-3">
        {asignaturas.map(a => {
          const retencion = Math.exp(
            -a.dias_desde_repaso / Math.max(a.estabilidad, 0.1)
          )
          const urgencia = 1 - retencion

          const colorBarra =
            retencion > 0.7 ? "bg-green-500" :
            retencion > 0.4 ? "bg-yellow-500" :
            "bg-red-500"

          const emoji =
            retencion > 0.7 ? "✅" :
            retencion > 0.4 ? "⚠️" :
            "🔴"

          return (
            <div key={a.id}
              className="flex items-center gap-4 p-3 rounded-xl bg-gray-50
                         hover:bg-gray-100 transition-colors">

              {/* Emoji de estado */}
              <span className="text-xl">{emoji}</span>

              {/* Nombre y barra */}
              <div className="flex-1">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold text-gray-800 text-sm">
                    {a.nombre}
                  </span>
                  <span className="text-sm font-bold text-gray-600">
                    {(retencion * 100).toFixed(0)}%
                  </span>
                </div>
                {/* Barra de retención */}
                <div className="w-full h-2 bg-gray-200 rounded-full">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${colorBarra}`}
                    style={{ width: `${retencion * 100}%` }}
                  />
                </div>
              </div>

              {/* Metadatos */}
              <div className="text-right text-xs text-gray-400 w-20">
                <p>{a.dias_desde_repaso.toFixed(0)}d sin repasar</p>
                <p>Dif: {(a.dificultad * 10).toFixed(0)}/10</p>
              </div>

            </div>
          )
        })}
      </div>
    </div>
  )
}