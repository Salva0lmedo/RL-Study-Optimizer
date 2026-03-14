# ============================================================
# models.py
# Modelos ORM — definen las tablas de la base de datos
#
# ¿Qué hace este archivo?
# Define la estructura de las tablas usando clases Python.
# SQLAlchemy traduce estas clases a SQL automáticamente.
# Tenemos 3 tablas: usuarios, asignaturas y sesiones de estudio.
# ============================================================

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.api.database import Base


class Usuario(Base):
    """
    Tabla de usuarios.
    Por ahora solo tendremos un usuario (tú),
    pero la estructura permite escalar a más usuarios en el futuro.
    """
    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String, nullable=False)
    creado_en  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones: un usuario tiene muchas asignaturas y sesiones
    asignaturas = relationship("Asignatura", back_populates="usuario")
    sesiones    = relationship("Sesion",     back_populates="usuario")


class Asignatura(Base):
    """
    Tabla de asignaturas del estudiante.
    Almacena la dificultad definida por el alumno y los parámetros
    de Ebbinghaus que se actualizan con cada sesión de estudio.
    """
    __tablename__ = "asignaturas"

    id                = Column(Integer, primary_key=True, index=True)
    usuario_id        = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nombre            = Column(String,  nullable=False)

    # Dificultad definida por el alumno (0.1 a 0.9)
    dificultad        = Column(Float, default=0.5)

    # Parámetro S de Ebbinghaus — aumenta con cada repaso exitoso
    estabilidad       = Column(Float, default=2.0)

    # Días desde el último repaso — se actualiza en cada sesión
    dias_desde_repaso = Column(Float, default=0.0)

    usuario  = relationship("Usuario",  back_populates="asignaturas")
    sesiones = relationship("Sesion",   back_populates="asignatura")


class Sesion(Base):
    """
    Tabla de sesiones de estudio completadas.
    Registra cada vez que el alumno estudia una asignatura,
    cuánto tiempo dedicó y qué nota se puso a sí mismo.
    Esta tabla es la memoria histórica del sistema.
    """
    __tablename__ = "sesiones"

    id              = Column(Integer, primary_key=True, index=True)
    usuario_id      = Column(Integer, ForeignKey("usuarios.id"),    nullable=False)
    asignatura_id   = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    duracion_min    = Column(Integer, nullable=False)

    # Score que el alumno se da a sí mismo tras la sesión (0.0 a 10.0)
    # Es la señal de feedback más importante para actualizar la dificultad
    score           = Column(Float, nullable=True)

    # Retención estimada antes y después de la sesión (Ebbinghaus)
    retencion_antes  = Column(Float, nullable=True)
    retencion_despues = Column(Float, nullable=True)

    creada_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    usuario    = relationship("Usuario",    back_populates="sesiones")
    asignatura = relationship("Asignatura", back_populates="sesiones")