// ============================================================
// Dominios.jsx
// Página de gestión del sistema universal de dominios e ítems
// ============================================================

import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://localhost:8000"

// Iconos por tipo de dominio
const ICONOS = {
  "Idiomas":       "🌍",
  "Música":        "🎵",
  "Medicina":      "🩺",
  "Oposiciones":   "📋",
  "Deporte":       "⚽",
  "Programación":  "💻",
  "Otro":          "📚"
}

const COLORES = {
  "Idiomas":       "bg-blue-50 border-blue-200",
  "Música":        "bg-purple-50 border-purple-200",
  "Medicina":      "bg-red-50 border-red-200",
  "Oposiciones":   "bg-yellow-50 border-yellow-200",
  "Deporte":       "bg-green-50 border-green-200",
  "Programación":  "bg-gray-50 border-gray-200",
  "Otro":          "bg-orange-50 border-orange-200"
}

export default function Dominios({ usuarioId }) {
  const [dominios,       setDominios]       = useState([])
  const [tipos,          setTipos]          = useState([])
  const [dominioActivo,  setDominioActivo]  = useState(null)
  const [items,          setItems]          = useState([])
  const [recomendacion,  setRecomendacion]  = useState(null)
  const [vista,          setVista]          = useState("dominios") // dominios | items | practicar
  const [cargando,       setCargando]       = useState(false)
  const [mostrarFormDom, setMostrarFormDom] = useState(false)
  const [mostrarFormItem,setMostrarFormItem]= useState(false)
  const [score,          setScore]          = useState(5)
  const [practicando,    setPracticando]    = useState(false)
  const [respuestaVisible, setRespuestaVisible] = useState(false)

  // ── Form nuevo dominio ────────────────────────────────────────────────────
  const [formDom, setFormDom] = useState({
    tipo: "Idiomas", nombre: "", descripcion: ""
  })

  // ── Form nuevo ítem ───────────────────────────────────────────────────────
  const [formItem, setFormItem] = useState({
    pregunta: "", respuesta: "", subdominio: "", dificultad: 0.5
  })

  // ── Cargar tipos y dominios al montar ─────────────────────────────────────
  useEffect(() => {
    cargarTipos()
    cargarDominios()
  }, [usuarioId])

  const cargarTipos = async () => {
    const res = await axios.get(`${API}/api/dominios/tipos`)
    setTipos(res.data.tipos)
  }

  const cargarDominios = async () => {
    setCargando(true)
    try {
      const res = await axios.get(`${API}/api/usuarios/${usuarioId}/dominios`)
      setDominios(res.data)
    } finally {
      setCargando(false)
    }
  }

  const cargarItems = async (dominioId) => {
    const res = await axios.get(`${API}/api/dominios/${dominioId}/items`)
    setItems(res.data)
  }

  // ── Crear dominio ─────────────────────────────────────────────────────────
  const crearDominio = async () => {
    if (!formDom.nombre.trim()) return
    await axios.post(`${API}/api/usuarios/${usuarioId}/dominios`, formDom)
    setFormDom({ tipo: "Idiomas", nombre: "", descripcion: "" })
    setMostrarFormDom(false)
    cargarDominios()
  }

  // ── Eliminar dominio ──────────────────────────────────────────────────────
  const eliminarDominio = async (dominioId) => {
    if (!confirm("¿Eliminar este dominio y todos sus ítems?")) return
    await axios.delete(`${API}/api/dominios/${dominioId}`)
    cargarDominios()
  }

  // ── Entrar a un dominio ───────────────────────────────────────────────────
  const entrarDominio = async (dominio) => {
    setDominioActivo(dominio)
    await cargarItems(dominio.id)
    setVista("items")
  }

  // ── Crear ítem ────────────────────────────────────────────────────────────
  const crearItem = async () => {
    if (!formItem.pregunta.trim()) return
    await axios.post(`${API}/api/dominios/${dominioActivo.id}/items`, formItem)
    setFormItem({ pregunta: "", respuesta: "", subdominio: "", dificultad: 0.5 })
    setMostrarFormItem(false)
    cargarItems(dominioActivo.id)
  }

  // ── Pedir recomendación y practicar ───────────────────────────────────────
  const iniciarPractica = async () => {
    const res = await axios.get(
      `${API}/api/dominios/${dominioActivo.id}/recomendar`
    )
    setRecomendacion(res.data)
    setRespuestaVisible(false)
    setScore(5)
    setVista("practicar")
  }

  const guardarPractica = async () => {
    setPracticando(true)
    try {
      await axios.post(
        `${API}/api/items/${recomendacion.item_id}/practicar?usuario_id=${usuarioId}`,
        { score }
      )
      // Volver a pedir recomendación para el siguiente ítem
      const res = await axios.get(
        `${API}/api/dominios/${dominioActivo.id}/recomendar`
      )
      setRecomendacion(res.data)
      setRespuestaVisible(false)
      setScore(5)
      cargarItems(dominioActivo.id)
    } finally {
      setPracticando(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  // ── Vista: Lista de dominios ──────────────────────────────────────────────
  if (vista === "dominios") return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

      {/* Cabecera */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Mis Dominios</h2>
          <p className="text-sm text-gray-500 mt-1">
            Áreas de conocimiento y habilidad que estás trabajando
          </p>
        </div>
        <button
          onClick={() => setMostrarFormDom(true)}
          className="bg-blue-800 hover:bg-blue-700 text-white font-bold
                     px-4 py-2 rounded-xl transition-colors text-sm"
        >
          + Nuevo dominio
        </button>
      </div>

      {/* Formulario nuevo dominio */}
      {mostrarFormDom && (
        <div className="bg-white rounded-2xl shadow border border-gray-200 p-6 space-y-4">
          <h3 className="font-bold text-gray-800">Nuevo dominio</h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Tipo
              </label>
              <select
                value={formDom.tipo}
                onChange={e => setFormDom({...formDom, tipo: e.target.value})}
                className="w-full border border-gray-200 rounded-xl px-3 py-2
                           text-sm focus:border-blue-400 focus:outline-none"
              >
                {tipos.map(t => (
                  <option key={t} value={t}>{ICONOS[t]} {t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Nombre
              </label>
              <input
                type="text"
                value={formDom.nombre}
                onChange={e => setFormDom({...formDom, nombre: e.target.value})}
                placeholder="Ej: Japonés N5, Guitarra clásica..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2
                           text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
              Descripción (opcional)
            </label>
            <input
              type="text"
              value={formDom.descripcion}
              onChange={e => setFormDom({...formDom, descripcion: e.target.value})}
              placeholder="Breve descripción..."
              className="w-full border border-gray-200 rounded-xl px-3 py-2
                         text-sm focus:border-blue-400 focus:outline-none"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setMostrarFormDom(false)}
              className="flex-1 py-2 border border-gray-200 rounded-xl
                         text-gray-500 hover:bg-gray-50 text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={crearDominio}
              disabled={!formDom.nombre.trim()}
              className="flex-1 py-2 bg-blue-800 hover:bg-blue-700 text-white
                         font-bold rounded-xl transition-colors text-sm
                         disabled:opacity-40"
            >
              Crear dominio
            </button>
          </div>
        </div>
      )}

      {/* Lista de dominios */}
      {cargando ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-3">🧠</p>
          <p>Cargando dominios...</p>
        </div>
      ) : dominios.length === 0 ? (
        <div className="text-center py-16 text-gray-400 bg-white rounded-2xl shadow">
          <p className="text-5xl mb-4">🌱</p>
          <p className="font-semibold text-lg">Aún no tienes dominios</p>
          <p className="text-sm mt-2">Crea tu primer dominio para empezar</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dominios.map(d => (
            <div
              key={d.id}
              className={`rounded-2xl border-2 p-5 cursor-pointer
                          hover:shadow-md transition-shadow ${COLORES[d.tipo] || COLORES["Otro"]}`}
              onClick={() => entrarDominio(d)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{ICONOS[d.tipo] || "📚"}</span>
                  <div>
                    <p className="font-bold text-gray-800">{d.nombre}</p>
                    <p className="text-xs text-gray-500">{d.tipo}</p>
                  </div>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); eliminarDominio(d.id) }}
                  className="text-gray-300 hover:text-red-400 transition-colors
                             text-lg leading-none"
                >
                  ×
                </button>
              </div>

              {d.descripcion && (
                <p className="text-sm text-gray-500 mt-3">{d.descripcion}</p>
              )}

              <div className="flex items-center justify-between mt-4">
                <span className="text-sm font-semibold text-gray-600">
                  {d.total_items} ítems
                </span>
                <span className="text-xs text-gray-400">
                  Toca para ver →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // ── Vista: Ítems del dominio ──────────────────────────────────────────────
  if (vista === "items") return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

      {/* Cabecera */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setVista("dominios")}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ← Volver
          </button>
          <span className="text-2xl">{ICONOS[dominioActivo.tipo]}</span>
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              {dominioActivo.nombre}
            </h2>
            <p className="text-sm text-gray-500">{items.length} ítems</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMostrarFormItem(true)}
            className="border border-blue-800 text-blue-800 hover:bg-blue-50
                       font-bold px-3 py-2 rounded-xl transition-colors text-sm"
          >
            + Añadir ítem
          </button>
          <button
            onClick={iniciarPractica}
            disabled={items.length === 0}
            className="bg-blue-800 hover:bg-blue-700 text-white font-bold
                       px-4 py-2 rounded-xl transition-colors text-sm
                       disabled:opacity-40"
          >
            ▶ Practicar
          </button>
        </div>
      </div>

      {/* Formulario nuevo ítem */}
      {mostrarFormItem && (
        <div className="bg-white rounded-2xl shadow border border-gray-200 p-6 space-y-4">
          <h3 className="font-bold text-gray-800">Nuevo ítem</h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Pregunta / Concepto
              </label>
              <input
                type="text"
                value={formItem.pregunta}
                onChange={e => setFormItem({...formItem, pregunta: e.target.value})}
                placeholder="Ej: 猫, Acorde Do Mayor, Art. 14..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2
                           text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Respuesta (opcional)
              </label>
              <input
                type="text"
                value={formItem.respuesta}
                onChange={e => setFormItem({...formItem, respuesta: e.target.value})}
                placeholder="Ej: gato, C-E-G, Igualdad..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2
                           text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Subdominio (opcional)
              </label>
              <input
                type="text"
                value={formItem.subdominio}
                onChange={e => setFormItem({...formItem, subdominio: e.target.value})}
                placeholder="Ej: Sustantivos, Escalas, Tema 3..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2
                           text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block">
                Dificultad (0.1 - 0.9)
              </label>
              <input
                type="range"
                min="0.1" max="0.9" step="0.1"
                value={formItem.dificultad}
                onChange={e => setFormItem({...formItem, dificultad: parseFloat(e.target.value)})}
                className="w-full accent-blue-800 mt-2"
              />
              <p className="text-xs text-gray-400 text-center">
                {formItem.dificultad}
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setMostrarFormItem(false)}
              className="flex-1 py-2 border border-gray-200 rounded-xl
                         text-gray-500 hover:bg-gray-50 text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={crearItem}
              disabled={!formItem.pregunta.trim()}
              className="flex-1 py-2 bg-blue-800 hover:bg-blue-700 text-white
                         font-bold rounded-xl transition-colors text-sm
                         disabled:opacity-40"
            >
              Añadir ítem
            </button>
          </div>
        </div>
      )}

      {/* Lista de ítems */}
      {items.length === 0 ? (
        <div className="text-center py-16 text-gray-400 bg-white rounded-2xl shadow">
          <p className="text-5xl mb-4">📝</p>
          <p className="font-semibold text-lg">Este dominio no tiene ítems</p>
          <p className="text-sm mt-2">Añade ítems para empezar a practicar</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map(item => {
            const color =
              item.retencion_actual > 0.7 ? "bg-green-500" :
              item.retencion_actual > 0.4 ? "bg-yellow-500" : "bg-red-500"
            const emoji =
              item.retencion_actual > 0.7 ? "✅" :
              item.retencion_actual > 0.4 ? "⚠️" : "🔴"

            return (
              <div key={item.id}
                className="bg-white rounded-xl border border-gray-100
                           shadow-sm p-4 flex items-center gap-4">
                <span className="text-lg">{emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-semibold text-gray-800 truncate">
                      {item.pregunta}
                    </p>
                    {item.subdominio && (
                      <span className="text-xs bg-gray-100 text-gray-500
                                       px-2 py-0.5 rounded-full shrink-0">
                        {item.subdominio}
                      </span>
                    )}
                  </div>
                  {item.respuesta && (
                    <p className="text-sm text-gray-500 truncate">
                      {item.respuesta}
                    </p>
                  )}
                  <div className="w-full h-1.5 bg-gray-100 rounded-full mt-2">
                    <div
                      className={`h-1.5 rounded-full ${color}`}
                      style={{ width: `${item.retencion_actual * 100}%` }}
                    />
                  </div>
                </div>
                <div className="text-right text-xs text-gray-400 shrink-0">
                  <p>{(item.retencion_actual * 100).toFixed(0)}%</p>
                  <p>{item.dias_desde_repaso.toFixed(0)}d</p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )

  // ── Vista: Practicar ítem ─────────────────────────────────────────────────
  if (vista === "practicar") return (
    <div className="max-w-lg mx-auto px-4 py-12 space-y-6">

      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => setVista("items")}
          className="text-gray-400 hover:text-gray-600"
        >
          ← Salir
        </button>
        <p className="text-sm text-gray-500">
          {ICONOS[dominioActivo.tipo]} {dominioActivo.nombre}
        </p>
      </div>

      {recomendacion && (
        <div className="bg-white rounded-2xl shadow-lg p-8 space-y-6">

          {/* Pregunta */}
          <div className="text-center">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">
              {recomendacion.subdominio || "Practicar"}
            </p>
            <p className="text-4xl font-bold text-gray-800 mb-2">
              {recomendacion.pregunta}
            </p>
            <p className="text-sm text-gray-400">
              Retención actual: {(recomendacion.retencion_estimada * 100).toFixed(0)}%
            </p>
          </div>

          {/* Respuesta oculta */}
          {!respuestaVisible ? (
            <button
              onClick={() => setRespuestaVisible(true)}
              className="w-full py-3 border-2 border-dashed border-gray-200
                         rounded-xl text-gray-400 hover:border-blue-300
                         hover:text-blue-500 transition-colors text-sm"
            >
              Mostrar respuesta
            </button>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center">
              <p className="text-lg font-semibold text-blue-800">
                {recomendacion.respuesta || "Sin respuesta definida"}
              </p>
            </div>
          )}

          {/* Score */}
          {respuestaVisible && (
            <div className="space-y-4">
              <p className="text-center text-sm font-semibold text-gray-600">
                ¿Cómo te ha ido?
              </p>
              <div className="flex justify-between text-2xl">
                {["😓", "😐", "😊", "🌟"].map((emoji, i) => {
                  const val = [2, 4, 7, 10][i]
                  return (
                    <button
                      key={i}
                      onClick={() => setScore(val)}
                      className={`p-3 rounded-xl transition-all text-3xl
                        ${score === val
                          ? "bg-blue-100 scale-110"
                          : "hover:bg-gray-100"}`}
                    >
                      {emoji}
                    </button>
                  )
                })}
              </div>
              <p className="text-center text-sm text-gray-400">
                Score: {score}/10
              </p>
              <button
                onClick={guardarPractica}
                disabled={practicando}
                className="w-full py-3 bg-blue-800 hover:bg-blue-700 text-white
                           font-bold rounded-xl transition-colors disabled:opacity-50"
              >
                {practicando ? "Guardando…" : "Siguiente ítem →"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}