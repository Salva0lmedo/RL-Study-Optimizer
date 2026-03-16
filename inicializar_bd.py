# ============================================================
# inicializar_bd.py
# Script para crear el usuario y todas las asignaturas
# automáticamente en la base de datos.
# Ejecutar con: python inicializar_bd.py
# ============================================================

import requests

API = "http://localhost:8000"

# ── 1. Crear usuario ─────────────────────────────────────────
print("Creando usuario...")
res = requests.post(f"{API}/api/usuarios", json={"nombre": "Salvador"})
usuario = res.json()
usuario_id = usuario["id"]
print(f"  ✅ Usuario creado — ID: {usuario_id}")

# ── 2. Asignaturas con dificultad equilibrada ────────────────
# La dificultad está ajustada para que el agente no ignore
# ninguna asignatura — ninguna es tan fácil que pueda olvidarse
# ni tan difícil que acapare toda la atención.
asignaturas = [
    {"nombre": "Lengua",        "dificultad": 0.4},  # Subida de 0.1 a 0.4
    {"nombre": "Ingles",        "dificultad": 0.5},  # Subida de 0.3 a 0.5
    {"nombre": "Matematicas 5", "dificultad": 0.8},  # Bajada de 0.9 a 0.8
    {"nombre": "Filosofia",     "dificultad": 0.5},  # Sin cambio
    {"nombre": "Latin",         "dificultad": 0.6},  # Bajada de 0.7 a 0.6
    {"nombre": "Frances",       "dificultad": 0.5},  # Subida de 0.3 a 0.5
    {"nombre": "Italiano 4",    "dificultad": 0.6},  # Bajada de 0.7 a 0.6
]

print("\nCreando asignaturas...")
for a in asignaturas:
    res = requests.post(
        f"{API}/api/usuarios/{usuario_id}/asignaturas",
        json=a
    )
    datos = res.json()
    barra = int(a["dificultad"] * 10) * "█" + (10 - int(a["dificultad"] * 10)) * "░"
    print(f"  ✅ {a['nombre']:<15} {barra}  ({a['dificultad']})")

# ── 3. Simular días iniciales distintos por asignatura ───────
# Esto es clave: si todas empiezan con 0 días, el agente
# no tiene información suficiente para diferenciarlas.
# Simulamos que el estudiante lleva días sin repasar algunas.
print("\nSimulando estado inicial realista...")

import requests, time

dias_por_asignatura = [3, 1, 4, 2, 5, 3, 1]  # días sin repasar por asignatura

for i in range(max(dias_por_asignatura)):
    requests.post(f"{API}/api/usuarios/{usuario_id}/avanzar-dia")

# Registrar una sesión inicial por cada asignatura para
# "resetear" las que deberían tener menos días sin repasar
asigs_res = requests.get(f"{API}/api/usuarios/{usuario_id}/asignaturas").json()

scores_iniciales = [7.0, 8.0, 6.0, 7.5, 5.5, 7.0, 8.0]

for asig, score in zip(asigs_res, scores_iniciales):
    requests.post(f"{API}/api/sesiones", json={
        "usuario_id":    usuario_id,
        "asignatura_id": asig["id"],
        "duracion_min":  60,
        "score":         score
    })

print("  ✅ Estado inicial simulado correctamente")

# ── 4. Mostrar resumen final ──────────────────────────────────
print("\n" + "="*50)
stats = requests.get(f"{API}/api/usuarios/{usuario_id}/estadisticas").json()
print(f"  Usuario ID:        {usuario_id}  ← APUNTA ESTE NÚMERO")
print(f"  Retención media:   {stats['retencion_media']*100:.1f}%")
print(f"  Más urgente:       {stats['asignatura_mas_urgente']}")
print(f"  Total sesiones:    {stats['total_sesiones']}")
print("="*50)
print(f"\n  Abre App.jsx y cambia USUARIO_ID = {usuario_id}")
print()