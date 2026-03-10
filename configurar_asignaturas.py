# ============================================================
# configurar_asignaturas.py
#
# Script de configuración inicial del estudiante.
# El alumno introduce sus asignaturas y valora la dificultad
# de cada una del 1 al 5. El sistema lo convierte al formato
# interno [0.0 - 1.0] que usa el entorno.
# Ejecutar con: python configurar_asignaturas.py
# ============================================================

import json
import os

# Conversión del nivel de dificultad (1-5) al valor interno (0.0-1.0)
# Usamos valores que no lleguen a los extremos absolutos:
#   1 = Muy fácil  → 0.1  (casi no cuesta retener)
#   2 = Fácil      → 0.3
#   3 = Normal     → 0.5
#   4 = Difícil    → 0.7
#   5 = Muy difícil→ 0.9  (cuesta mucho retener)
NIVEL_A_DIFICULTAD = {
    1: 0.1,
    2: 0.3,
    3: 0.5,
    4: 0.7,
    5: 0.9
}

def pedir_asignaturas():
    """
    Pide al alumno que introduzca sus asignaturas y su nivel de dificultad.
    Devuelve una lista de diccionarios con nombre y dificultad de cada una.
    """
    print("\n" + "="*55)
    print("  CONFIGURACIÓN DE ASIGNATURAS")
    print("  RL Study Optimizer")
    print("="*55)
    print("\nVamos a configurar tus asignaturas.")
    print("Introduce el nombre de cada asignatura y su nivel")
    print("de dificultad del 1 al 5:")
    print()
    print("  1 = Muy fácil   (ej: asignatura que dominas)")
    print("  2 = Fácil")
    print("  3 = Normal      (ej: requiere estudio regular)")
    print("  4 = Difícil")
    print("  5 = Muy difícil (ej: mucho contenido complejo)")
    print()

    # Pedir número de asignaturas
    while True:
        try:
            n = int(input("¿Cuántas asignaturas tienes? (2-10): "))
            if 2 <= n <= 10:
                break
            print("  ⚠️  Por favor introduce un número entre 2 y 10.")
        except ValueError:
            print("  ⚠️  Escribe solo un número.")

    asignaturas = []

    print()
    for i in range(n):
        print(f"── Asignatura {i+1} de {n} ──────────────────────────")

        # Pedir nombre
        while True:
            nombre = input(f"  Nombre: ").strip()
            if nombre:
                break
            print("  ⚠️  El nombre no puede estar vacío.")

        # Pedir nivel de dificultad
        while True:
            try:
                nivel = int(input(f"  Dificultad (1-5): "))
                if 1 <= nivel <= 5:
                    break
                print("  ⚠️  Introduce un número entre 1 y 5.")
            except ValueError:
                print("  ⚠️  Escribe solo un número.")

        # Convertir nivel a valor interno
        dificultad_interna = NIVEL_A_DIFICULTAD[nivel]

        asignaturas.append({
            "nombre":              nombre,
            "nivel_dificultad":    nivel,           # Lo que introdujo el alumno (1-5)
            "dificultad_interna":  dificultad_interna,  # Lo que usa el entorno (0.0-1.0)
            "minutos_diarios_max": 180              # Tiempo máximo de estudio al día
        })

        # Confirmar lo que se ha guardado
        etiquetas = {1: "Muy fácil", 2: "Fácil", 3: "Normal",
                     4: "Difícil", 5: "Muy difícil"}
        print(f"  ✅ '{nombre}' guardada — {etiquetas[nivel]} ({dificultad_interna})\n")

    return asignaturas


def guardar_configuracion(asignaturas):
    """
    Guarda la configuración en un archivo JSON para que el entorno
    pueda cargarla automáticamente en el entrenamiento y la inferencia.
    """
    config = {
        "n_topics":    len(asignaturas),
        "asignaturas": asignaturas,

        # Listas planas que usa directamente el entorno
        "nombres":      [a["nombre"]             for a in asignaturas],
        "dificultades": [a["dificultad_interna"] for a in asignaturas]
    }

    # Guardar en la raíz del proyecto
    ruta = "config_asignaturas.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("="*55)
    print(f"  ✅ Configuración guardada en '{ruta}'")
    print("="*55)
    return config


def mostrar_resumen(config):
    """
    Muestra un resumen visual de la configuración guardada.
    """
    print("\n  RESUMEN DE TUS ASIGNATURAS:")
    print()

    barras = {0.1: "█░░░░", 0.3: "██░░░", 0.5: "███░░",
              0.7: "████░", 0.9: "█████"}

    for a in config["asignaturas"]:
        barra = barras[a["dificultad_interna"]]
        print(f"  {a['nombre']:<25} {barra}  "
              f"Nivel {a['nivel_dificultad']}/5")

    print()
    print(f"  Total de asignaturas: {config['n_topics']}")
    print()


def cargar_configuracion():
    """
    Carga la configuración guardada desde el JSON.
    Útil para usarla desde otros scripts (train.py, inference.py, etc.)
    """
    ruta = "config_asignaturas.json"
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            "No se encontró 'config_asignaturas.json'.\n"
            "Ejecuta primero: python configurar_asignaturas.py"
        )
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Ejecutar la configuración ────────────────────────────────────────────────
if __name__ == "__main__":
    asignaturas = pedir_asignaturas()
    config      = guardar_configuracion(asignaturas)
    mostrar_resumen(config)

    print("  Ahora puedes entrenar el agente con:")
    print("  python src/agent/train.py")
    print()