"""
fase3_clima.py
==============
Ejecuta la Fase 3: el modelo con recursos más clima (estaciones de lluvia y
temperatura, con una temperatura óptima para las plantas).

Qué hace:
  1. Estaciones: simula 60 años con RK4 y comprueba que el ecosistema entra
     en un ciclo anual que se repite año tras año.
  2. Ola de calor: en el año 30 la temperatura sube +8 °C durante 12 meses.
     Compara contra el mundo normal, mide cuánto caen las poblaciones y cuánto
     tarda el ecosistema en recuperarse.
  3. Guarda las gráficas en la carpeta resultados/.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase3_clima.py
"""

import math
import os

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.integrate import solve_ivp

from modelo import ParametrosClima, derivadas_clima, f_temperatura, lluvia, temperatura
from solver import rk4

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
y0 = [50.0, 10.0, 2.0, 50.0, 20.0]   # estado inicial: P, H, C, W, N
H_PASO = 0.1
T_FINAL = 720.0                      # 60 años

CALOR_INICIO = 360.0     # mes en que empieza la ola de calor (año 30)
CALOR_DURACION = 12.0    # meses que dura
CALOR_EXTRA = 8.0        # °C que se suman a la temperatura normal
BANDA_RECUPERACION = 0.05   # "recuperado" = dentro del 5% del mundo normal

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

COLOR = {"P": "tab:green", "H": "tab:orange", "C": "tab:red",
         "W": "tab:blue", "N": "tab:brown", "T": "tab:red", "R": "tab:blue"}
POBLACIONES = [("P", "Plantas (P)"), ("H", "Herbívoros (H)"), ("C", "Depredadores (C)")]


def ola_de_calor(tt):
    """
    Grados extra que se suman a la temperatura en el mes tt.

    Vale CALOR_EXTRA durante CALOR_DURACION meses, con una subida y una bajada
    suaves (de unas pocas semanas) en vez de un salto brusco, como en una ola
    de calor real.
    """
    ascenso = math.tanh((tt - CALOR_INICIO) / 0.5)
    descenso = math.tanh((tt - CALOR_INICIO - CALOR_DURACION) / 0.5)
    return CALOR_EXTRA * 0.5 * (ascenso - descenso)


# ---------------------------------------------------------------------------
# Simulaciones
# ---------------------------------------------------------------------------
p_normal = ParametrosClima()
p_calor = ParametrosClima(delta_temperatura=ola_de_calor)

t, Y_normal = rk4(derivadas_clima, y0, 0.0, T_FINAL, H_PASO, args=(p_normal,))
_, Y_calor = rk4(derivadas_clima, y0, 0.0, T_FINAL, H_PASO, args=(p_calor,))

# ---------------------------------------------------------------------------
# 1. Estaciones: ¿el ecosistema repite el mismo ciclo cada año?
# ---------------------------------------------------------------------------
paso_anio = int(round(12 / H_PASO))
ultimo = Y_normal[-paso_anio - 1:]            # último año
anterior = Y_normal[-2 * paso_anio - 1:-paso_anio]   # año anterior
dif_anios = np.max(np.abs(ultimo[:-1] - anterior[:-1]) / np.maximum(anterior[:-1], 1e-9))
print("ESTACIONES")
print(f"  Diferencia relativa máxima entre los dos últimos años: {dif_anios:.2e}")

ciclo = Y_normal[t >= T_FINAL - 12]
print("  Rango durante el último año (mínimo - máximo):")
for i, nombre in enumerate(["Plantas", "Herbívoros", "Depredadores", "Agua", "Nutrientes"]):
    print(f"    {nombre:<14} {ciclo[:, i].min():7.2f} - {ciclo[:, i].max():7.2f}")

# Verificación con SciPy sobre el último año
ref = solve_ivp(lambda tt, yy: derivadas_clima(tt, yy, p_normal), (0, T_FINAL), y0,
                method="LSODA", rtol=1e-9, atol=1e-11, max_step=0.25, dense_output=True)
t_ult = t[t >= T_FINAL - 12]
err = np.max(np.abs(ref.sol(t_ult).T - ciclo))
print(f"  Diferencia máxima RK4 vs SciPy en el último año: {err:.2e}")

# Gráfica de las estaciones: 4 años ya estabilizados
ventana = (t >= 600) & (t <= 648)
tv = t[ventana]
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

T_curva = np.array([temperatura(x, p_normal) for x in tv])
R_curva = np.array([lluvia(x, p_normal) for x in tv])
ax1.plot(tv, T_curva, color=COLOR["T"], label="Temperatura (°C)")
ax1.set_ylabel("Temperatura (°C)", color=COLOR["T"])
ax1b = ax1.twinx()
ax1b.plot(tv, R_curva, color=COLOR["R"], label="Lluvia")
ax1b.set_ylabel("Lluvia (entrada de agua por mes)", color=COLOR["R"])
ax1.set_title("Fase 3: el clima estacional produce un ciclo anual en el ecosistema\n"
              "(4 años, ya estabilizado; la lluvia llega ~2 meses después del calor)")
