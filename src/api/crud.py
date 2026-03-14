# ============================================================
# crud.py
# Operaciones CRUD con la base de datos
#
# ¿Qué hace este archivo?
# Contiene todas las funciones que leen y escriben en SQLite.
# CRUD = Create, Read, Update, Delete.
# Los endpoints de main.py llaman a estas funciones.
# ============================================================

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.api import models, schemas


# ── Usuario ──────────────────────────────────────────────────────────────────

def crear_usuario(db: Session, datos: schemas.UsuarioCrear) -> models.Usuario:
    """Crea un nuevo usuario en la base de datos."""
    usuario = models.Usuario(nombre=datos.nombre)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_usuario(db: Session, usuario_id: int) -> models.Usuario:
    """Obtiene un usuario por su ID."""
    return db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id
    ).first()


# ── Asignatura ───────────────────────────────────────────────────────────────

def crear_asignatura(db: Session, usuario_id: int,
                     datos: schemas.AsignaturaCrear) -> models.Asignatura:
    """Crea una nueva asignatura para un usuario."""
    asignatura = models.Asignatura(
        usuario_id=usuario_id,
        nombre=datos.nombre,
        dificultad=datos.dificultad
    )
    db.add(asignatura)
    db.commit()
    db.refresh(asignatura)
    return asignatura


def obtener_asignaturas(db: Session, usuario_id: int) -> list[models.Asignatura]:
    """Devuelve todas las asignaturas de un usuario."""
    return db.query(models.Asignatura).filter(
        models.Asignatura.usuario_id == usuario_id
    ).all()


def actualizar_estabilidad(db: Session, asignatura_id: int, score: float):
    """
    Actualiza la estabilidad de memoria de una asignatura tras una sesión.

    Cuanto mejor es el score, más aumenta la estabilidad (S de Ebbinghaus).
    La fórmula es simple: si el score es alto, la memoria se consolida más.
    """
    asignatura = db.query(models.Asignatura).filter(
        models.Asignatura.id == asignatura_id
    ).first()

    if asignatura:
        # Score normalizado a [0,1]
        score_norm = score / 10.0

        # La estabilidad aumenta proporcionalmente al score
        # Un 10/10 suma 1.0 día de estabilidad
        # Un 5/10 suma 0.5 días
        # Un 2/10 suma solo 0.2 días
        ganancia = score_norm * (1.0 - asignatura.dificultad)
        asignatura.estabilidad      += ganancia
        asignatura.dias_desde_repaso = 0.0   # Resetear el contador

        db.commit()
        db.refresh(asignatura)

    return asignatura


def avanzar_dias(db: Session, usuario_id: int):
    """
    Incrementa en 1 el contador de días de TODAS las asignaturas del usuario.
    Se llama una vez al día para simular el paso del tiempo.
    """
    db.query(models.Asignatura).filter(
        models.Asignatura.usuario_id == usuario_id
    ).update({"dias_desde_repaso": models.Asignatura.dias_desde_repaso + 1.0})
    db.commit()


# ── Sesión ───────────────────────────────────────────────────────────────────

def crear_sesion(db: Session, datos: schemas.SesionCrear) -> models.Sesion:
    """
    Registra una sesión de estudio completada.
    Calcula la retención antes y después usando Ebbinghaus.
    """
    # Obtener la asignatura para calcular retenciones
    asignatura = db.query(models.Asignatura).filter(
        models.Asignatura.id == datos.asignatura_id
    ).first()

    retencion_antes = None
    retencion_despues = None

    if asignatura:
        # Retención ANTES: R(t) = e^(-dias/estabilidad)
        retencion_antes = float(np.exp(
            -asignatura.dias_desde_repaso / max(asignatura.estabilidad, 0.1)
        ))

        # Actualizar estabilidad con el score
        actualizar_estabilidad(db, datos.asignatura_id, datos.score)

        # Volver a obtener la asignatura actualizada
        db.refresh(asignatura)

        # Retención DESPUÉS: con la nueva estabilidad y dias=0
        retencion_despues = float(np.exp(
            -0.0 / max(asignatura.estabilidad, 0.1)
        ))  # = 1.0 (recién repasado)

    sesion = models.Sesion(
        usuario_id=datos.usuario_id,
        asignatura_id=datos.asignatura_id,
        duracion_min=datos.duracion_min,
        score=datos.score,
        retencion_antes=retencion_antes,
        retencion_despues=retencion_despues
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


# ── Estado del estudiante ────────────────────────────────────────────────────

def construir_vector_estado(db: Session, usuario_id: int) -> np.ndarray:
    """
    Construye el vector de observación para el agente PPO.
    Es el mismo formato que usa el entorno Gymnasium:
    [retención, días_norm, estabilidad_norm, dificultad, urgencia] por asignatura.
    """
    asignaturas = obtener_asignaturas(db, usuario_id)

    if not asignaturas:
        return np.zeros(1, dtype=np.float32)

    features = []
    for a in asignaturas:
        dias    = a.dias_desde_repaso
        estab   = max(a.estabilidad, 0.1)
        reten   = float(np.exp(-dias / estab))
        urgency = 1.0 - reten

        features.extend([
            reten,           # [0] retención actual
            dias / 30.0,     # [1] días normalizados
            estab / 30.0,    # [2] estabilidad normalizada
            a.dificultad,    # [3] dificultad
            urgency          # [4] urgencia
        ])

    return np.array(features, dtype=np.float32)


def obtener_estadisticas(db: Session, usuario_id: int) -> dict:
    """Calcula las estadísticas generales del estudiante."""
    asignaturas = obtener_asignaturas(db, usuario_id)

    if not asignaturas:
        return {}

    retenciones = [
        float(np.exp(-a.dias_desde_repaso / max(a.estabilidad, 0.1)))
        for a in asignaturas
    ]

    # Asignatura más urgente = menor retención
    idx_urgente = int(np.argmin(retenciones))

    # Total de sesiones y minutos
    total_sesiones = db.query(func.count(models.Sesion.id)).filter(
        models.Sesion.usuario_id == usuario_id
    ).scalar() or 0

    total_minutos = db.query(func.sum(models.Sesion.duracion_min)).filter(
        models.Sesion.usuario_id == usuario_id
    ).scalar() or 0

    return {
        "retencion_media":        float(np.mean(retenciones)),
        "asignatura_mas_urgente": asignaturas[idx_urgente].nombre,
        "total_sesiones":         total_sesiones,
        "minutos_totales":        int(total_minutos),
        "asignaturas":            asignaturas
    }