# ============================================================
# study_env.py
# Entorno personalizado de Gymnasium para el RL Study Optimizer
#
# ¿Qué hace este archivo?
# Define el "mundo" en el que vive nuestro agente de RL.
# El agente observa el estado cognitivo del estudiante y decide
# qué tema repasar hoy y durante cuánto tiempo.
# ============================================================

import gymnasium as gym        # Framework para crear entornos de RL
import numpy as np             # Para operaciones matemáticas vectoriales
from gymnasium import spaces   # Para definir el tipo de observaciones y acciones


class StudyEnv(gym.Env):
    """
    Entorno de RL que simula el proceso de estudio de un estudiante.

    El agente aprende a decidir:
        - QUÉ tema repasar (de N temas disponibles)
        - CUÁNTO tiempo dedicarle (30, 60 o 90 minutos)

    El objetivo es maximizar la retención media de todos los temas
    usando el mínimo tiempo posible.
    """

    # metadata es obligatorio en Gymnasium — indica los modos de visualización
    metadata = {"render_modes": ["human"]}

    def __init__(self, n_topics=5, max_daily_minutes=180, difficulties=None):
        """
        Constructor del entorno.

        Parámetros:
            n_topics (int): Número de temas que tiene el estudiante.
                            Empezamos con 5 para que sea fácil de depurar.
            max_daily_minutes (int): Máximo de minutos de estudio por día.
                                     Si se supera, el agente recibe penalización.
            difficulties (list): Dificultades definidas por el alumno (0.0 a 1.0).
                                  Si es None, se asigna 0.5 a todos los temas.
        """
        super().__init__()  # Llamada obligatoria al constructor padre de gym.Env

        self.n_topics = n_topics
        self.max_daily_minutes = max_daily_minutes

        # ── ESPACIO DE OBSERVACIÓN ──────────────────────────────────────────
        # ¿Qué "ve" el agente en cada momento?
        # Por cada tema, le damos 5 números (features):
        #
        #   [0] retención actual       → qué tanto recuerda el estudiante (0=olvidado, 1=perfecto)
        #   [1] días desde último repaso → normalizado dividiendo entre 30
        #   [2] estabilidad             → qué tan duradera es la memoria (normalizado entre 30)
        #   [3] dificultad              → qué tan difícil es el tema para este estudiante (0 a 1)
        #   [4] urgencia                → 1 - retención (cuánto de urgente es repasar)
        #
        # Total de números = n_topics × 5
        # Todos los valores están entre 0.0 y 1.0 (Box = espacio continuo)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(n_topics * 5,),   # Vector plano de floats
            dtype=np.float32
        )

        # ── ESPACIO DE ACCIONES ─────────────────────────────────────────────
        # ¿Qué puede hacer el agente?
        # Dos decisiones simultáneas:
        #
        #   [0] índice del tema a repasar  → número entre 0 y n_topics-1
        #   [1] duración                   → 0=30min, 1=60min, 2=90min
        #
        # MultiDiscrete permite múltiples acciones discretas en una sola
        self.action_space = spaces.MultiDiscrete([n_topics, 3])

        # ── DIFICULTADES FIJAS ──────────────────────────────────────────────
        # Guardamos las dificultades ANTES de llamar a _init_state()
        # porque _init_state() también se llama en cada reset() y necesitamos
        # que las dificultades del alumno persistan entre episodios.
        # Sin esto, cada reset() sobreescribiría las dificultades con 0.5.
        if difficulties is not None:
            self._difficulties_fixed = np.array(difficulties, dtype=np.float32)
        else:
            self._difficulties_fixed = None

        # Inicializar el estado interno del entorno
        self._init_state()

    # ────────────────────────────────────────────────────────────────────────
    def _init_state(self):
        """
        Inicializa (o reinicia) el estado interno del entorno.
        Se llama al principio y en cada reset().

        El estado interno son los datos 'reales' del estudiante,
        que el agente no ve directamente — solo ve la observación
        procesada que se le entrega en _get_obs().
        """

        # Dificultad de cada tema:
        # Si el alumno definió las dificultades manualmente → usarlas.
        # Si no → asignar 0.5 (dificultad media) a todos los temas.
        # hasattr() comprueba que _difficulties_fixed ya existe (por si
        # _init_state() se llama antes de que se defina el atributo).
        if hasattr(self, '_difficulties_fixed') and self._difficulties_fixed is not None:
            self.difficulty = self._difficulties_fixed.copy()
        else:
            self.difficulty = np.full(self.n_topics, 0.5, dtype=np.float32)

        # Estabilidad de memoria por tema (en días)
        # Parámetro S de la curva de Ebbinghaus: R(t) = e^(-t/S)
        # Empieza en 2.0 días para todos los temas (memoria reciente y frágil)
        self.stability = np.ones(self.n_topics, dtype=np.float32) * 2.0

        # Días transcurridos desde el último repaso de cada tema
        # Aleatorio entre 0 y 4 para simular que el estudiante lleva algo de tiempo
        self.days_since = np.random.randint(0, 5, self.n_topics).astype(np.float32)

        # Contador de minutos usados en el episodio actual
        self.time_used = 0.0

        # Contador de días (steps) dentro del episodio
        # Un episodio = 1 semana = 7 días
        self.day = 0

    # ────────────────────────────────────────────────────────────────────────
    def _get_retention(self):
        """
        Calcula la retención actual de cada tema usando la curva de Ebbinghaus.

        Fórmula: R(t) = e^(-t / S)

            R = retención (0 a 1)
            t = tiempo desde el último repaso (days_since)
            S = estabilidad de la memoria (stability)

        Cuanto mayor es S, más lentamente se olvida.
        Cuanto más tiempo pasa (t grande), más se olvida (R tiende a 0).
        """
        return np.exp(-self.days_since / self.stability)

    # ────────────────────────────────────────────────────────────────────────
    def _get_obs(self):
        """
        Construye el vector de observación que se entrega al agente.

        Transforma el estado interno en un vector plano de floats [0, 1]
        que el agente puede procesar con su red neuronal.

        Estructura del vector (5 features × n_topics):
            [ret_0, dias_0, estab_0, dif_0, urg_0,
             ret_1, dias_1, estab_1, dif_1, urg_1, ...]
        """
        retention = self._get_retention()           # R(t) para cada tema
        urgency   = 1.0 - retention                  # Urgencia = inverso de retención

        # np.stack agrupa los 5 arrays en una matriz (n_topics × 5)
        # .flatten() la convierte en un vector plano de (n_topics * 5,)
        obs = np.stack([
            retention,                               # [0] retención actual (0-1)
            self.days_since / 30.0,                  # [1] días normalizados (÷30 para [0,1])
            self.stability  / 30.0,                  # [2] estabilidad normalizada
            self.difficulty,                         # [3] dificultad (ya está en [0,1])
            urgency                                  # [4] urgencia (0=fresco, 1=olvidado)
        ], axis=1).flatten().astype(np.float32)

        return obs

    # ────────────────────────────────────────────────────────────────────────
    def step(self, action):
        """
        Avanza el entorno un día (un step = una decisión de estudio).

        Es el método más importante del entorno. El agente llama a step()
        con su acción y recibe:
            - la nueva observación
            - la recompensa obtenida
            - si el episodio ha terminado

        Parámetros:
            action: array [topic_idx, duration_idx]
                    - topic_idx: índice del tema a repasar (0 a n_topics-1)
                    - duration_idx: duración (0=30min, 1=60min, 2=90min)

        Retorna:
            obs (np.array): nueva observación tras la acción
            reward (float): recompensa obtenida (positiva = buena decisión)
            terminated (bool): True si el episodio terminó normalmente (7 días)
            truncated (bool): True si se cortó por tiempo excesivo
            info (dict): información extra para depuración
        """

        # ── 1. Extraer la acción ────────────────────────────────────────────
        topic_idx    = int(action[0])    # Qué tema repasa hoy
        duration_idx = int(action[1])    # Cuánto tiempo le dedica

        durations_map = [30, 60, 90]    # Minutos reales según el índice
        duration_min  = durations_map[duration_idx]

        # ── 2. Calcular retención ANTES del repaso ──────────────────────────
        # Necesitamos saber cuánto recordaba ANTES para calcular la ganancia
        retention_before = self._get_retention()

        # ── 3. Actualizar la estabilidad del tema repasado ──────────────────
        # Cuando repasas un tema, su memoria se vuelve más estable (S aumenta)
        #
        # La ganancia de estabilidad depende de:
        #   - cuánto tiempo dedicas: log1p(duration/30) → rendimientos decrecientes
        #     (60 min no es el doble de bueno que 30 min, la curva es logarítmica)
        #   - qué tan difícil es: temas difíciles ganan menos estabilidad por repaso
        #   - cuánto olvidaste: si ya lo tenías fresco, el repaso aporta menos
        #     (factor: 1 - retention_before = "margen de mejora")
        #
        gain = (
            np.log1p(duration_min / 30.0)           # Beneficio de la duración (logarítmico)
            * (1.0 - self.difficulty[topic_idx])     # Penaliza temas difíciles
        )
        self.stability[topic_idx] += gain * (1.0 - retention_before[topic_idx])

        # El tema repasado "resetea" su contador de días
        self.days_since[topic_idx] = 0.0

        # ── 4. Pasar un día para TODOS los temas ───────────────────────────
        # Cada step = 1 día. Todos los temas "envejecen" un día más
        self.days_since += 1.0
        self.time_used  += duration_min
        self.day        += 1

        # ── 5. Calcular retención DESPUÉS del repaso ────────────────────────
        retention_after = self._get_retention()

        # ── 6. Calcular la recompensa ───────────────────────────────────────
        #
        # Recompensa = ganancia de retención media ponderada por dificultad
        #
        # Ponderamos por dificultad porque mantener la retención de un tema
        # difícil es más valioso que mantener la de uno fácil.
        #
        delta_retention = (retention_after - retention_before) * self.difficulty
        reward = float(np.mean(delta_retention))

        # Penalización si se supera el tiempo máximo diario
        # Queremos que el agente aprenda a ser eficiente, no solo efectivo
        if self.time_used > self.max_daily_minutes:
            reward -= 0.5

        # ── 7. Condiciones de fin de episodio ───────────────────────────────
        terminated = self.day >= 7                              # 7 días completados = fin normal
        truncated  = self.time_used > self.max_daily_minutes * 7 * 2  # Abuso extremo de tiempo

        # ── 8. Info de depuración ───────────────────────────────────────────
        info = {
            "mean_retention":  float(np.mean(retention_after)),  # Retención media actual
            "topic_reviewed":  topic_idx,                         # Qué tema se repasó
            "duration_min":    duration_min,                      # Cuánto tiempo
            "day":             self.day,                          # Día actual del episodio
            "time_used":       self.time_used                     # Minutos acumulados
        }

        return self._get_obs(), reward, terminated, truncated, info

    # ────────────────────────────────────────────────────────────────────────
    def reset(self, seed=None, options=None):
        """
        Reinicia el entorno al estado inicial para empezar un nuevo episodio.

        Gymnasium llama a reset() al principio de cada episodio de entrenamiento.
        Debe devolver la observación inicial y un diccionario de info (puede estar vacío).

        Parámetros:
            seed: semilla aleatoria para reproducibilidad (estándar Gymnasium)
            options: opciones adicionales (no usamos ninguna)
        """
        super().reset(seed=seed)    # Importante: inicializa el RNG interno de Gymnasium
        self._init_state()          # Reinicia el estado del estudiante
        return self._get_obs(), {}  # Devuelve observación inicial e info vacía

    # ────────────────────────────────────────────────────────────────────────
    def render(self, mode="human"):
        """
        Muestra el estado actual del entorno en la terminal.
        Útil para depurar y entender qué está haciendo el agente.
        """
        retention = self._get_retention()
        print(f"\n{'='*55}")
        print(f"  DÍA {self.day} | Tiempo usado: {self.time_used:.0f} min")
        print(f"{'='*55}")
        print(f"  {'Tema':<8} {'Retención':>10} {'Días':>6} {'Estab.':>8} {'Dific.':>8}")
        print(f"  {'-'*50}")
        for i in range(self.n_topics):
            # Indicador visual de urgencia
            if retention[i] > 0.7:
                estado = "✅"
            elif retention[i] > 0.4:
                estado = "⚠️ "
            else:
                estado = "🔴"
            print(
                f"  {estado} T{i:<5} "
                f"{retention[i]:>9.1%} "
                f"{self.days_since[i]:>5.0f}d "
                f"{self.stability[i]:>7.2f} "
                f"{self.difficulty[i]:>7.1%}"
            )
        print(f"{'='*55}")
        print(f"  Retención media: {np.mean(retention):.1%}")
        print(f"{'='*55}\n")