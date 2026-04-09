# Memoria Técnica: RL Study Optimizer

## 1. Explicación Técnica de la Arquitectura

### 1.1 Visión General
El proyecto **RL Study Optimizer** es una aplicación full-stack diseñada para optimizar las sesiones de estudio utilizando Inteligencia Artificial, específicamente Aprendizaje por Refuerzo (Reinforcement Learning - RL). El sistema decide qué asignatura estudiar y por cuánto tiempo (30, 60 o 90 minutos) para maximizar la retención de la memoria basándose en la **Curva del Olvido de Ebbinghaus**.

### 1.2 Componentes Principales
La arquitectura se divide en tres bloques fundamentales:

1. **Agente de Inteligencia Artificial (Backend/RL)**
   - **Modelo:** Proximal Policy Optimization (PPO) de la librería `stable-baselines3`.
   - **Entorno (Environment):** Implementado con `gymnasium`. Se define como `StudyEnv`, simulando un estudiante. El espacio de observación (estado) incluye 5 características por asignatura: *retención, días sin repasar, estabilidad de memoria, dificultad y urgencia*.
   - **Recompensa (Reward):** El agente es recompensado en función del aumento de la retención media ponderada por la dificultad de la asignatura. Se aplican penalizaciones si se supera el límite de tiempo diario (180 minutos).
   - **Observación Continua y Acción Discreta:** La red neuronal observa estados flotantes y toma una decisión `MultiDiscrete` (asignatura y bloque de tiempo).

2. **API REST (Backend)**
   - **Framework:** FastAPI, permitiendo validación iterativa robusta y documentación automática.
   - **Base de Datos:** SQLite gestionada a través de SQLAlchemy (ORM) con estructura de modelos definida (Usuario, Asignatura, Sesion).
   - **Integración RL-API:** El endpoint de recomendación utiliza un enfoque híbrido. Carga el modelo PPO en modo inferencia, normaliza el estado alojado en la base de datos a través de `VecNormalize` y obtiene la sugerencia. Para evitar inanición de asignaturas que el modelo pudiera ignorar en el largo plazo, el sistema combina la predicción del agente (como un plus en el puntaje general) con una puntuación heurística de urgencia que penaliza exponencialmente el paso de los días.

3. **Frontend UI**
   - **Tecnologías:** React + Vite, y estilizado con Tailwind CSS. Permite también mostrar gráficas con Recharts.
   - **Comunicación:** Axios para comunicarse con la API de FastAPI e impactar los cambios temporalmente en la pantalla del usuario.

### 1.3 Flujo de Datos
1. El usuario solicita una recomendación desde el Dashboard.
2. FastAPI recaba de la Base de Datos el estado actual (estado de retención, asignaturas, memoria) y lo unifica en un vector dimensional.
3. Se normaliza el vector y se consulta el modelo PPO preentrenado.
4. El agente devuelve una sugerencia a FastAPI, que la matiza algorítmicamente y la envía al frontend.
5. El usuario acepta la sugerencia, completa el tiempo de estudio programado y califica su nivel interior.
6. La API inserta la nueva sesión, recalcula el factor de Ebbinghaus (su ganancia de estabilidad) y los parámetros globales cambian en consecuencia.
7. Al simular o suceder un cambio horario "nuevo día", los contadores de tiempo se extienden y la retención decae según las leyes matemáticas implementadas.

---

## 2. Retos Encontrados

Durante el desarrollo del sistema se presentaron varios ecosistemas y problemas matemáticos, entre ellos:

