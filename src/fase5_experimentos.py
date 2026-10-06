"""
fase5_experimentos.py
=====================
Experimentos sobre el modelo completo (5 variables + clima).

  Experimento C - Eliminación de depredadores:
      En el año 30 se elimina el 95% (y luego el 100%) de los depredadores.
      Se observa el efecto en cascada sobre herbívoros y plantas.

  Experimento E - Punto de no retorno:
      Se aplican sequías de distinta duración y severidad. Si una población
      baja del umbral de cuasi-extinción (0.05), se considera extinta para
      siempre. El resultado es un mapa que indica qué sequías el ecosistema
      resiste y cuáles lo cambian de forma permanente.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase5_experimentos.py
(el mapa de sequías hace 56 simulaciones y puede tardar de 20 a 60 segundos)
"""

import os

import matplotlib
matplotlib.use("Agg")  # guarda imágenes sin abrir ventana; quita esta línea para verlas en pantalla
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from experimentos import simular_con_extincion, simular_con_salto, tiempo_recuperacion
from modelo import ParametrosClima, derivadas_clima
from solver import rk4

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
y0 = [50.0, 10.0, 2.0, 50.0, 20.0]   # estado inicial: P, H, C, W, N
H_PASO = 0.1
T_FINAL = 720.0          # 60 años
T_EVENTO = 360.0         # el evento ocurre en el año 30
UMBRAL_EXTINCION = 0.05  # por debajo de este valor una población se considera extinta

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
os.makedirs(CARPETA, exist_ok=True)

COLOR_ESPECIE = {"P": "tab:green", "H": "tab:orange", "C": "tab:red"}
p = ParametrosClima()

# ===========================================================================
# EXPERIMENTO C: eliminación de depredadores
# ===========================================================================
print("EXPERIMENTO C: eliminación de depredadores en el mes", int(T_EVENTO))

t, Y_normal = rk4(derivadas_clima, y0, 0.0, T_FINAL, H_PASO, args=(p,))


def quitar_depredadores(fraccion_que_queda):
    """Devuelve una función que deja solo esa fracción de los depredadores."""
    def modificar(y):
        y[2] *= fraccion_que_queda
        return y
    return modificar


escenarios = [
    ("Se eliminan el 95% de los depredadores", 0.05, "tab:blue", "-"),
    ("Se eliminan el 100% de los depredadores", 0.0, "tab:red", "--"),
]
resultados = []
ultimo_anio = t >= T_FINAL - 12

for nombre, fraccion, color, estilo in escenarios:
    _, Y = simular_con_salto(derivadas_clima, y0, T_EVENTO, T_FINAL,
                             quitar_depredadores(fraccion), H_PASO, args=(p,))
    resultados.append((nombre, color, estilo, Y))

    despues = t >= T_EVENTO
    pico_H = np.max(Y[despues, 1] / Y_normal[despues, 1])
    caida_P = 100 * np.max(1 - Y[despues, 0] / Y_normal[despues, 0])
    print(f"\n  {nombre}")
    print(f"    Herbívoros: llegan a {pico_H:.1f} veces lo normal")
    print(f"    Plantas   : caen hasta un {caida_P:.0f}% por debajo de lo normal")
    if fraccion > 0:
        rec = tiempo_recuperacion(t, Y, Y_normal, T_EVENTO)
        print(f"    El ecosistema se recupera por completo: {rec:.0f} meses después de la eliminación")
    else:
        print("    Estado final (promedio del último año) frente al mundo normal:")
        for i, nom in enumerate(["Plantas", "Herbívoros", "Depredadores"]):
            final = Y[ultimo_anio, i].mean()
            normal = Y_normal[ultimo_anio, i].mean()
            print(f"      {nom:<13} {final:6.2f}   (normal: {normal:6.2f})")

# Gráfica: tres paneles, uno por especie
ventana = (t >= 336) & (t <= 516)
fig, ejes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
for ax, (i, nombre_especie) in zip(ejes, enumerate(["Plantas (P)", "Herbívoros (H)", "Depredadores (C)"])):
    ax.plot(t[ventana], Y_normal[ventana, i], color="black", linestyle=":", label="Mundo normal")
    for nombre, color, estilo, Y in resultados:
        ax.plot(t[ventana], Y[ventana, i], color=color, linestyle=estilo, label=nombre)
    ax.axvline(T_EVENTO, color="gray", alpha=0.6)
    ax.set_ylabel(nombre_especie)
    ax.grid(alpha=0.3)
ejes[0].legend(loc="lower right", fontsize=8)
ejes[0].set_title("Experimento C: efecto en cascada al eliminar depredadores\n"
                  "(la línea gris vertical marca el momento de la eliminación)")
ejes[-1].set_xlabel("Tiempo (meses)")
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase5_sin_depredadores.png"), dpi=150)
plt.close(fig)

# ===========================================================================
# EXPERIMENTO E: punto de no retorno ante sequías
# ===========================================================================
print("\nEXPERIMENTO E: sequías de distinta severidad y duración (umbral de extinción =",
      UMBRAL_EXTINCION, ")")

DURACIONES = [12, 24, 36, 48, 60, 72, 96, 120]          # meses de sequía
LLUVIAS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]    # fracción de la lluvia normal

NOMBRES_RESULTADO = {0: "Se recupera", 1: "Pierde depredadores",
                     2: "Quedan solo plantas", 3: "Colapso total"}
ETIQUETA_CELDA = {0: "ok", 1: "sin C", 2: "solo P", 3: "colapso"}
COLORES_RESULTADO = ["#4daf4a", "#ffb000", "#d7301f", "#444444"]


