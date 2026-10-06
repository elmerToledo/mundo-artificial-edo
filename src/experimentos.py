"""
experimentos.py
===============
Herramientas compartidas por los scripts de experimentos.

    simular_con_salto      : simula y, en un mes dado, cambia el estado de golpe
                             (por ejemplo, eliminar depredadores).
    simular_con_extincion  : simula y, si una población baja de un umbral,
                             la declara extinta (queda en 0 para siempre).
    tiempo_recuperacion    : meses que tarda el sistema en volver a su
                             comportamiento normal después de una perturbación.

Nota sobre la extinción: en una ecuación diferencial las poblaciones son
números continuos, y una población de 0.001 animales "se recupera" sola
aunque en la realidad ya no quedaría ninguno. Por eso se define un UMBRAL de
cuasi-extinción: por debajo de él la población se considera extinta.
"""

import numpy as np

from solver import rk4


def simular_con_salto(f, y0, t_salto, t_fin, modificar, h, args=()):
    """
    Simula de 0 a t_salto, aplica modificar(estado) al estado en ese instante
    y continúa hasta t_fin.

    modificar : función que recibe una copia del estado y devuelve el estado
                modificado, por ejemplo  lambda y: [y[0], y[1], 0.0, y[3], y[4]]
    Devuelve (t, Y) como los métodos de solver.py.
    """
    t1, Y1 = rk4(f, y0, 0.0, t_salto, h, args=args)
    y_nuevo = np.array(modificar(Y1[-1].copy()), dtype=float)
    t2, Y2 = rk4(f, y_nuevo, t_salto, t_fin, h, args=args)
    return np.concatenate([t1, t2[1:]]), np.vstack([Y1, Y2[1:]])


def simular_con_extincion(f, y0, t_fin, h, args=(), umbral=0.05, indices=(0, 1, 2)):
    """
    Simula con RK4 revisando cada mes si alguna población bajó del umbral.
    Si ocurre, esa población se pone en 0 y ya no puede volver (no hay
    inmigración ni semillas externas).

    indices : posiciones del estado que son poblaciones (P, H, C = 0, 1, 2)
    Devuelve (t, Y, extinciones) donde extinciones es un diccionario
    {posición: mes en que se extinguió}.
    """
    y = np.array(y0, dtype=float)
    tiempos = [np.array([0.0])]
    estados = [y.reshape(1, -1).copy()]
    extinciones = {}

    t_ini = 0.0
    while t_ini < t_fin - 1e-9:
        t, Y = rk4(f, y, t_ini, t_ini + 1.0, h, args=args)
        y = Y[-1].copy()
        for i in indices:
            if y[i] < umbral and i not in extinciones:
                extinciones[i] = t[-1]
            if i in extinciones:
                y[i] = 0.0
        Y[-1] = y
        tiempos.append(t[1:])
        estados.append(Y[1:])
        t_ini += 1.0

    return np.concatenate(tiempos), np.vstack(estados), extinciones


def tiempo_recuperacion(t, Y, Y_ref, t_fin_perturbacion, banda=0.05, indices=(0, 1, 2)):
    """
    Meses, contados desde que termina la perturbación, hasta que las
    poblaciones vuelven y se quedan dentro de la banda (5% por defecto) de la
    simulación de referencia (mundo normal) en el mismo mes.

    Devuelve 0 si nunca se salieron de la banda después de la perturbación.
    """
    idx = list(indices)
    desviacion = np.abs(Y[:, idx] - Y_ref[:, idx]) / np.maximum(Y_ref[:, idx], 1e-9)
    fuera = np.where((desviacion > banda).any(axis=1) & (t >= t_fin_perturbacion))[0]
    return (t[fuera[-1]] - t_fin_perturbacion) if len(fuera) else 0.0
