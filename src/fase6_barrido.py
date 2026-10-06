"""
fase6_barrido.py
================
Fase 6: barrido de parámetros en 2D.

Se prueban muchas combinaciones de LLUVIA BASE (R0) y TEMPERATURA MEDIA (T0).
Para cada una se simulan 60 años y se mira cómo termina el ecosistema.
El resultado es un mapa que responde:

    ¿En qué climas puede sobrevivir el ecosistema, y en cuáles se rompe?

Clasificación de cada combinación (se mira el comportamiento de los últimos 5 años):

    Estable                 coexisten las 3 especies y varían poco durante el año
    Fluctuaciones fuertes   coexisten, pero con grandes vaivenes entre estaciones
    En riesgo               coexisten, pero alguna especie quedó por debajo del 25%
                            de su población en el mundo de referencia
    Sin depredadores        los depredadores se extinguen
    Solo plantas            se extinguen herbívoros y depredadores
    Colapso total           se extinguen las plantas

Importante: las "fluctuaciones" son los ciclos anuales causados por las estaciones.
En todo el rango estudiado los ciclos se repiten idénticos cada año; no aparecen
oscilaciones propias de varios años ni caos.

Una especie se considera extinta si baja de la población mínima viable
(UMBRAL_EXTINCION); ver experimentos.py.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase6_barrido.py
(hace unas 250 simulaciones y puede tardar de 30 segundos a 2 minutos)
"""

import os
import time

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from experimentos import simular_con_extincion
from modelo import ParametrosClima, derivadas_clima

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
y0 = [50.0, 10.0, 2.0, 50.0, 20.0]        # estado inicial: P, H, C, W, N
H_PASO = 0.25                              # paso del solver (suficiente para RK4)
T_FINAL = 720.0                            # 60 años
VENTANA = 60.0                             # se analizan los últimos 5 años
UMBRAL_EXTINCION = 0.05                    # población mínima viable
FRACCION_RIESGO = 0.25                     # "en riesgo" = menos del 25% de lo normal
AMPLITUD_FUERTE = 0.30                     # variación anual relativa que se considera fuerte

R0_VALORES = np.arange(1.0, 12.01, 1.0)    # lluvia base (la de referencia es 6)
T0_VALORES = np.arange(18.0, 38.01, 1.0)   # temperatura media en °C (la óptima es 25)

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

# Clases, de mejor a peor
NOMBRES = ["Estable", "Fluctuaciones fuertes", "En riesgo",
           "Sin depredadores", "Solo plantas", "Colapso total"]
LETRAS = ["E", "F", "R", "C", "P", "X"]
COLORES = ["#2ca25f", "#a1d99b", "#fee08b", "#f46d43", "#a50026", "#252525"]
ESPECIES = ["Plantas", "Herbívoros", "Depredadores"]


def simular_celda(R0, T0, h=H_PASO, t_final=T_FINAL):
    """Simula un clima (R0, T0) y devuelve (tiempo, estados, extinciones)."""
    p = ParametrosClima(R0=float(R0), T0=float(T0))
    return simular_con_extincion(derivadas_clima, y0, t_final, h, args=(p,),
                                 umbral=UMBRAL_EXTINCION)


def resumir(t, Y, ext, t_final=T_FINAL):
    """
    Devuelve (clase, medias de P, H, C) mirando los últimos 5 años.
    Las clases son los índices de NOMBRES.
    """
    ventana = Y[t >= t_final - VENTANA][:, :3]
    medias = ventana.mean(axis=0)
    if 0 in ext:
        return 5, medias
    if 1 in ext:
        return 4, medias
    if 2 in ext:
        return 3, medias
    return None, medias   # sobreviven las tres: falta decidir entre E, F y R


