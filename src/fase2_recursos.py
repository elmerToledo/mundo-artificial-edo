"""
fase2_recursos.py
=================
Ejecuta la Fase 2: modelo con recursos (plantas, herbívoros, depredadores,
agua y nutrientes).

Qué hace:
  1. Mundo normal: simula con RK4 y comprueba que el sistema llega al
     equilibrio calculado (y que coincide con SciPy).
  2. Sequía: la lluvia baja al 20% entre el mes 150 y el 200, y luego vuelve
     a la normalidad. Mide cuánto caen las poblaciones y cuánto tarda el
     ecosistema en recuperarse.
  3. Guarda las gráficas en la carpeta resultados/.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase2_recursos.py
"""

import os

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from modelo import ParametrosCompleto, derivadas_completo, equilibrio_completo
from solver import rk4

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
y0 = [50.0, 10.0, 2.0, 50.0, 20.0]   # estado inicial: P, H, C, W, N
H_PASO = 0.1

SEQUIA_INICIO = 150.0   # mes en que empieza la sequía
SEQUIA_FIN = 200.0      # mes en que vuelve la lluvia
SEQUIA_FACTOR = 0.2     # la lluvia baja al 20% de lo normal
BANDA_RECUPERACION = 0.05   # "recuperado" = dentro del 5% del equilibrio

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

COLOR = {"P": "tab:green", "H": "tab:orange", "C": "tab:red",
         "W": "tab:blue", "N": "tab:brown"}


def graficar(t, Y, eq, titulo, archivo, sequia=None):
    """Dos paneles: poblaciones arriba y recursos abajo."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for i, (clave, nombre) in enumerate([("P", "Plantas (P)"), ("H", "Herbívoros (H)"),
                                         ("C", "Depredadores (C)")]):
        ax1.plot(t, Y[:, i], color=COLOR[clave], label=nombre)
        ax1.axhline(eq[i], color=COLOR[clave], linestyle=":", alpha=0.5)
    ax1.set_ylabel("Población")
    ax1.set_title(titulo + "\n(líneas punteadas = equilibrio)")
    ax1.grid(alpha=0.3)

    for i, (clave, nombre) in enumerate([("W", "Agua (W)"), ("N", "Nutrientes (N)")], start=3):
        ax2.plot(t, Y[:, i], color=COLOR[clave], label=nombre)
        ax2.axhline(eq[i], color=COLOR[clave], linestyle=":", alpha=0.5)
    ax2.set_ylabel("Cantidad de recurso")
    ax2.set_xlabel("Tiempo (meses)")
    ax2.grid(alpha=0.3)

    if sequia is not None:
        for ax in (ax1, ax2):
            ax.axvspan(sequia[0], sequia[1], color="gold", alpha=0.25)
        ax1.text((sequia[0] + sequia[1]) / 2, ax1.get_ylim()[1] * 0.95, "sequía",
                 ha="center", va="top")

    ax1.legend(loc="center right")
    ax2.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Mundo normal
# ---------------------------------------------------------------------------
p = ParametrosCompleto()
eq = equilibrio_completo(p)
print("Equilibrio (P*, H*, C*, W*, N*):", eq.round(3))

t, Y = rk4(derivadas_completo, y0, 0.0, 150.0, H_PASO, args=(p,))
print("Estado final RK4 (mundo normal):", Y[-1].round(3))

# Verificación con SciPy
ref = solve_ivp(lambda tt, yy: derivadas_completo(tt, yy, p), (0, 150), y0,
                method="LSODA", rtol=1e-9, atol=1e-11)
print("Estado final SciPy             :", ref.y[:, -1].round(3))

graficar(t, Y, eq, "Fase 2: mundo normal con agua y nutrientes (RK4)", "fase2_mundo_normal.png")

# ---------------------------------------------------------------------------
# 2. Sequía
# ---------------------------------------------------------------------------
p_sequia = ParametrosCompleto(
    factor_lluvia=lambda tt: SEQUIA_FACTOR if SEQUIA_INICIO <= tt < SEQUIA_FIN else 1.0
)
t, Y = rk4(derivadas_completo, y0, 0.0, 450.0, H_PASO, args=(p_sequia,))

# Mínimos que alcanzan las variables desde que empieza la sequía
desde = t >= SEQUIA_INICIO
minimos = Y[desde].min(axis=0)
nombres = ["Plantas", "Herbívoros", "Depredadores", "Agua", "Nutrientes"]

print("\nEfecto de la sequía (lluvia al %d%% entre los meses %d y %d)" %
      (SEQUIA_FACTOR * 100, SEQUIA_INICIO, SEQUIA_FIN))
print("  variable        equilibrio   mínimo    caída")
for i, nombre in enumerate(nombres):
    caida = 100 * (1 - minimos[i] / eq[i])
    print(f"  {nombre:<14} {eq[i]:10.2f} {minimos[i]:9.2f} {caida:7.1f} %")

# Tiempo de recuperación: meses después de la sequía hasta que P, H y C
# vuelven y se quedan dentro del 5% de su equilibrio
dentro = np.all(np.abs(Y[:, :3] - eq[:3]) <= BANDA_RECUPERACION * eq[:3], axis=1)
fuera = np.where(~dentro & (t >= SEQUIA_FIN))[0]
t_recuperacion = (t[fuera[-1]] - SEQUIA_FIN) if len(fuera) else 0.0
print(f"\nTiempo de recuperación: {t_recuperacion:.1f} meses después de que vuelve la lluvia")

graficar(t, Y, eq, "Fase 2: sequía y recuperación (RK4)", "fase2_sequia.png",
         sequia=(SEQUIA_INICIO, SEQUIA_FIN))

print("\nGráficas guardadas en:", os.path.abspath(CARPETA))
