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
# Esto crea el archivo study_optimizer.db con todas las tablas
# si no existe todavía. Si ya existe, no hace nada.
models.Base.metadata.create_all(bind=engine)

# ── Inicializar FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="RL Study Optimizer API",
    description="Backend del optimizador de estudio con Reinforcement Learning",
    version="1.0.0"
)

# ── CORS: permite que el frontend React se comunique con la API ───────────────
# Sin esto, el navegador bloquearía las peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # En producción limitaríamos a la URL del frontend
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Cargar el agente PPO al arrancar la API ───────────────────────────────────
# Lo cargamos una sola vez al iniciar para que sea rápido en cada request
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


# ════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/")
def raiz():
    """Comprueba que la API está funcionando."""
    return {"estado": "ok", "mensaje": "RL Study Optimizer API funcionando"}


# ── Usuarios ──────────────────────────────────────────────────────────────────
@app.post("/api/usuarios", response_model=schemas.UsuarioRespuesta)
def crear_usuario(datos: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario.
    Ejemplo de uso desde el navegador (Swagger UI):
        POST /api/usuarios
        Body: {"nombre": "Salvador"}
    """
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
    """Lista todas las asignaturas de un usuario con su estado actual."""
    return crud.obtener_asignaturas(db, usuario_id)


# ── Recomendación del agente ──────────────────────────────────────────────────
@app.get("/api/usuarios/{usuario_id}/recomendar",
         response_model=schemas.RecomendacionRespuesta)
def recomendar(usuario_id: int, db: Session = Depends(get_db)):
    """
    Pregunta al agente PPO qué asignatura estudiar hoy y cuánto tiempo.
    Este es el endpoint más importante de la API.
    """
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    asignaturas = crud.obtener_asignaturas(db, usuario_id)
    if not asignaturas:
        raise HTTPException(status_code=400,
                            detail="El usuario no tiene asignaturas. "
                                   "Añade asignaturas primero.")

    # Construir el vector de estado actual del estudiante
    estado = crud.construir_vector_estado(db, usuario_id)

    # Pedir recomendación al agente
    obs = _vec_env.normalize_obs(estado.reshape(1, -1))
    accion, _ = agente.predict(obs, deterministic=True)

    topic_idx    = int(accion[0][0])
    duration_idx = int(accion[0][1])
    duraciones   = [30, 60, 90]

    # Asegurarse de que el índice no supera el número de asignaturas reales
    topic_idx = min(topic_idx, len(asignaturas) - 1)
    asignatura = asignaturas[topic_idx]

    # Calcular retención y urgencia actuales
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
    El alumno indica cuánto estudió y se pone una nota del 0 al 10.
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
    En producción esto se llamaría automáticamente cada 24 horas.
    """
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    crud.avanzar_dias(db, usuario_id)
    return {"estado": "ok", "mensaje": "Día avanzado correctamente"}