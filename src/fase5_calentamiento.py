"""
fase5_calentamiento.py
======================
Experimento D: calentamiento sostenido.

Se sube la temperatura media anual T0 (de 25 °C, que es la temperatura óptima
de las plantas, hasta 37 °C) y se mira cómo queda el ecosistema después de
60 años. Pregunta: ¿hasta qué temperatura media aguanta cada especie?

Igual que en fase5_experimentos.py, una especie que baja de la población
mínima viable (UMBRAL_EXTINCION) se considera extinta para siempre.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase5_calentamiento.py
(hace 25 simulaciones y puede tardar de 10 a 30 segundos)
"""

import os

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np

from experimentos import simular_con_extincion
from modelo import ParametrosClima, derivadas_clima

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
y0 = [50.0, 10.0, 2.0, 50.0, 20.0]   # estado inicial: P, H, C, W, N
H_PASO = 0.1
T_FINAL = 720.0                      # 60 años
UMBRAL_EXTINCION = 0.05              # población mínima viable
T0_VALORES = np.arange(25.0, 37.01, 0.5)

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

ESPECIES = [("P", "Plantas (P)", "tab:green", 0),
            ("H", "Herbívoros (H)", "tab:orange", 1),
            ("C", "Depredadores (C)", "tab:red", 2)]

# ---------------------------------------------------------------------------
# Simulaciones
# ---------------------------------------------------------------------------
print("EXPERIMENTO D: calentamiento sostenido (temperatura media T0 más alta)")
print(f"  Calculando {len(T0_VALORES)} simulaciones...")

medias = []          # población media de los últimos 2 años, por cada T0
mes_extincion = []   # {especie: mes en que se extinguió}, por cada T0
for T0 in T0_VALORES:
    p = ParametrosClima(T0=float(T0))
    t, Y, ext = simular_con_extincion(derivadas_clima, y0, T_FINAL, H_PASO,
                                      args=(p,), umbral=UMBRAL_EXTINCION)
    medias.append(Y[t >= T_FINAL - 24].mean(axis=0))
    mes_extincion.append(ext)
medias = np.array(medias)

# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
print(f"\n  {'T0 (°C)':>8} {'plantas':>9} {'herbívoros':>11} {'depredadores':>13}")
for T0, m in zip(T0_VALORES, medias):
    if T0 == 25.0 or abs(T0 - round(T0)) < 1e-9 and int(round(T0)) % 2 == 1:
        print(f"  {T0:8.1f} {m[0]:9.2f} {m[1]:11.2f} {m[2]:13.2f}")

print()
for clave, nombre, _, i in reversed(ESPECIES):
    criticos = [T0 for T0, ext in zip(T0_VALORES, mes_extincion) if i in ext]
    if criticos:
        print(f"  {nombre.split(' (')[0]:<13}: se extinguen a partir de T0 = {criticos[0]:.1f} °C "
              f"(+{criticos[0] - 25.0:.1f} °C sobre la temperatura óptima)")
    else:
        print(f"  {nombre.split(' (')[0]:<13}: sobreviven en todo el rango estudiado")

# ---------------------------------------------------------------------------
# Gráfica
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
for clave, nombre, color, i in ESPECIES:
    ax.plot(T0_VALORES, medias[:, i], "o-", color=color, markersize=4, label=nombre)
    criticos = [T0 for T0, ext in zip(T0_VALORES, mes_extincion) if i in ext]
    if criticos:
        ax.axvline(criticos[0], color=color, linestyle="--", alpha=0.5)
        ax.text(criticos[0] + 0.1, 32 - 4 * i, f"se extinguen {nombre.split(' (')[0].lower()}",
                color=color, fontsize=9, va="center")
ax.axvline(25.0, color="gray", linestyle=":", alpha=0.7)
ax.text(25.15, 2, "temperatura óptima\nde las plantas", fontsize=8, color="gray", va="bottom")
ax.set_xlabel("Temperatura media anual T0 (°C)")
ax.set_ylabel("Población media (últimos 2 años)")
ax.set_title("Experimento D: ¿cuánto calentamiento sostenido aguanta el ecosistema?\n"
             f"(extinción = población bajo {UMBRAL_EXTINCION})")
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase5_calentamiento.png"), dpi=150)
plt.close(fig)

print("\nGráfica guardada en:", os.path.abspath(CARPETA))