1. **Diseño de la Función de Recompensa (Reward-Shaping):**
   * *Reto:* Al principio, si el agente solo recibía puntos por "elevar" la retención, prefería obsesivamente las asignaturas más fáciles (porque mejoran más rápido) o recomendaba siempre el máximo de minutos posible todos los días.
   * *Solución:* Se decidió ponderar el \`delta_retention\` multiplicándolo por la dificultad del tema (haciendo que salvar un tema difícil de caer otorgase mayor peso en la época) y se codificó una penalización grave (-0.5 pts) en el Reward si se superaba el tiempo de vida (180 min diarios).

2. **Sincronización Matemática entre Entrenamiento e Inferencia:**
   * *Reto:* Las redes neuronales analizan los ratios de variación en el vector. Al desplegar el PPO al backend/FastAPI, el entorno infería con los datos crudos, haciendo que el output del PPO se corrompiera porque en el entorno de aprendizaje usó `VecNormalize`.
   * *Solución:* Fue necesario asegurar que el `VecNormalize.load()` se cargase en modo inferencia (`training=False` y `norm_reward=False`) tanto en los entrenamientos en local como en la API para forzar que ambos mapas de acción estuvieran escalados correctamente.

3. **Inanición de Asignaturas (Starvation):**
   * *Reto:* Ocasionalmente, el RL encontraba una "zona de confort" donde ignoraba una materia, lo que dejaba el tema olvidado durante decenas de ciclos virtuales ("Cold Start Problem").
   * *Solución:* Se creó una lógica híbrida en la rutina `seleccionar_asignatura()` de la API. Esta rutina calcula "Scores" de urgencia y multiplica un factor exponencial por los días transcurridos. La respuesta del Agente PPO solo sube o actúa como "Bono" en ese score. Garantiza que las lecciones no queden sepultadas.

4. **Variables Reseteadas por 'Gymnasium':**
   * *Reto:* En cada etapa de `reset()`, Gymnasium creaba todo de cero y el entorno sobreescribía las dificultades de las asignaturas a "0.5".
   * *Solución:* En un ciclo override manual de `_init_state()`, se protegió la persistencia mediante la flag `_difficulties_fixed`.

---

## 3. Manual de Uso

Este manual asume que ya existe un modelo PPO entrenado ubicado en `models/best/best_model`.

### 3.1 Despliegue y Arranque

**Paso 1: (Opcional) Reentrenar el Agente**
En caso de modificar el archivo `config_asignaturas.json` incrementando el número de materias con los metadatos iniciales, repite el adiestramiento abriendo tu terminal y ejecutando:
```bash
python src/agent/train.py
```
*(Tiempo estimado: ~10 minutos en CPU convencional)*

**Paso 2: Iniciar el servidor Backend (FastAPI)**
Con el modelo y la BD lista, instanciando desde la raíz del equipo lanza el entorno WSGI:
```bash
uvicorn src.api.main:app --reload --port 8000
```
> [!TIP]
> Se abrirá el motor base. Para leer la testificación completa y el dashboard Swagger para pruebas manuales ve a `http://localhost:8000/docs`.

**Paso 3: Servir el Frontend (React)**
Una vez montada la API, inicia el marco de trabajo VITE:
```bash
cd frontend
npm install   # Instala dependencias la primera vez
npm run dev
```

### 3.2 Instrucciones para el Estudiante (UI)

1. **Dashboard y Diagnóstico Inicial:** 
   El Frontend cargará un "Usuario Default" con el vector asignado. Verás un panel con las esferas circulares que demuestran qué porcentaje de retención actual posees.

2. **Botón 'Solicitar Recomendación':**
   Presiónalo para que el Pipeline de algoritmos calcule tu Ebbinghaus personal + sugerencia IA. Te arrojará un dictamen. (Ej. "Física - 90 minutos").

3. **Registrar Repaso Terminados (Completar Sesión):**
   Posterior a que el tiempo de estudio finalice tu revisión empírica, deberás calificar la dificultad que presenciaste en la sesión cursada (escala general). 

4. **Simulación Temporal (Avanzar Día):**
   Para vislumbrar las implicaciones o jugar con la interfaz de manera hiperactiva, utiliza el botón **"Avanzar Día"**. Esto fuerza una alteración global, degrada iteradamente la retención y comprueba cómo el Optimizador ajusta su próxima oferta por la urgencia.
