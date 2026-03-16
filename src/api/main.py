# ============================================================
# main.py
# API REST con FastAPI — punto de entrada del backend
#
# ¿Qué hace este archivo?
# Define todos los endpoints de la API. Cada endpoint es una
# URL a la que el frontend (o tú desde el navegador) puede
# hacer peticiones HTTP para interactuar con el sistema.
#
# Ejecutar con: uvicorn src.api.main:app --reload --port 8000
# Documentación automática: http://localhost:8000/docs
# ============================================================

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.api.database import engine, get_db
from src.api import models, schemas, crud
from src.environment.study_env import StudyEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from configurar_asignaturas import cargar_configuracion

# ── Crear tablas en la base de datos ─────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# ── Inicializar FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="RL Study Optimizer API",
    description="Backend del optimizador de estudio con Reinforcement Learning",
    version="1.0.0"
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Cargar el agente PPO ──────────────────────────────────────────────────────
print("Cargando agente PPO...")
config = cargar_configuracion()

def make_env_api():
    env = StudyEnv(
        n_topics=config["n_topics"],
        difficulties=config["dificultades"]
    )
    return Monitor(env)

_vec_env = DummyVecEnv([make_env_api])
_vec_env = VecNormalize.load("models/vec_normalize.pkl", _vec_env)
_vec_env.training    = False
_vec_env.norm_reward = False
agente = PPO.load("models/best/best_model", env=_vec_env)
print("✅ Agente PPO cargado correctamente")


# ── Función de selección de asignatura ───────────────────────────────────────
def seleccionar_asignatura(asignaturas, estado):
    """
    Selecciona qué asignatura estudiar combinando el agente PPO
    con una puntuación de urgencia real.

    Funcionamiento:
      1. El agente PPO sugiere una asignatura basándose en el estado.
      2. Se calcula una puntuación para TODAS las asignaturas:
             score = urgencia × dificultad × factor_tiempo
         donde factor_tiempo penaliza las asignaturas que llevan
         muchos días sin repasar.
      3. Se elige la asignatura con mayor score final.

    Así el agente influye en la decisión pero no puede ignorar
    indefinidamente una asignatura muy olvidada.
    """
    n = len(asignaturas)

    # ── Paso 1: sugerencia del agente PPO ────────────────────────────────
    obs = _vec_env.normalize_obs(estado.reshape(1, -1))
    accion, _ = agente.predict(obs, deterministic=True)
    topic_ppo    = int(accion[0][0])
    duration_idx = int(accion[0][1])
    topic_ppo    = min(topic_ppo, n - 1)

    # ── Paso 2: calcular scores para todas las asignaturas ───────────────
    scores = []
    for i, a in enumerate(asignaturas):
        retencion = float(np.exp(
            -a.dias_desde_repaso / max(a.estabilidad, 0.1)
        ))
        urgencia = 1.0 - retencion

        # Factor tiempo: penaliza exponencialmente los días sin repasar
        # Una asignatura con 10 días sin repasar tiene factor 2.7x
        # Una con 1 día tiene factor 1.1x
        factor_tiempo = float(np.exp(a.dias_desde_repaso / 10.0))

        # Score base = urgencia × dificultad × factor_tiempo
        score_base = urgencia * factor_tiempo

        # Bonus si el agente PPO también eligió esta asignatura
        # Así el agente influye pero no monopoliza la decisión
        bonus_ppo = 0.3 if i == topic_ppo else 0.0

        scores.append(score_base + bonus_ppo)

    # ── Paso 3: elegir la asignatura con mayor score ──────────────────────
    topic_idx = int(np.argmax(scores))

    return topic_idx, duration_idx


# ════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.get("/")
def raiz():
    """Comprueba que la API está funcionando."""
    return {"estado": "ok", "mensaje": "RL Study Optimizer API funcionando"}


