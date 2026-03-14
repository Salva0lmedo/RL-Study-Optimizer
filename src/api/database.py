# ============================================================
# database.py
# Configuración de la conexión a la base de datos SQLite
#
# ¿Qué hace este archivo?
# Crea el motor de base de datos y la sesión que usarán
# el resto de archivos para leer y escribir datos.
# SQLite guarda todo en un único archivo local (study_optimizer.db)
# sin necesidad de instalar ningún servidor de base de datos.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ruta del archivo de base de datos SQLite
# Se creará automáticamente en la raíz del proyecto
DATABASE_URL = "sqlite:///./study_optimizer.db"

# create_engine crea la conexión a la base de datos
# check_same_thread=False es necesario para FastAPI porque
# puede manejar múltiples requests en hilos distintos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal es la clase que usaremos para crear sesiones
# Cada request de la API abrirá y cerrará su propia sesión
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base es la clase padre de todos nuestros modelos ORM
# Los modelos heredan de Base para que SQLAlchemy los registre
Base = declarative_base()


def get_db():
    """
    Generador de sesiones de base de datos.
    FastAPI lo usa como dependencia en cada endpoint.
    Garantiza que la sesión se cierra aunque haya un error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()