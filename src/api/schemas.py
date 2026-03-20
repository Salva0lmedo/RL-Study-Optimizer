# ============================================================
# schemas.py
# Schemas Pydantic — validan los datos que entran y salen de la API
#
# ¿Qué hace este archivo?
# Define la forma exacta que deben tener los datos en cada
# request y response. Pydantic valida automáticamente los tipos
# y devuelve errores claros si algo no es correcto.
# ============================================================

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Schemas de Usuario ───────────────────────────────────────────────────────

class UsuarioCrear(BaseModel):
    """Datos necesarios para crear un usuario nuevo."""
    nombre: str = Field(..., min_length=1, max_length=50)


class UsuarioRespuesta(BaseModel):
    """Datos que devuelve la API al consultar un usuario."""
    id:        int
    nombre:    str
    creado_en: datetime

    class Config:
        from_attributes = True  # Permite crear desde objetos SQLAlchemy


# ── Schemas de Asignatura ────────────────────────────────────────────────────

class AsignaturaCrear(BaseModel):
    """Datos para crear una asignatura."""
    nombre:     str   = Field(..., min_length=1, max_length=100)
    dificultad: float = Field(..., ge=0.0, le=1.0)  # ge=mayor o igual, le=menor o igual


class AsignaturaRespuesta(BaseModel):
    """Datos que devuelve la API al consultar una asignatura."""
    id:                int
    nombre:            str
    dificultad:        float
    estabilidad:       float
    dias_desde_repaso: float

    class Config:
        from_attributes = True


# ── Schemas de Sesión ────────────────────────────────────────────────────────

class SesionCrear(BaseModel):
    """
    Datos para registrar una sesión completada.
    El alumno indica cuánto estudió y se pone una nota.
    """
    usuario_id:    int
    asignatura_id: int
    duracion_min:  int   = Field(..., ge=30, le=90)   # Entre 30 y 90 minutos
    score:         float = Field(..., ge=0.0, le=10.0) # Nota del 0 al 10


class SesionRespuesta(BaseModel):
    """Datos que devuelve la API al registrar una sesión."""
    id:               int
    asignatura_id:    int
    duracion_min:     int
    score:            float
    retencion_antes:  Optional[float]
    retencion_despues: Optional[float]
    creada_en:        datetime

    class Config:
        from_attributes = True


# ── Schemas de Recomendación ─────────────────────────────────────────────────

class RecomendacionRespuesta(BaseModel):
    """
    Lo que devuelve el agente PPO cuando se le pregunta qué estudiar hoy.
    Es el endpoint más importante de toda la API.
    """
    asignatura_id:       int
    nombre_asignatura:   str
    duracion_minutos:    int
    retencion_estimada:  float   # Retención actual de esa asignatura (0-1)
    urgencia:            float   # 1 - retención (0=tranquilo, 1=urgente)
    dificultad:          float


# ── Schemas de Estadísticas ──────────────────────────────────────────────────

class EstadisticasRespuesta(BaseModel):
    """Resumen del estado actual del estudiante."""
    retencion_media:      float
    asignatura_mas_urgente: str
    total_sesiones:       int
    minutos_totales:      int
    asignaturas:          list[AsignaturaRespuesta]


# ── Schemas de Dominio ────────────────────────────────────────────────────────

class DominioCrear(BaseModel):
    """Datos para crear un dominio nuevo."""
    tipo:        str = Field(..., min_length=1, max_length=50)
    nombre:      str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


class DominioRespuesta(BaseModel):
    """Datos que devuelve la API al consultar un dominio."""
    id:          int
    tipo:        str
    nombre:      str
    descripcion: Optional[str]
    total_items: int = 0   # Calculado dinámicamente

    class Config:
        from_attributes = True


# ── Schemas de Item ───────────────────────────────────────────────────────────

class ItemCrear(BaseModel):
    """Datos para crear un ítem nuevo."""
    pregunta:   str   = Field(..., min_length=1)
    respuesta:  Optional[str] = None
    subdominio: Optional[str] = None
    dificultad: float = Field(0.5, ge=0.0, le=1.0)


class ItemRespuesta(BaseModel):
    """Datos que devuelve la API al consultar un ítem."""
    id:               int
    pregunta:         str
    respuesta:        Optional[str]
    subdominio:       Optional[str]
    dificultad:       float
    estabilidad:      float
    dias_desde_repaso: float
    veces_practicado: int
    retencion_actual: float = 0.0   # Calculado dinámicamente

    class Config:
        from_attributes = True


class ItemPracticar(BaseModel):
    """Datos para registrar la práctica de un ítem."""
    score: float = Field(..., ge=0.0, le=10.0)


# ── Schema de Recomendación de Ítem ──────────────────────────────────────────

class RecomendacionItemRespuesta(BaseModel):
    """Lo que devuelve el agente al recomendar qué ítem practicar."""
    item_id:           int
    pregunta:          str
    respuesta:         Optional[str]
    subdominio:        Optional[str]
    dominio_nombre:    str
    dominio_tipo:      str
    retencion_estimada: float
    urgencia:          float
    dificultad:        float


# ── Schema de Estadísticas de Dominio ────────────────────────────────────────

class EstadisticasDominioRespuesta(BaseModel):
    """Resumen del estado de un dominio."""
    dominio_id:           int
    nombre:               str
    tipo:                 str
    total_items:          int
    retencion_media:      float
    item_mas_urgente:     Optional[str]
    items_en_zona_critica: int   # ítems con retención < 40%
    items:                list[ItemRespuesta]