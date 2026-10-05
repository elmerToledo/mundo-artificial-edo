"""
fase1_minimo.py
===============
Ejecuta la Fase 1: modelo mínimo (plantas, herbívoros, depredadores).

Qué hace:
  1. Resuelve el sistema con RK4 y muestra las poblaciones en el tiempo.
  2. Compara Euler y RK4 con una solución de referencia de SciPy (solve_ivp)
     para varios tamaños de paso h, y mide el error.
  3. Guarda las gráficas en la carpeta resultados/.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase1_minimo.py
"""

import os
import time

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from modelo import Parametros, derivadas, equilibrio_coexistencia
from solver import euler, rk4

# ---------------------------------------------------------------------------
# Configuración del experimento
# ---------------------------------------------------------------------------
p = Parametros()
y0 = [50.0, 10.0, 2.0]   # estado inicial: P, H, C
T_FINAL = 200.0          # meses simulados
H_PASO = 0.1             # paso para la simulación principal

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

NOMBRES = ["Plantas (P)", "Herbívoros (H)", "Depredadores (C)"]
COLORES = ["tab:green", "tab:orange", "tab:red"]

# ---------------------------------------------------------------------------
# 1. Simulación principal con RK4
# ---------------------------------------------------------------------------
t, Y = rk4(derivadas, y0, 0.0, T_FINAL, H_PASO, args=(p,))
P_eq, H_eq, C_eq = equilibrio_coexistencia(p)

print("Equilibrio teórico (P*, H*, C*):", round(P_eq, 3), round(H_eq, 3), round(C_eq, 3))
print("Estado final con RK4           :", Y[-1].round(3))

fig, ejes = plt.subplots(1, 2, figsize=(13, 4.5))

for i in range(3):
    ejes[0].plot(t, Y[:, i], color=COLORES[i], label=NOMBRES[i])
    ejes[0].axhline([P_eq, H_eq, C_eq][i], color=COLORES[i], linestyle=":", alpha=0.5)
ejes[0].set_xlabel("Tiempo (meses)")
ejes[0].set_ylabel("Población")
ejes[0].set_title("Evolución del ecosistema (RK4)\nlíneas punteadas = equilibrio teórico")
ejes[0].legend()
ejes[0].grid(alpha=0.3)

ejes[1].plot(Y[:, 1], Y[:, 2], color="tab:purple")
ejes[1].plot(Y[0, 1], Y[0, 2], "o", color="black", label="inicio")
ejes[1].plot(H_eq, C_eq, "*", color="gold", markersize=14, markeredgecolor="black", label="equilibrio")
ejes[1].set_xlabel("Herbívoros (H)")
ejes[1].set_ylabel("Depredadores (C)")
ejes[1].set_title("Plano de fase H-C: la trayectoria espira hacia el equilibrio")
ejes[1].legend()
ejes[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase1_evolucion.png"), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Comparación Euler vs RK4 contra una referencia de SciPy
# ---------------------------------------------------------------------------
T_COMP = 60.0  # ventana corta, donde hay más dinámica y los errores se notan
ref = solve_ivp(derivadas, (0, T_COMP), y0, args=(p,), method="RK45",
                rtol=1e-10, atol=1e-12, dense_output=True)

pasos = [5.0, 2.0, 1.0, 0.5, 0.1, 0.05]
err_euler, err_rk4, tiempo_euler, tiempo_rk4 = [], [], [], []

print("\n  h     error Euler     error RK4    tiempo Euler   tiempo RK4")
for h in pasos:
    t0 = time.perf_counter()
    te, Ye = euler(derivadas, y0, 0.0, T_COMP, h, args=(p,))
    dt_e = time.perf_counter() - t0

    t0 = time.perf_counter()
    tr, Yr = rk4(derivadas, y0, 0.0, T_COMP, h, args=(p,))
    dt_r = time.perf_counter() - t0

    exacta_e = ref.sol(te).T
    exacta_r = ref.sol(tr).T
    e_e = np.max(np.abs(Ye - exacta_e))   # error máximo en todo el intervalo
    e_r = np.max(np.abs(Yr - exacta_r))

    err_euler.append(e_e)
    err_rk4.append(e_r)
    tiempo_euler.append(dt_e)
    tiempo_rk4.append(dt_r)
    print(f"{h:5.2f}   {e_e:12.3e}   {e_r:12.3e}   {dt_e*1000:8.2f} ms   {dt_r*1000:8.2f} ms")

fig, ejes = plt.subplots(1, 2, figsize=(13, 4.5))

ejes[0].loglog(pasos, err_euler, "o-", color="tab:blue", label="Euler")
ejes[0].loglog(pasos, err_rk4, "s-", color="tab:red", label="RK4")
ejes[0].set_xlabel("Tamaño de paso h")
ejes[0].set_ylabel("Error máximo vs referencia")
ejes[0].set_title("Error según el paso (escala log-log)")
ejes[0].legend()
ejes[0].grid(alpha=0.3, which="both")

h_vis = 2.0
te, Ye = euler(derivadas, y0, 0.0, T_COMP, h_vis, args=(p,))
tr, Yr = rk4(derivadas, y0, 0.0, T_COMP, h_vis, args=(p,))
tt = np.linspace(0, T_COMP, 500)
ejes[1].plot(tt, ref.sol(tt)[1], "k-", linewidth=2, label="Referencia (SciPy)")
ejes[1].plot(te, Ye[:, 1], "o--", color="tab:blue", markersize=3, label=f"Euler h={h_vis}")
ejes[1].plot(tr, Yr[:, 1], "s--", color="tab:red", markersize=3, label=f"RK4 h={h_vis}")
ejes[1].set_xlabel("Tiempo (meses)")
ejes[1].set_ylabel("Herbívoros (H)")
ejes[1].set_title(f"Herbívoros con paso grande (h={h_vis})")
ejes[1].legend()
ejes[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase1_euler_vs_rk4.png"), dpi=150)
plt.close(fig)

print("\nGráficas guardadas en:", os.path.abspath(CARPETA))
