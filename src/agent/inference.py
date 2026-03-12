# ============================================================
# inference.py
# Consultar al agente entrenado qué estudiar hoy
#
# ¿Qué hace este archivo?
# Carga el modelo PPO entrenado y pregunta al agente
# qué asignatura recomienda estudiar hoy y cuánto tiempo.
#
# Ejecutar con: python src/agent/inference.py
# ============================================================

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

from src.environment.study_env import StudyEnv
from configurar_asignaturas import cargar_configuracion


def cargar_agente():
    """
    Carga el modelo PPO y el normalizador desde disco.
    """
    config = cargar_configuracion()

    def make_env():
        env = StudyEnv(
            n_topics=config["n_topics"],
            difficulties=config["dificultades"]
        )
        return Monitor(env)

    # Cargar entorno con el normalizador entrenado
    env = DummyVecEnv([make_env])
    env = VecNormalize.load("models/vec_normalize.pkl", env)
    env.training = False      # No actualizar estadísticas en inferencia
    env.norm_reward = False   # No normalizar recompensas en inferencia

    # Cargar el mejor modelo (no el final — el mejor durante el entrenamiento)
    model = PPO.load("models/best/best_model", env=env)

    return model, env, config


def recomendar_hoy():
    """
    Pregunta al agente qué estudiar hoy y muestra la recomendación.
    """
    print("\n" + "="*55)
    print("  RL STUDY OPTIMIZER — Recomendación de hoy")
    print("="*55)

    model, env, config = cargar_agente()

    # Obtener observación inicial
    obs = env.reset()

    # El agente toma su decisión de forma determinista
    # deterministic=True = sin exploración, la mejor acción conocida
    action, _ = model.predict(obs, deterministic=True)

    # Interpretar la acción
    topic_idx    = int(action[0][0])
    duration_idx = int(action[0][1])
    duraciones   = [30, 60, 90]
    duration_min = duraciones[duration_idx]

    nombre_asignatura = config["nombres"][topic_idx]
    dificultad        = config["dificultades"][topic_idx]

    # Mostrar la recomendación
    print(f"\n  📚 Asignatura recomendada: {nombre_asignatura}")
    print(f"  ⏱️  Duración sugerida:      {duration_min} minutos")
    print(f"  🎯 Dificultad:             {dificultad} / 1.0")
    print()
    print("  El agente ha decidido esto basándose en:")
    print(f"    → Es la asignatura con mayor urgencia ponderada")
    print(f"    → {duration_min} minutos es la duración óptima según")
    print(f"       su dificultad ({dificultad}) y el tiempo disponible")
    print("="*55 + "\n")


if __name__ == "__main__":
    recomendar_hoy()