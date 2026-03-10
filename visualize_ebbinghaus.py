# ============================================================
# visualize_ebbinghaus.py
# Visualiza la curva de Ebbinghaus para entender qué aprende el agente
# Ejecutar con: python visualize_ebbinghaus.py
# ============================================================

import numpy as np
import matplotlib.pyplot as plt

# Simular el paso del tiempo (0 a 30 días)
dias = np.linspace(0, 30, 300)

# Diferentes valores de estabilidad S
# S bajo = memoria frágil (pocos repasos)
# S alto = memoria consolidada (muchos repasos)
estabilidades = {
    "S=2  (sin repasos)":    2,
    "S=5  (1 repaso)":       5,
    "S=10 (2 repasos)":     10,
    "S=20 (3 repasos)":     20,
}

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ── Gráfica 1: Curvas de olvido ──────────────────────────────────────────────
ax1 = axes[0]
colores = ["#E74C3C", "#F39C12", "#2ECC71", "#2E86C1"]

for (label, S), color in zip(estabilidades.items(), colores):
    retencion = np.exp(-dias / S)
    ax1.plot(dias, retencion, label=label, color=color, linewidth=2.5)

ax1.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="Umbral 50%")
ax1.fill_between(dias, 0, 0.4, alpha=0.05, color="red", label="Zona crítica (<40%)")
ax1.set_xlabel("Días desde el último repaso", fontsize=12)
ax1.set_ylabel("Retención R(t)", fontsize=12)
ax1.set_title("Curva del Olvido de Ebbinghaus\nR(t) = e^(-t/S)", fontsize=13, fontweight="bold")
ax1.legend(fontsize=10)
ax1.set_ylim(0, 1.05)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

# ── Gráfica 2: Simulación de un episodio del entorno ────────────────────────
ax2 = axes[1]

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.environment.study_env import StudyEnv

env = StudyEnv(n_topics=5, max_daily_minutes=180)
obs, _ = env.reset()

retenciones_por_dia = []
dias_episodio = []

retenciones_por_dia.append(env._get_retention().copy())
dias_episodio.append(0)

for day in range(7):
    # Acción inteligente manual: repasar siempre el tema más olvidado
    retention = env._get_retention()
    topic_mas_olvidado = int(np.argmin(retention))
    action = [topic_mas_olvidado, 1]  # 60 minutos

    obs, reward, terminated, truncated, info = env.step(action)
    retenciones_por_dia.append(env._get_retention().copy())
    dias_episodio.append(day + 1)

    if terminated or truncated:
        break

retenciones_array = np.array(retenciones_por_dia)
colores_temas = ["#E74C3C", "#F39C12", "#2ECC71", "#2E86C1", "#9B59B6"]

for i in range(env.n_topics):
    ax2.plot(
        dias_episodio,
        retenciones_array[:, i],
        label=f"Tema {i} (dif={env.difficulty[i]:.0%})",
        color=colores_temas[i],
        marker="o",
        linewidth=2,
        markersize=6
    )

ax2.set_xlabel("Día del episodio", fontsize=12)
ax2.set_ylabel("Retención por tema", fontsize=12)
ax2.set_title("Simulación: estrategia 'repasar el más olvidado'\n(episodio de 7 días)", fontsize=13, fontweight="bold")
ax2.legend(fontsize=9)
ax2.set_ylim(0, 1.05)
ax2.set_xticks(dias_episodio)
ax2.grid(True, alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

plt.tight_layout()
plt.savefig("ebbinghaus_visualization.png", dpi=150, bbox_inches="tight")
plt.show()
print("Gráfica guardada como ebbinghaus_visualization.png")