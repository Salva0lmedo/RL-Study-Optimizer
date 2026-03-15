// ============================================================
// Header.jsx
// Cabecera de la aplicación
// ============================================================

export default function Header({ retencionMedia }) {
  // Color de la barra según la retención media
  const colorBarra =
    retencionMedia > 0.7 ? "bg-green-500" :
    retencionMedia > 0.4 ? "bg-yellow-500" :
    "bg-red-500"

  return (
    <header className="bg-blue-900 text-white px-6 py-4 shadow-lg">
      <div className="max-w-4xl mx-auto flex items-center justify-between">

        {/* Título */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            RL Study Optimizer
          </h1>
          <p className="text-blue-300 text-sm mt-0.5">
            Optimizador de estudio con Reinforcement Learning
          </p>
        </div>

        {/* Indicador de retención media global */}
        <div className="text-right">
          <p className="text-blue-300 text-xs uppercase tracking-wide mb-1">
            Retención media
          </p>
          <p className="text-3xl font-bold">
            {(retencionMedia * 100).toFixed(0)}%
          </p>
          {/* Barra de progreso */}
          <div className="w-32 h-2 bg-blue-800 rounded-full mt-1">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${colorBarra}`}
              style={{ width: `${retencionMedia * 100}%` }}
            />
          </div>
        </div>

      </div>
    </header>
  )
}