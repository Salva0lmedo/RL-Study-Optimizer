# ============================================================
# models.py
# Modelos ORM — definen las tablas de la base de datos
#
# Estructura:
#   Usuario → Dominio → Item (nuevo sistema universal)
#   Usuario → Asignatura → Sesion (sistema original, sin cambios)
# ============================================================

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.api.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String, nullable=False)
    creado_en  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones existentes
    asignaturas = relationship("Asignatura", back_populates="usuario")
    sesiones    = relationship("Sesion",     back_populates="usuario")

    # Relaciones nuevas
    dominios    = relationship("Dominio", back_populates="usuario")


class Asignatura(Base):
    """Tabla original — no se modifica."""
    __tablename__ = "asignaturas"

    id                = Column(Integer, primary_key=True, index=True)
    usuario_id        = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nombre            = Column(String,  nullable=False)
    dificultad        = Column(Float, default=0.5)
    estabilidad       = Column(Float, default=2.0)
    dias_desde_repaso = Column(Float, default=0.0)

    usuario  = relationship("Usuario",  back_populates="asignaturas")
    sesiones = relationship("Sesion",   back_populates="asignatura")


class Sesion(Base):
    """Tabla original — no se modifica."""
    __tablename__ = "sesiones"

    id               = Column(Integer, primary_key=True, index=True)
    usuario_id       = Column(Integer, ForeignKey("usuarios.id"),    nullable=False)
    asignatura_id    = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    duracion_min     = Column(Integer, nullable=False)
    score            = Column(Float, nullable=True)
    retencion_antes  = Column(Float, nullable=True)
    retencion_despues = Column(Float, nullable=True)
    creada_en        = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    usuario    = relationship("Usuario",    back_populates="sesiones")
    asignatura = relationship("Asignatura", back_populates="sesiones")


# ── NUEVAS TABLAS ─────────────────────────────────────────────────────────────

# Catálogo de tipos de dominio disponibles
TIPOS_DOMINIO = [
    "Idiomas",
    "Música",
    "Medicina",
    "Oposiciones",
    "Deporte",
    "Programación",
    "Otro"
]


class Dominio(Base):
    """
    Un dominio es el área general de conocimiento o habilidad.
    Ejemplos: Idiomas, Música, Medicina, Oposiciones...

    Un usuario puede tener múltiples dominios activos.
    """
    __tablename__ = "dominios"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Tipo del dominio (del catálogo TIPOS_DOMINIO)
    tipo        = Column(String, nullable=False)

    # Nombre personalizado por el usuario
    # Ej: tipo="Idiomas", nombre="Japonés N5"
    nombre      = Column(String, nullable=False)

    # Descripción opcional
    descripcion = Column(Text, nullable=True)

    creado_en   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    usuario  = relationship("Usuario", back_populates="dominios")
    items    = relationship("Item",    back_populates="dominio",
                           cascade="all, delete-orphan")


class Item(Base):
    """
    Un ítem es la unidad mínima de conocimiento o habilidad dentro de un dominio.

    Ejemplos por dominio:
      Idiomas:       "猫 = gato" (japonés), "être = ser/estar" (francés)
      Música:        "Acorde de Do Mayor", "Escala pentatónica menor"
      Medicina:      "Fémur = hueso más largo del cuerpo"
      Oposiciones:   "Artículo 14 de la Constitución"
      Deporte:       "Sentadilla — técnica correcta"
      Programación:  "List comprehension en Python"

    Cada ítem tiene sus propios parámetros de Ebbinghaus independientes.
    """
    __tablename__ = "items"

    id         = Column(Integer, primary_key=True, index=True)
    dominio_id = Column(Integer, ForeignKey("dominios.id"), nullable=False)

    # Contenido del ítem
    pregunta   = Column(Text, nullable=False)   # Lo que se muestra al estudiar
    respuesta  = Column(Text, nullable=True)    # La respuesta correcta (opcional)

    # Subdominio para agrupar ítems dentro del dominio
    # Ej: dentro de "Japonés N5" → subdominio "Verbos", "Sustantivos", "Partículas"
    subdominio = Column(String, nullable=True)

    # Dificultad estimada (0.1 a 0.9)
    dificultad = Column(Float, default=0.5)

    # Parámetros de Ebbinghaus — se actualizan con cada sesión
    estabilidad       = Column(Float, default=2.0)
    dias_desde_repaso = Column(Float, default=0.0)

    # Número de veces que se ha practicado este ítem
    veces_practicado  = Column(Integer, default=0)

    creado_en  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dominio         = relationship("Dominio", back_populates="items")
    sesiones_item   = relationship("SesionItem", back_populates="item")


class SesionItem(Base):
    """
    Registra cada vez que el usuario practica un ítem específico.
    Es el equivalente a Sesion pero a nivel de ítem individual.
    """
    __tablename__ = "sesiones_item"

    id               = Column(Integer, primary_key=True, index=True)
    item_id          = Column(Integer, ForeignKey("items.id"), nullable=False)
    usuario_id       = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    score            = Column(Float, nullable=False)   # 0-10
    retencion_antes  = Column(Float, nullable=True)
    retencion_despues = Column(Float, nullable=True)
    creada_en        = Column(DateTime,
                              default=lambda: datetime.now(timezone.utc))

    item    = relationship("Item",    back_populates="sesiones_item")
    usuario = relationship("Usuario")