def sequia(fraccion, duracion):
    return lambda tt: fraccion if T_EVENTO <= tt < T_EVENTO + duracion else 1.0


def clasificar(extinciones):
    """0 = se recupera, 1 = sin depredadores, 2 = solo plantas, 3 = colapso total."""
    if 0 in extinciones:
        return 3
    if 1 in extinciones:
        return 2
    if 2 in extinciones:
        return 1
    return 0


print("  Calculando el mapa (56 simulaciones)...")
mapa = np.zeros((len(LLUVIAS), len(DURACIONES)), dtype=int)
for i, fraccion in enumerate(LLUVIAS):
    for j, duracion in enumerate(DURACIONES):
        p_sequia = ParametrosClima(factor_lluvia=sequia(fraccion, duracion))
        _, _, ext = simular_con_extincion(derivadas_clima, y0, T_FINAL, H_PASO,
                                          args=(p_sequia,), umbral=UMBRAL_EXTINCION)
        mapa[i, j] = clasificar(ext)

print("\n  Resultado (filas: lluvia durante la sequía; columnas: duración en meses)")
print("  lluvia  " + "".join(f"{d:>8d}" for d in DURACIONES))
for i, fraccion in enumerate(LLUVIAS):
    print(f"  {fraccion*100:4.0f} %  " + "".join(f"{ETIQUETA_CELDA[mapa[i, j]]:>8}" for j in range(len(DURACIONES))))

# Gráfica del mapa
fig, ax = plt.subplots(figsize=(9, 6))
cmap = ListedColormap(COLORES_RESULTADO)
ax.pcolormesh(np.arange(len(DURACIONES) + 1), np.arange(len(LLUVIAS) + 1), mapa,
              cmap=cmap, vmin=0, vmax=3, edgecolors="white", linewidth=2)
for i in range(len(LLUVIAS)):
    for j in range(len(DURACIONES)):
        valor = mapa[i, j]
        ax.text(j + 0.5, i + 0.5, ETIQUETA_CELDA[valor], ha="center", va="center",
                color="white" if valor in (2, 3) else "black", fontsize=10, fontweight="bold")
ax.set_xticks(np.arange(len(DURACIONES)) + 0.5)
ax.set_xticklabels(DURACIONES)
ax.set_yticks(np.arange(len(LLUVIAS)) + 0.5)
ax.set_yticklabels([f"{f*100:.0f}%" for f in LLUVIAS])
ax.set_xlabel("Duración de la sequía (meses)")
ax.set_ylabel("Lluvia durante la sequía\n(% de la lluvia normal)")
ax.set_title("Experimento E: ¿qué sequías resiste el ecosistema?\n"
             f"(extinción = población bajo {UMBRAL_EXTINCION})")
presentes = sorted(set(mapa.flatten()))
ax.legend(handles=[Patch(facecolor=COLORES_RESULTADO[k], label=f"{ETIQUETA_CELDA[k]}: {NOMBRES_RESULTADO[k]}")
                   for k in presentes],
          loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase5_mapa_sequias.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# Trayectorias de tres casos representativos
casos = [
    ("Sequía moderada: 36 meses con 10% de la lluvia  ->  se recupera", 0.10, 36),
    ("Sequía larga: 60 meses con 10% de la lluvia  ->  se extinguen los depredadores", 0.10, 60),
    ("Sequía extrema: 36 meses sin lluvia  ->  se extinguen herbívoros y depredadores", 0.0, 36),
]
fig, ejes = plt.subplots(3, 1, figsize=(10, 10), sharex=True, sharey=True)
print("\n  Casos representativos:")
for ax, (titulo, fraccion, duracion) in zip(ejes, casos):
    p_sequia = ParametrosClima(factor_lluvia=sequia(fraccion, duracion))
    tt, YY, ext = simular_con_extincion(derivadas_clima, y0, T_FINAL, H_PASO,
                                        args=(p_sequia,), umbral=UMBRAL_EXTINCION)
    v = (tt >= 336) & (tt <= 600)
    for i, (clave, nombre) in enumerate([("P", "Plantas"), ("H", "Herbívoros"), ("C", "Depredadores")]):
        ax.plot(tt[v], YY[v, i], color=COLOR_ESPECIE[clave], label=nombre)
    ax.axvspan(T_EVENTO, T_EVENTO + duracion, color="gold", alpha=0.25)
    for i, mes in ext.items():
        ax.annotate("extinción", xy=(mes, 0), xytext=(mes + 6, 12),
                    arrowprops=dict(arrowstyle="->", color="gray"), fontsize=8, color="dimgray")
    ax.set_title(titulo, fontsize=10)
    ax.set_ylabel("Población")
    ax.grid(alpha=0.3)
    nombres_ext = {0: "plantas", 1: "herbívoros", 2: "depredadores"}
    resumen = ", ".join(f"{nombres_ext[i]} (mes {mes:.0f})" for i, mes in sorted(ext.items())) or "ninguna"
    print(f"    {titulo.split('->')[0].strip()}: extinciones = {resumen}")
    print(f"      Estado al final: P={YY[-1, 0]:.1f}  H={YY[-1, 1]:.1f}  C={YY[-1, 2]:.1f}")
ejes[0].legend(loc="center right", fontsize=8)
ejes[-1].set_xlabel("Tiempo (meses)   (la franja amarilla es la sequía)")
fig.tight_layout()
fig.savefig(os.path.join(CARPETA, "fase5_trayectorias_sequia.png"), dpi=150)
plt.close(fig)

print("\nGráficas guardadas en:", os.path.abspath(CARPETA))
