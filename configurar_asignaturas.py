# ============================================================
# configurar_asignaturas.py
# Script de configuración inicial del estudiante.
#
# ¿Qué hace este archivo?
# Pide al alumno sus asignaturas por terminal y las guarda
# DIRECTAMENTE en la base de datos SQLite, de forma que
# el frontend las muestra automáticamente.
#
# Ejecutar con: python configurar_asignaturas.py
# ============================================================

import json
import os
import sys
import requests

# ── Configuración ─────────────────────────────────────────────────────────────
API = "http://127.0.0.1:8000"

NIVEL_A_DIFICULTAD = {1: 0.1, 2: 0.3, 3: 0.5, 4: 0.7, 5: 0.9}
ETIQUETAS          = {1: "Muy fácil", 2: "Fácil", 3: "Normal",
                      4: "Difícil",   5: "Muy difícil"}


def cargar_configuracion():
    """
    Carga la configuración guardada desde el JSON.
    Usado por train.py para entrenar el agente.
    """
    ruta = "config_asignaturas.json"
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            "No se encontró 'config_asignaturas.json'.\n"
            "Ejecuta primero: python configurar_asignaturas.py"
        )
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def pedir_asignaturas():
    """Pide al alumno sus asignaturas y dificultades por terminal."""
    print("\n" + "="*55)
    print("  CONFIGURACIÓN DE ASIGNATURAS")
    print("  RL Study Optimizer")
    print("="*55)
    print("\nIntroduce el nombre y dificultad de cada asignatura.")
    print()
    print("  1 = Muy fácil   (ej: asignatura que dominas)")
    print("  2 = Fácil")
    print("  3 = Normal      (ej: requiere estudio regular)")
    print("  4 = Difícil")
    print("  5 = Muy difícil (ej: mucho contenido complejo)")
    print()

    # Pedir número de asignaturas (máximo 7 por el modelo entrenado)
    while True:
        try:
            n = int(input("¿Cuántas asignaturas tienes? (1-7): "))
            if 1 <= n <= 7:
                break
            print("  ⚠️  Por favor introduce un número entre 1 y 7.")
        except ValueError:
            print("  ⚠️  Escribe solo un número.")

    asignaturas = []
    print()

    for i in range(n):
        print(f"── Asignatura {i+1} de {n} ──────────────────────────")

        while True:
            nombre = input(f"  Nombre: ").strip()
            if nombre:
                break
            print("  ⚠️  El nombre no puede estar vacío.")

        while True:
            try:
                nivel = int(input(f"  Dificultad (1-5): "))
                if 1 <= nivel <= 5:
                    break
                print("  ⚠️  Introduce un número entre 1 y 5.")
            except ValueError:
                print("  ⚠️  Escribe solo un número.")

        dificultad = NIVEL_A_DIFICULTAD[nivel]
        asignaturas.append({
            "nombre":             nombre,
            "nivel_dificultad":   nivel,
            "dificultad_interna": dificultad
        })

        print(f"  ✅ '{nombre}' guardada — {ETIQUETAS[nivel]} ({dificultad})\n")

    return asignaturas


def guardar_json(asignaturas):
    """
    Guarda las asignaturas en config_asignaturas.json.
    Este archivo lo usa train.py para entrenar el agente.
    """
    config = {
        "n_topics":    len(asignaturas),
        "nombres":     [a["nombre"]             for a in asignaturas],
        "dificultades":[a["dificultad_interna"] for a in asignaturas]
    }
    with open("config_asignaturas.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"  ✅ config_asignaturas.json guardado (para entrenamiento)")


def guardar_en_bd(asignaturas):
    """
    Crea el usuario y las asignaturas directamente en la base de datos
    a través de la API. El frontend las mostrará automáticamente.
    """
    print("\n  Conectando con el backend...")

    # Verificar que el backend está corriendo
    try:
        requests.get(f"{API}/", timeout=3)
    except Exception:
        print("  ⚠️  El backend no está corriendo.")
        print("  Arranca primero: uvicorn src.api.main:app --reload --port 8000")
        return None

    # Borrar localStorage del navegador no es posible desde Python,
    # pero sí podemos crear un usuario nuevo y guardar su ID en un archivo
    # para que App.jsx lo lea automáticamente.

    # Crear usuario
    res = requests.post(f"{API}/api/usuarios", json={"nombre": "Estudiante"})
    if res.status_code != 200:
        print(f"  ❌ Error al crear usuario: {res.text}")
        return None

    usuario_id = res.json()["id"]
    print(f"  ✅ Usuario creado con ID: {usuario_id}")

    # Crear cada asignatura
    for a in asignaturas:
        res = requests.post(
            f"{API}/api/usuarios/{usuario_id}/asignaturas",
            json={"nombre": a["nombre"], "dificultad": a["dificultad_interna"]}
        )
        if res.status_code == 200:
            barra = int(a["dificultad_interna"] * 10) * "█" + \
                    (10 - int(a["dificultad_interna"] * 10)) * "░"
            print(f"  ✅ {a['nombre']:<20} {barra}  ({a['dificultad_interna']})")
        else:
            print(f"  ❌ Error al crear {a['nombre']}: {res.text}")

    # Guardar el usuario_id en un archivo para que el frontend lo lea
    with open("frontend/public/usuario_id.json", "w") as f:
        json.dump({"usuario_id": usuario_id}, f)

    print(f"\n  ✅ usuario_id.json guardado en frontend/public/")
    return usuario_id


def mostrar_resumen(asignaturas):
    """Muestra un resumen visual de las asignaturas configuradas."""
    print("\n" + "="*55)
    print("  RESUMEN DE TUS ASIGNATURAS")
    print("="*55)
    barras = {0.1: "█░░░░", 0.3: "██░░░", 0.5: "███░░",
              0.7: "████░", 0.9: "█████"}
    for a in asignaturas:
        barra = barras[a["dificultad_interna"]]
        print(f"  {a['nombre']:<25} {barra}  Nivel {a['nivel_dificultad']}/5")
    print("="*55)


# ── Ejecutar ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asignaturas = pedir_asignaturas()
    guardar_json(asignaturas)
    mostrar_resumen(asignaturas)

    usuario_id = guardar_en_bd(asignaturas)

    if usuario_id:
        print(f"\n  Todo listo. Abre http://localhost:5173")
        print(f"  (Si no carga, limpia localStorage en F12 → Application → Local Storage)\n")