// ============================================================
// RecomendacionCard.jsx
// Tarjeta principal con la recomendación del agente PPO
// Muestra qué estudiar hoy y cuánto tiempo
// ============================================================

export default function RecomendacionCard({ recomendacion, onIniciarSesion }) {
  if (!recomendacion) {
    return (
      <div className="bg-white rounded-2xl shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
        <div className="h-8 bg-gray-200 rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-200 rounded w-1/4" />
      </div>
    )
  }

  const urgencia = recomendacion.urgencia
  const retencion = recomendacion.retencion_estimada

  // Color del borde según urgencia
  const colorBorde =
    urgencia > 0.6 ? "border-red-400 bg-red-50" :
    urgencia > 0.3 ? "border-yellow-400 bg-yellow-50" :
    "border-green-400 bg-green-50"

  const colorUrgencia =
    urgencia > 0.6 ? "text-red-600" :
    urgencia > 0.3 ? "text-yellow-600" :
    "text-green-600"

  const emoji =
    urgencia > 0.6 ? "🔴" :
    urgencia > 0.3 ? "⚠️" :
    "✅"

  return (
    <div className={`rounded-2xl shadow border-2 p-6 ${colorBorde}`}>

      {/* Cabecera */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
          {emoji} Recomendación del agente para hoy
        </p>
        <span className={`text-sm font-bold ${colorUrgencia}`}>
          Urgencia: {(urgencia * 100).toFixed(0)}%
        </span>
      </div>

      {/* Asignatura */}
      <h2 className="text-3xl font-bold text-gray-800 mb-1">
        {recomendacion.nombre_asignatura}
      </h2>

      {/* Detalles */}
      <div className="flex gap-6 mt-3 mb-5">
        <div>
          <p className="text-xs text-gray-500">Duración</p>
          <p className="text-xl font-bold text-blue-800">
            {recomendacion.duracion_minutos} min
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Retención actual</p>
          <p className="text-xl font-bold text-blue-800">
            {(retencion * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Dificultad</p>
          <p className="text-xl font-bold text-blue-800">
            {(recomendacion.dificultad * 10).toFixed(0)}/10
          </p>
        </div>
      </div>

      {/* Botón */}
      <button
        onClick={onIniciarSesion}
        className="w-full bg-blue-800 hover:bg-blue-700 text-white font-bold
                   py-3 px-6 rounded-xl transition-colors duration-200 text-lg"
      >
        Iniciar sesión de estudio
      </button>

    </div>
  )
}