ax1.grid(alpha=0.3)

Yv = Y_normal[ventana]
for i, (clave, nombre) in enumerate(POBLACIONES):
    ax2.plot(tv, Yv[:, i], color=COLOR[clave], label=nombre)
ax2.set_ylabel("Población")
ax2.legend(loc="center right")
ax2.grid(alpha=0.3)

for i, (clave, nombre) in enumerate([("W", "Agua (W)"), ("N", "Nutrientes (N)")], start=3):
    ax3.plot(tv, Yv[:, i], color=COLOR[clave], label=nombre)
ax3.set_ylabel("Cantidad de recurso")
ax3.set_xlabel("Tiempo (meses)")
ax3.legend(loc="center right")
ax3.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase3_estaciones.png"), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Ola de calor
# ---------------------------------------------------------------------------
fin_calor = CALOR_INICIO + CALOR_DURACION
T_normal = np.array([temperatura(x, p_normal) for x in t])
T_calor = np.array([temperatura(x, p_calor) for x in t])
fT_normal = np.array([f_temperatura(x, p_normal) for x in T_normal])
fT_calor = np.array([f_temperatura(x, p_calor) for x in T_calor])

print(f"\nOLA DE CALOR (+{CALOR_EXTRA:.0f} °C entre los meses {CALOR_INICIO:.0f} y {fin_calor:.0f})")
print(f"  Temperatura máxima: {T_normal.max():.1f} °C (normal)  ->  {T_calor.max():.1f} °C (con ola)")
print(f"  Efecto de la temperatura fT mínimo: {fT_normal.min():.2f} (normal)  ->  "
      f"{fT_calor.min():.3f} (con ola)")

despues = t >= CALOR_INICIO
nombres = ["Plantas", "Herbívoros", "Depredadores", "Agua", "Nutrientes"]
print("\n  variable        caída máxima respecto al mundo normal (mismo mes)")
for i, nombre in enumerate(nombres):
    caida = 100 * np.max(1 - Y_calor[despues, i] / Y_normal[despues, i])
    print(f"  {nombre:<14} {max(caida, 0.0):7.1f} %")

desviacion = np.abs(Y_calor[:, :3] - Y_normal[:, :3]) / Y_normal[:, :3]
fuera = np.where((desviacion > BANDA_RECUPERACION).any(axis=1) & (t >= fin_calor))[0]
t_recuperacion = (t[fuera[-1]] - fin_calor) if len(fuera) else 0.0
print(f"\n  Tiempo de recuperación: {t_recuperacion:.1f} meses después de que termina la ola de calor")

# Gráfica de la ola de calor
v = (t >= 336) & (t <= 516)
tv = t[v]
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

ax1.plot(tv, T_normal[v], color=COLOR["T"], linestyle=":", alpha=0.6, label="Temperatura normal")
ax1.plot(tv, T_calor[v], color=COLOR["T"], label="Con ola de calor")
ax1.axhline(p_normal.Topt, color="gray", linestyle="--", alpha=0.6)
ax1.text(tv[0] + 1, p_normal.Topt + 0.4, "temperatura óptima", fontsize=8, color="gray")
ax1.set_ylabel("Temperatura (°C)")
ax1.set_title("Fase 3: ola de calor y recuperación del ecosistema (RK4)\n"
              "punteado = mundo normal sin ola de calor")
ax1.legend(loc="upper right")
ax1.grid(alpha=0.3)

for i, (clave, nombre) in enumerate(POBLACIONES):
    ax2.plot(tv, Y_calor[v, i], color=COLOR[clave], label=nombre)
    ax2.plot(tv, Y_normal[v, i], color=COLOR[clave], linestyle=":", alpha=0.6)
ax2.set_ylabel("Población")
ax2.legend(loc="center right")
ax2.grid(alpha=0.3)

ax3.plot(tv, fT_normal[v], color="black", linestyle=":", alpha=0.6, label="Normal")
ax3.plot(tv, fT_calor[v], color="black", label="Con ola de calor")
ax3.set_ylabel("Efecto de la temperatura fT\n(1 = crecimiento máximo)")
ax3.set_xlabel("Tiempo (meses)")
ax3.set_ylim(0, 1.05)
ax3.legend(loc="lower right")
ax3.grid(alpha=0.3)

for ax in (ax1, ax2, ax3):
    ax.axvspan(CALOR_INICIO, fin_calor, color="gold", alpha=0.25)

fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase3_ola_calor.png"), dpi=150)
plt.close(fig)

print("\nGráficas guardadas en:", os.path.abspath(CARPETA))
