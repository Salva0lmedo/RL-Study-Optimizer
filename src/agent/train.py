# ============================================================
# train.py
# Entrenamiento del agente PPO con Stable-Baselines3
#
# ¿Qué hace este archivo?
# Carga tu configuración de asignaturas, crea el entorno
# Gymnasium y entrena un agente PPO durante 500.000 steps.
# El agente aprende qué asignatura repasar cada día y
# cuánto tiempo dedicarle para maximizar la retención.
#
# Ejecutar con: python src/agent/train.py
# ============================================================

import os
import sys

# Añadir la raíz del proyecto al path para encontrar src/ y configurar_asignaturas.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
import torch

from src.environment.study_env import StudyEnv
from configurar_asignaturas import cargar_configuracion

# ── 1. Cargar la configuración de asignaturas ────────────────────────────────
# Lee el config_asignaturas.json que generaste con configurar_asignaturas.py
print("\n" + "="*60)
print("  RL STUDY OPTIMIZER — Entrenamiento del Agente PPO")
print("="*60)

config = cargar_configuracion()

print(f"\n  Asignaturas cargadas ({config['n_topics']}):")
for nombre, dif in zip(config["nombres"], config["dificultades"]):
    barra = int(dif * 10) * "█" + (10 - int(dif * 10)) * "░"
    print(f"    {nombre:<20} {barra}  ({dif})")

# ── 2. Crear carpetas necesarias ─────────────────────────────────────────────
os.makedirs("models/best",        exist_ok=True)
os.makedirs("models/checkpoints", exist_ok=True)
os.makedirs("logs",               exist_ok=True)
os.makedirs("tensorboard_logs",   exist_ok=True)

# ── 3. Definir la función que crea el entorno ────────────────────────────────
# DummyVecEnv necesita una función (no una instancia) para crear el entorno.
# Usamos Monitor para registrar estadísticas de cada episodio (recompensa, duración).
def make_env():
    """
    Crea una instancia del entorno con TUS asignaturas y dificultades.
    Monitor envuelve el entorno para guardar logs automáticamente.
    """
    env = StudyEnv(
        n_topics=config["n_topics"],
        max_daily_minutes=180,
        difficulties=config["dificultades"]   # ← tus asignaturas reales
    )
    env = Monitor(env, filename="logs/monitor")
    return env

# ── 4. Crear el entorno vectorizado ─────────────────────────────────────────
# DummyVecEnv ejecuta N entornos en paralelo (aquí 4).
# Más entornos = más experiencias por update = entrenamiento más estable.
# Con 4 entornos, el agente ve 4 episodios simultáneos en cada step.
print("\n  Creando entornos vectorizados (x4)...")
vec_env = DummyVecEnv([make_env] * 4)

# VecNormalize normaliza las observaciones y recompensas automáticamente.
# Esto es MUY importante para la estabilidad del entrenamiento:
#   - Sin normalización, valores muy distintos confunden a la red neuronal
#   - norm_obs=True: normaliza el vector de observación (media 0, std 1)
#   - norm_reward=True: normaliza las recompensas
#   - clip_obs=10.0: recorta observaciones extremas
vec_env = VecNormalize(
    vec_env,
    norm_obs=True,
    norm_reward=True,
    clip_obs=10.0
)

# ── 5. Entorno de evaluación separado ────────────────────────────────────────
# Usamos un entorno distinto para evaluar el agente durante el entrenamiento.
# Es importante que sea independiente del entorno de entrenamiento para
# que las métricas de evaluación sean honestas.
eval_env = DummyVecEnv([make_env])
eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10.0)
# ── 6. Definir los callbacks ─────────────────────────────────────────────────
# Los callbacks son funciones que se ejecutan automáticamente durante el
# entrenamiento en momentos específicos (cada N steps, al final, etc.)

# EvalCallback: evalúa el agente cada 5.000 steps y guarda el mejor modelo
eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="models/best/",   # Guarda aquí el mejor modelo
    log_path="logs/",                       # Guarda logs de evaluación
    eval_freq=5000,                         # Evaluar cada 5.000 steps
    n_eval_episodes=20,                     # Usar 20 episodios para la evaluación
    deterministic=True,                     # Sin aleatoriedad en la evaluación
    verbose=1
)

# CheckpointCallback: guarda el modelo cada 50.000 steps como respaldo
# Si el entrenamiento falla a mitad, puedes retomarlo desde el último checkpoint
checkpoint_callback = CheckpointCallback(
    save_freq=50000,
    save_path="models/checkpoints/",
    name_prefix="ppo_study"
)

# ── 7. Definir el agente PPO ─────────────────────────────────────────────────
print("  Creando agente PPO...")
print(f"  Dispositivo: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}\n")