# ── Usuarios ──────────────────────────────────────────────────────────────────
@app.post("/api/usuarios", response_model=schemas.UsuarioRespuesta)
def crear_usuario(datos: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    """Crea un nuevo usuario."""
    return crud.crear_usuario(db, datos)


@app.get("/api/usuarios/{usuario_id}", response_model=schemas.UsuarioRespuesta)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtiene los datos de un usuario por su ID."""
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


# ── Asignaturas ───────────────────────────────────────────────────────────────
@app.post("/api/usuarios/{usuario_id}/asignaturas",
          response_model=schemas.AsignaturaRespuesta)
def crear_asignatura(usuario_id: int, datos: schemas.AsignaturaCrear,
                     db: Session = Depends(get_db)):
    """Añade una asignatura a un usuario."""
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return crud.crear_asignatura(db, usuario_id, datos)


@app.get("/api/usuarios/{usuario_id}/asignaturas",
         response_model=list[schemas.AsignaturaRespuesta])
def listar_asignaturas(usuario_id: int, db: Session = Depends(get_db)):
    """Lista todas las asignaturas de un usuario."""
    return crud.obtener_asignaturas(db, usuario_id)


# ── Recomendación del agente ──────────────────────────────────────────────────
@app.get("/api/usuarios/{usuario_id}/recomendar",
         response_model=schemas.RecomendacionRespuesta)
def recomendar(usuario_id: int, db: Session = Depends(get_db)):
    """
    Recomienda qué asignatura estudiar hoy combinando el agente PPO
    con una puntuación de urgencia real por asignatura.
    Garantiza que ninguna asignatura queda abandonada indefinidamente.
    """
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    asignaturas = crud.obtener_asignaturas(db, usuario_id)
    if not asignaturas:
        raise HTTPException(status_code=400,
                            detail="El usuario no tiene asignaturas.")

    # Construir vector de estado y seleccionar asignatura
    estado = crud.construir_vector_estado(db, usuario_id)
    topic_idx, duration_idx = seleccionar_asignatura(asignaturas, estado)

    duraciones = [30, 60, 90]
    asignatura = asignaturas[topic_idx]

    # Calcular retención y urgencia de la asignatura seleccionada
    retencion = float(np.exp(
        -asignatura.dias_desde_repaso / max(asignatura.estabilidad, 0.1)
    ))

    return schemas.RecomendacionRespuesta(
        asignatura_id=asignatura.id,
        nombre_asignatura=asignatura.nombre,
        duracion_minutos=duraciones[duration_idx],
        retencion_estimada=retencion,
        urgencia=1.0 - retencion,
        dificultad=asignatura.dificultad
    )


# ── Sesiones ──────────────────────────────────────────────────────────────────
@app.post("/api/sesiones", response_model=schemas.SesionRespuesta)
def registrar_sesion(datos: schemas.SesionCrear, db: Session = Depends(get_db)):
    """
    Registra una sesión de estudio completada.
    El alumno se pone una nota del 0 al 10.
    Esto actualiza la estabilidad de Ebbinghaus de la asignatura.
    """
    return crud.crear_sesion(db, datos)


# ── Estadísticas ──────────────────────────────────────────────────────────────
@app.get("/api/usuarios/{usuario_id}/estadisticas",
         response_model=schemas.EstadisticasRespuesta)
def estadisticas(usuario_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el resumen del estado actual del estudiante:
    retención media, asignatura más urgente, total de sesiones, etc.
    """
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    stats = crud.obtener_estadisticas(db, usuario_id)
    if not stats:
        raise HTTPException(status_code=400,
                            detail="El usuario no tiene asignaturas todavía.")
    return stats


# ── Avanzar día ───────────────────────────────────────────────────────────────
@app.post("/api/usuarios/{usuario_id}/avanzar-dia")
def avanzar_dia(usuario_id: int, db: Session = Depends(get_db)):
    """
    Simula el paso de un día: incrementa el contador de días
    de todas las asignaturas del usuario.
    """
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    crud.avanzar_dias(db, usuario_id)
    return {"estado": "ok", "mensaje": "Día avanzado correctamente"}