def clasificar_final(t, Y, ext, ref, t_final=T_FINAL):
    """Clase completa (0 a 5), usando las medias de referencia `ref`."""
    clase, medias = resumir(t, Y, ext, t_final)
    if clase is not None:
        return clase, medias
    if (medias < FRACCION_RIESGO * ref).any():
        return 2, medias
    ventana = Y[t >= t_final - VENTANA][:, :3]
    amplitud = ((ventana.max(axis=0) - ventana.min(axis=0)) / np.maximum(medias, 1e-9)).max()
    return (1 if amplitud >= AMPLITUD_FUERTE else 0), medias


# ---------------------------------------------------------------------------
# Mundo de referencia (R0 = 6, T0 = 25)
# ---------------------------------------------------------------------------
t_ref, Y_ref, ext_ref = simular_celda(6.0, 25.0)
ref = Y_ref[t_ref >= T_FINAL - VENTANA][:, :3].mean(axis=0)
print("Mundo de referencia (R0 = 6, T0 = 25 °C): medias de P, H, C =", ref.round(2))

# ---------------------------------------------------------------------------
# Barrido
# ---------------------------------------------------------------------------
n_r, n_t = len(R0_VALORES), len(T0_VALORES)
print(f"\nBARRIDO: {n_r} valores de lluvia x {n_t} de temperatura = {n_r * n_t} simulaciones...")
inicio = time.time()

clases = np.zeros((n_r, n_t), dtype=int)
medias = np.zeros((n_r, n_t, 3))
for i, R0 in enumerate(R0_VALORES):
    for j, T0 in enumerate(T0_VALORES):
        t, Y, ext = simular_celda(R0, T0)
        clases[i, j], medias[i, j] = clasificar_final(t, Y, ext, ref)
print(f"  listo en {time.time() - inicio:.0f} segundos")

# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
print("\nMAPA (filas: lluvia R0, de mayor a menor; columnas: temperatura T0 en °C)")
print("  E=estable  F=fluctuaciones fuertes  R=en riesgo  C=sin depredadores  "
      "P=solo plantas  X=colapso")
print("  R0\\T0 " + "".join(f"{int(T):>3d}" for T in T0_VALORES))
for i in range(n_r - 1, -1, -1):
    print(f"  {R0_VALORES[i]:5.0f} " + "".join(f"{LETRAS[clases[i, j]]:>3}" for j in range(n_t)))

print("\nPORCENTAJE DEL MAPA EN CADA CLASE")
for k, nombre in enumerate(NOMBRES):
    print(f"  {nombre:<22} {100 * np.mean(clases == k):5.1f} %")

# Ventana de supervivencia: dónde coexisten las tres especies de forma sólida
# (estable o con fluctuaciones fuertes). Las celdas "en riesgo" no se cuentan:
# ahí alguna especie está muy baja y, con más tiempo, a veces se extingue.
solida = clases <= 1
print("\nVENTANA DE SUPERVIVENCIA (las tres especies coexisten de forma sólida)")
i6 = int(np.where(R0_VALORES == 6.0)[0][0])
j25 = int(np.where(T0_VALORES == 25.0)[0][0])
cols = np.where(solida[i6])[0]
if len(cols):
    print(f"  Con lluvia normal (R0 = 6): entre T0 = {T0_VALORES[cols[0]]:.0f} y "
          f"{T0_VALORES[cols[-1]]:.0f} °C")
filas = np.where(solida[:, j25])[0]
if len(filas):
    print(f"  Con temperatura óptima (T0 = 25 °C): desde R0 = {R0_VALORES[filas[0]]:.0f} "
          f"(la lluvia normal es 6)")

# ---------------------------------------------------------------------------
# Comprobación de robustez: celdas del borde entre regiones, con más detalle
# ---------------------------------------------------------------------------
print("\nCOMPROBACIÓN DE ROBUSTEZ")
borde = []
for i in range(n_r):
    for j in range(n_t):
        vecinos = [clases[i + di, j + dj] for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= i + di < n_r and 0 <= j + dj < n_t]
        if any(v != clases[i, j] for v in vecinos):
            borde.append((i, j))