model = PPO(
    policy="MlpPolicy",    # Red neuronal MLP (Multi-Layer Perceptron)
                           # Es la política estándar para espacios de observación
                           # continuos como el nuestro (vector de floats)
    env=vec_env,

    # ── Hiperparámetros de aprendizaje ──
    learning_rate=3e-4,    # Tasa de aprendizaje del optimizador Adam
                           # 3e-4 = 0.0003, valor estándar y robusto para PPO

    n_steps=2048,          # Pasos de experiencia que se recogen antes de cada update
                           # Con 4 entornos paralelos: 4 × 2048 = 8.192 experiencias por update

    batch_size=64,         # Tamaño del minibatch para el SGD
                           # Debe ser divisor de (n_steps × n_envs) = 8.192

    n_epochs=10,           # Veces que se reutiliza cada batch de experiencias
                           # PPO puede reutilizar datos (a diferencia de otros RL)

    # ── Hiperparámetros de recompensa ──
    gamma=0.99,            # Factor de descuento: cuánto valora el agente el futuro
                           # 0.99 = visión a largo plazo (ideal para nuestro problema)
                           # 0.9  = visión cortoplacista

    gae_lambda=0.95,       # GAE lambda: balance entre sesgo y varianza en las ventajas
                           # 1.0 = sin sesgo pero alta varianza
                           # 0.0 = bajo varianza pero alto sesgo
                           # 0.95 = balance estándar probado empíricamente

    # ── Hiperparámetros de estabilidad PPO ──
    clip_range=0.2,        # Clipping de PPO: limita cuánto puede cambiar la política
                           # en cada update. Evita actualizaciones destructivas.
                           # 0.2 significa que la nueva política no puede alejarse
                           # más del 20% de la política anterior

    ent_coef=0.01,         # Coeficiente de entropía: incentiva la exploración
                           # Sin esto el agente converge demasiado rápido a una
                           # política subóptima (se queda "en un mínimo local")

    vf_coef=0.5,           # Peso del error del Crítico en la pérdida total
                           # El Crítico estima V(s), el Actor decide la acción

    max_grad_norm=0.5,     # Gradient clipping: evita gradientes explosivos
                           # Especialmente útil al inicio del entrenamiento

    # ── Arquitectura de la red neuronal ──
    policy_kwargs=dict(
        net_arch=[256, 256],          # 2 capas ocultas de 256 neuronas cada una
                                       # Suficiente para nuestro problema (7 temas × 5 features = 35 inputs)
        activation_fn=torch.nn.ReLU   # ReLU es la activación estándar para MLP en RL
    ),

    verbose=1,                         # Mostrar progreso durante el entrenamiento
    tensorboard_log="tensorboard_logs/"  # Para visualizar métricas con TensorBoard
)

# ── 8. Mostrar resumen del agente ────────────────────────────────────────────
print("  Arquitectura del agente:")
print(f"    Entradas:      {config['n_topics'] * 5} neuronas "
      f"({config['n_topics']} asignaturas × 5 features)")
print(f"    Capas ocultas: 256 → 256 neuronas (ReLU)")
print(f"    Salidas Actor: {config['n_topics']} temas × 3 duraciones "
      f"= {config['n_topics'] * 3} acciones posibles")
print(f"    Salida Crítico: 1 valor (V(s))\n")

# ── 9. Entrenar el agente ────────────────────────────────────────────────────
TOTAL_STEPS = 500_000   # Steps totales de entrenamiento
                         # Con 4 entornos paralelos, el agente verá
                         # 500.000 / 7 días ≈ 71.428 episodios completos

print(f"  Iniciando entrenamiento: {TOTAL_STEPS:,} steps...")
print(f"  Episodios aproximados:   {TOTAL_STEPS // 7:,}")
print(f"  Tiempo estimado en CPU:  10-20 minutos")
print("="*60 + "\n")

model.learn(
    total_timesteps=TOTAL_STEPS,
    callback=[eval_callback, checkpoint_callback],
    progress_bar=True    # Barra de progreso en la terminal
)

# ── 10. Guardar el modelo y el normalizador ───────────────────────────────────
# Es CRÍTICO guardar también el VecNormalize junto al modelo.
# Sin él, las observaciones en inferencia tendrán una escala diferente
# a la del entrenamiento y el agente tomará decisiones incorrectas.
print("\n" + "="*60)
print("  Entrenamiento completado. Guardando modelo...")

model.save("models/ppo_study_optimizer")
vec_env.save("models/vec_normalize.pkl")

print("  ✅ Modelo guardado en:      models/ppo_study_optimizer.zip")
print("  ✅ Normalizador guardado en: models/vec_normalize.pkl")
print("="*60)
print() 