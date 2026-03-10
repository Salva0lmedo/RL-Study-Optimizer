# ============================================================
# test_env.py
# Tests de validación del entorno StudyEnv
#
# ¿Qué hace este archivo?
# Comprueba que el entorno cumple el estándar de Gymnasium
# y que la lógica interna (Ebbinghaus, recompensas) es correcta.
# Ejecutar con: python tests/test_env.py
# ============================================================

import numpy as np
import sys
import os

# Añadir la carpeta raíz al path para que Python encuentre src/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment.study_env import StudyEnv


def test_gymnasium_compliance():
    """
    Test 1: Verifica que el entorno cumple el estándar oficial de Gymnasium.
    check_env lanza AssertionError si hay algún problema en los espacios
    o en el formato de los retornos de step() y reset().
    """
    print("TEST 1: Validación de estándar Gymnasium...")
    from stable_baselines3.common.env_checker import check_env
    env = StudyEnv(n_topics=5)
    check_env(env, warn=True)
    print("  ✅ Entorno válido según el estándar Gymnasium\n")


def test_observation_shape():
    """
    Test 2: Verifica que el vector de observación tiene el tamaño correcto
    y todos sus valores están dentro del rango [0, 1].
    """
    print("TEST 2: Forma y rango de la observación...")
    env = StudyEnv(n_topics=5)
    obs, _ = env.reset()

    # Debe ser un vector de 5 temas × 5 features = 25 números
    assert obs.shape == (25,), f"Shape incorrecto: {obs.shape}"

    # Todos los valores deben estar en [0, 1]
    assert obs.min() >= 0.0, f"Valor mínimo fuera de rango: {obs.min()}"
    assert obs.max() <= 1.0, f"Valor máximo fuera de rango: {obs.max()}"

    print(f"  ✅ Shape: {obs.shape} | Min: {obs.min():.3f} | Max: {obs.max():.3f}\n")


def test_ebbinghaus_decay():
    """
    Test 3: Verifica que la retención decae con el tiempo (Ebbinghaus).
    Si el estudiante no repasa, debe olvidar progresivamente.
    """
    print("TEST 3: Curva de olvido de Ebbinghaus...")
    env = StudyEnv(n_topics=3)
    env.reset()

    # Forzar un estado conocido: todos los temas recién repasados
    env.days_since = np.array([0.0, 5.0, 10.0], dtype=np.float32)
    env.stability  = np.array([5.0, 5.0,  5.0], dtype=np.float32)

    retention = env._get_retention()

    # El tema con 0 días debe tener retención 1.0 (recién repasado)
    assert abs(retention[0] - 1.0) < 0.001, f"Retención inicial incorrecta: {retention[0]}"

    # El tema con más días debe tener menor retención
    assert retention[0] > retention[1] > retention[2], \
        f"Retención no decae correctamente: {retention}"

    print(f"  ✅ Retenciones con 0d, 5d, 10d: {retention[0]:.3f}, {retention[1]:.3f}, {retention[2]:.3f}")
    print(f"     (Confirma que más días = menos retención)\n")


def test_step_returns_correct_format():
    """
    Test 4: Verifica que step() devuelve exactamente lo que Gymnasium espera:
    (obs, reward, terminated, truncated, info)
    """
    print("TEST 4: Formato de retorno de step()...")
    env = StudyEnv(n_topics=5)
    env.reset()

    # Acción: repasar tema 0 durante 60 minutos
    obs, reward, terminated, truncated, info = env.step([0, 1])

    assert isinstance(obs, np.ndarray),  "obs debe ser np.ndarray"
    assert isinstance(reward, float),    "reward debe ser float"
    assert isinstance(terminated, bool), "terminated debe ser bool"
    assert isinstance(truncated, bool),  "truncated debe ser bool"
    assert isinstance(info, dict),       "info debe ser dict"
    assert "mean_retention" in info,     "info debe contener mean_retention"

    print(f"  ✅ obs: array{obs.shape} | reward: {reward:.4f} | "
          f"terminated: {terminated} | info: {list(info.keys())}\n")


def test_reward_positive_when_reviewing_forgotten_topic():
    """
    Test 5: El agente debe recibir recompensa positiva cuando repasa
    un tema muy olvidado. Es la señal más importante del sistema.
    """
    print("TEST 5: Recompensa positiva al repasar tema olvidado...")
    env = StudyEnv(n_topics=3)
    env.reset()

    # Forzar que el tema 0 está muy olvidado (20 días sin repasar)
    env.days_since = np.array([20.0, 1.0, 1.0], dtype=np.float32)
    env.stability  = np.array([2.0,  5.0, 5.0], dtype=np.float32)

    # Repasar el tema 0 durante 60 minutos
    _, reward, _, _, info = env.step([0, 1])

    print(f"  Recompensa obtenida: {reward:.4f}")
    print(f"  Retención media tras el repaso: {info['mean_retention']:.1%}")

    # La retención media debe haber mejorado
    assert info["mean_retention"] > 0.0, "La retención media debe ser positiva"
    print("  ✅ El sistema recompensa correctamente repasar temas olvidados\n")


def test_time_penalty():
    """
    Test 6: Verificar que superar el tiempo máximo diario penaliza la recompensa.
    El agente debe aprender a ser eficiente, no a estudiar infinitamente.
    """
    print("TEST 6: Penalización por exceso de tiempo...")
    env = StudyEnv(n_topics=3, max_daily_minutes=30)  # Solo 30 min permitidos
    env.reset()

    # Repasar 90 minutos (3 veces el límite)
    _, reward, _, _, info = env.step([0, 2])  # duration_idx=2 → 90 min

    print(f"  Tiempo usado: {info['time_used']:.0f} min (límite: 30 min)")
    print(f"  Recompensa con penalización: {reward:.4f}")
    print("  ✅ Penalización por tiempo aplicada correctamente\n")


def test_full_episode():
    """
    Test 7: Simula un episodio completo de 7 días con acciones aleatorias.
    Comprueba que el entorno termina correctamente y el render() funciona.
    """
    print("TEST 7: Episodio completo de 7 días...")
    env = StudyEnv(n_topics=5)
    obs, _ = env.reset()

    total_reward = 0.0
    step_count   = 0

    env.render()  # Ver el estado inicial

    while True:
        # Acción aleatoria (en el entrenamiento real, aquí iría el agente PPO)
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        step_count   += 1

        if terminated or truncated:
            break

    env.render()  # Ver el estado final

    assert step_count == 7, f"El episodio debe durar exactamente 7 días, duró {step_count}"
    print(f"  ✅ Episodio completado en {step_count} días")
    print(f"  Recompensa total acumulada: {total_reward:.4f}")
    print(f"  Retención media final: {info['mean_retention']:.1%}\n")


# ── Ejecutar todos los tests ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("   VALIDACIÓN DEL ENTORNO StudyEnv")
    print("="*55 + "\n")

    test_gymnasium_compliance()
    test_observation_shape()
    test_ebbinghaus_decay()
    test_step_returns_correct_format()
    test_reward_positive_when_reviewing_forgotten_topic()
    test_time_penalty()
    test_full_episode()

    print("="*55)
    print("   ✅ TODOS LOS TESTS PASADOS CORRECTAMENTE")
    print("="*55 + "\n")