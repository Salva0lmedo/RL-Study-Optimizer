# ============================================================
# validacion.py
# Pruebas de validación del agente PPO
#
# ¿Qué hace este archivo?
# Compara el agente PPO entrenado contra dos estrategias
# baseline durante 50 episodios simulados:
#
#   - Random:      elige tema y duración aleatoriamente
#   - Round-Robin: repasa cada tema por turnos
#   - PPO:         nuestro agente entrenado
#
# Ejecutar con: python validacion.py
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from src.environment.study_env import StudyEnv
from configurar_asignaturas import cargar_configuracion

config = cargar_configuracion()

# ── Configuración del experimento ─────────────────────────────────────────────
N_EPISODIOS = 50    # Episodios por estrategia (cada uno = 7 días)
SEED        = 42    # Semilla para reproducibilidad


def make_env():
    """Crea el entorno con las asignaturas del config."""
    env = StudyEnv(
        n_topics=config["n_topics"],
        difficulties=config["dificultades"]
    )
    return Monitor(env)


def evaluar_estrategia(nombre, get_accion_fn, n_episodios=N_EPISODIOS):
    """
    Evalúa una estrategia durante N episodios y devuelve métricas.

    Parámetros:
        nombre:        nombre de la estrategia (para mostrar)
        get_accion_fn: función que recibe (env, obs) y devuelve acción
        n_episodios:   número de episodios a simular

    Retorna:
        dict con métricas agregadas
    """
    env = make_env()

    recompensas_totales = []
    retenciones_finales = []
    retenciones_por_dia = []

    print(f"  Evaluando '{nombre}'...", end=" ", flush=True)

    for ep in range(n_episodios):
        obs, _ = env.reset()
        recompensa_ep  = 0.0
        retenciones_ep = []

        terminated = truncated = False
        while not (terminated or truncated):
            accion = get_accion_fn(env, obs)
            obs, reward, terminated, truncated, info = env.step(accion)
            recompensa_ep += reward
            retenciones_ep.append(info["mean_retention"])

        recompensas_totales.append(recompensa_ep)
        retenciones_finales.append(retenciones_ep[-1])

        if ep == 0:
            retenciones_por_dia = retenciones_ep

    media_recompensa = float(np.mean(recompensas_totales))
    media_retencion  = float(np.mean(retenciones_finales))
    std_retencion    = float(np.std(retenciones_finales))

    print(f"✅ Retención media: {media_retencion:.1%} ± {std_retencion:.1%}")

    return {
        "nombre":            nombre,
        "recompensa_media":  media_recompensa,
        "retencion_media":   media_retencion,
        "retencion_std":     std_retencion,
        "retencion_por_dia": retenciones_por_dia,
        "todas_retenciones": retenciones_finales
    }


# ── Estrategia 1: Random ──────────────────────────────────────────────────────
def accion_random(env, obs):
    """Elige tema y duración completamente al azar."""
    return env.action_space.sample()


# ── Estrategia 2: Round-Robin ─────────────────────────────────────────────────
turno_rr = [0]

def accion_round_robin(env, obs):
    """Repasa cada tema por turnos, siempre 60 minutos."""
    topic = turno_rr[0] % config["n_topics"]
    turno_rr[0] += 1
    return [topic, 1]


# ── Estrategia 3: Agente PPO ──────────────────────────────────────────────────
print("\nCargando agente PPO...")
_env_ppo = DummyVecEnv([make_env])
_env_ppo = VecNormalize.load("models/vec_normalize.pkl", _env_ppo)
_env_ppo.training    = False
_env_ppo.norm_reward = False
modelo_ppo = PPO.load("models/best/best_model", env=_env_ppo)
print("✅ Agente cargado\n")

def accion_ppo(env, obs):
    """El agente PPO entrenado toma la decisión."""
    # Adaptar el vector de estado al tamaño del modelo (7 temas)
    estado_adaptado = np.zeros(7 * 5, dtype=np.float32)
    n_usar = min(len(obs) // 5, 7)
    estado_adaptado[:n_usar * 5] = obs[:n_usar * 5]

    obs_norm = _env_ppo.normalize_obs(estado_adaptado.reshape(1, -1))
    accion, _ = modelo_ppo.predict(obs_norm, deterministic=True)
    return [int(accion[0][0]), int(accion[0][1])]


# ── Ejecutar la comparación ───────────────────────────────────────────────────
print("="*55)
print("  COMPARACIÓN DE ESTRATEGIAS")
print(f"  {N_EPISODIOS} episodios × 7 días = {N_EPISODIOS * 7} días simulados")
print("="*55 + "\n")

np.random.seed(SEED)

resultados = []
resultados.append(evaluar_estrategia("Random",        accion_random))
turno_rr[0] = 0
resultados.append(evaluar_estrategia("Round-Robin",   accion_round_robin))
resultados.append(evaluar_estrategia("PPO (nuestro)", accion_ppo))


# ── Mostrar tabla de resultados ───────────────────────────────────────────────
print("\n" + "="*55)
print("  RESULTADOS FINALES")
print("="*55)
print(f"  {'Estrategia':<20} {'Retención':<18} {'Recompensa':<15}")
print(f"  {'-'*52}")
for r in resultados:
    print(
        f"  {r['nombre']:<20} "
        f"{r['retencion_media']:>6.1%} ±{r['retencion_std']:.1%}   "
        f"{r['recompensa_media']:>+.3f}"
    )
print("="*55)

mejora = (
    (resultados[2]["retencion_media"] - resultados[0]["retencion_media"])
    / max(resultados[0]["retencion_media"], 0.001) * 100
)
print(f"\n  El agente PPO {'mejora' if mejora > 0 else 'varía'} un {mejora:.1f}%")
print(f"  la retención respecto a la estrategia aleatoria.\n")


# ── Generar gráficas ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colores = ["#E74C3C", "#F39C12", "#2E86C1"]

# Gráfica 1: Evolución de retención durante un episodio
ax1 = axes[0]
for r, color in zip(resultados, colores):
    dias = list(range(1, len(r["retencion_por_dia"]) + 1))
    ax1.plot(dias, r["retencion_por_dia"],
             label=r["nombre"], color=color,
             linewidth=2.5, marker="o", markersize=5)

ax1.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
ax1.set_xlabel("Día del episodio", fontsize=12)
ax1.set_ylabel("Retención media", fontsize=12)
ax1.set_title("Evolución de retención\n(un episodio de 7 días)",
              fontsize=13, fontweight="bold")
ax1.legend(fontsize=10)
ax1.set_ylim(0, 1.05)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.0%}")
)

# Gráfica 2: Distribución de retenciones finales (boxplot)
ax2 = axes[1]
datos_box = [r["todas_retenciones"] for r in resultados]
nombres   = [r["nombre"] for r in resultados]
bp = ax2.boxplot(datos_box, tick_labels=nombres,
                 patch_artist=True, notch=False)

for patch, color in zip(bp["boxes"], colores):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax2.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
ax2.set_ylabel("Retención final del episodio", fontsize=12)
ax2.set_title(f"Distribución de retención final\n({N_EPISODIOS} episodios)",
              fontsize=13, fontweight="bold")
ax2.set_ylim(0, 1.05)
ax2.grid(True, alpha=0.3, axis="y")
ax2.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.0%}")
)

plt.tight_layout()
plt.savefig("validacion_resultados.png", dpi=150, bbox_inches="tight")
plt.show()
print("  Gráfica guardada como 'validacion_resultados.png'")