rng = np.random.default_rng(0)
muestra = [borde[k] for k in rng.permutation(len(borde))[:12]]
coinciden = 0
for i, j in muestra:
    # paso 2.5 veces más fino y simulación 2 veces más larga (100 años... 125)
    t2, Y2, ext2 = simular_celda(R0_VALORES[i], T0_VALORES[j], h=0.1, t_final=1500.0)
    clase2, _ = clasificar_final(t2, Y2, ext2, ref, t_final=1500.0)
    coinciden += int(clase2 == clases[i, j])
    if clase2 != clases[i, j]:
        print(f"  R0 = {R0_VALORES[i]:.0f}, T0 = {T0_VALORES[j]:.0f}: "
              f"{NOMBRES[clases[i, j]]} (60 años) vs {NOMBRES[clase2]} (125 años, paso fino)")
print(f"  {len(borde)} celdas están en el borde entre regiones; de {len(muestra)} revisadas "
      f"con paso más fino y 125 años, {coinciden} dan la misma clase.")
print("  (los cambios ocurren en celdas 'en riesgo' o casi extintas, que se asientan despacio:\n"
      "   los bordes del mapa pueden correrse una celda con simulaciones más largas)")

# ---------------------------------------------------------------------------
# Gráfica 1: mapa de comportamiento
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))
ax.pcolormesh(np.arange(n_t + 1) + T0_VALORES[0] - 0.5, np.arange(n_r + 1) + R0_VALORES[0] - 0.5,
              clases, cmap=ListedColormap(COLORES), vmin=0, vmax=len(NOMBRES) - 1,
              edgecolors="white", linewidth=0.8)
ax.plot(25.0, 6.0, "*", color="white", markersize=18, markeredgecolor="black", markeredgewidth=1.2)
ax.annotate("mundo de referencia", xy=(25.0, 6.0), xytext=(18.5, 9.5), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="black"),
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
ax.set_xticks(T0_VALORES[::2])
ax.set_yticks(R0_VALORES)
ax.set_xlabel("Temperatura media anual T0 (°C)   (la óptima de las plantas es 25)")
ax.set_ylabel("Lluvia base R0   (la normal es 6)")
ax.set_title("Fase 6: ¿en qué climas sobrevive el ecosistema?\n"
             f"(60 años de simulación; extinción = población bajo {UMBRAL_EXTINCION})")
presentes = sorted(set(clases.flatten()))
ax.legend(handles=[Patch(facecolor=COLORES[k], edgecolor="gray", label=NOMBRES[k]) for k in presentes],
          loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, title="Resultado")
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase6_mapa_coexistencia.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# Gráfica 2: población media de cada especie en cada clima
# ---------------------------------------------------------------------------
fig, ejes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
mapas_color = ["Greens", "Oranges", "Reds"]
for k, (ax, nombre, cmap) in enumerate(zip(ejes, ESPECIES, mapas_color)):
    malla = ax.pcolormesh(np.arange(n_t + 1) + T0_VALORES[0] - 0.5,
                          np.arange(n_r + 1) + R0_VALORES[0] - 0.5,
                          medias[:, :, k], cmap=cmap, vmin=0)
    ax.plot(25.0, 6.0, "*", color="white", markersize=14, markeredgecolor="black")
    fig.colorbar(malla, ax=ax, fraction=0.046, pad=0.03, label="población media")
    ax.set_title(nombre)
    ax.set_xticks(T0_VALORES[::4])
    ax.set_yticks(R0_VALORES[1::2])
    ax.set_xlabel("Temperatura media T0 (°C)")
ejes[0].set_ylabel("Lluvia base R0")
fig.suptitle("Fase 6: población media de cada especie según el clima (blanco = extinta; estrella = referencia)",
             y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase6_mapa_poblaciones.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("\nGráficas guardadas en:", os.path.abspath(CARPETA))
