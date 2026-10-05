"""
solver.py
=========
Métodos numéricos para resolver sistemas de EDO de la forma

    dy/dt = f(t, y),   y(t0) = y0

Se implementan dos métodos "a mano":

    - Euler (orden 1)
    - Runge-Kutta de cuarto orden, RK4 (orden 4)

Ambos devuelven el tiempo y la solución en cada paso.
"""

import numpy as np


def euler(f, y0, t0, tf, h, args=()):
    """
    Método de Euler:   y_{n+1} = y_n + h * f(t_n, y_n)

    f    : función f(t, y, *args) que devuelve las derivadas
    y0   : estado inicial
    t0   : tiempo inicial
    tf   : tiempo final
    h    : tamaño de paso
    args : parámetros extra que se pasan a f (por ejemplo, el objeto Parametros)

    Devuelve (t, Y) donde Y[i] es el estado en t[i].
    """
    n = int(round((tf - t0) / h))
    t = t0 + h * np.arange(n + 1)
    Y = np.zeros((n + 1, len(y0)))
    Y[0] = y0

    for i in range(n):
        Y[i + 1] = Y[i] + h * np.array(f(t[i], Y[i], *args))
        Y[i + 1] = np.maximum(Y[i + 1], 0.0)  # una población no puede ser negativa

    return t, Y


def rk4(f, y0, t0, tf, h, args=()):
    """
    Runge-Kutta de cuarto orden:

        k1 = f(t_n, y_n)
        k2 = f(t_n + h/2, y_n + h/2 * k1)
        k3 = f(t_n + h/2, y_n + h/2 * k2)
        k4 = f(t_n + h,   y_n + h * k3)
        y_{n+1} = y_n + h/6 * (k1 + 2*k2 + 2*k3 + k4)

    Los argumentos y lo que devuelve son iguales a los de euler().
    """
    n = int(round((tf - t0) / h))
    t = t0 + h * np.arange(n + 1)
    Y = np.zeros((n + 1, len(y0)))
    Y[0] = y0

    for i in range(n):
        ti, yi = t[i], Y[i]
        k1 = np.array(f(ti, yi, *args))
        k2 = np.array(f(ti + h / 2, yi + h / 2 * k1, *args))
        k3 = np.array(f(ti + h / 2, yi + h / 2 * k2, *args))
        k4 = np.array(f(ti + h, yi + h * k3, *args))
        Y[i + 1] = yi + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        Y[i + 1] = np.maximum(Y[i + 1], 0.0)  # una población no puede ser negativa

    return t, Y
