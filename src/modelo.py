"""
modelo.py
=========
Fase 1 del proyecto "Mundo artificial": modelo mínimo con tres variables.

    P(t): plantas
    H(t): herbívoros
    C(t): depredadores (carnívoros)

Sistema de ecuaciones diferenciales ordinarias no lineales:

    dP/dt = rP * P * (1 - P/KP) - a*P*H - mP*P
    dH/dt = eH * a * P * H - b*H*C - mH*H
    dC/dt = eC * b * H * C - mC*C

Este archivo SOLO contiene la matemática del modelo. No dibuja nada.
"""

from dataclasses import dataclass


@dataclass
class Parametros:
    """Parámetros del modelo (todos en unidades arbitrarias por mes)."""

    # --- Plantas ---
    rP: float = 0.8     # tasa de crecimiento de las plantas
    KP: float = 100.0   # capacidad de carga (máximo que soporta el espacio)
    mP: float = 0.05    # mortalidad natural de las plantas

    # --- Herbívoros ---
    a: float = 0.02     # tasa de consumo de plantas por herbívoro
    eH: float = 0.5     # eficiencia: cuánta planta comida se vuelve herbívoro
    mH: float = 0.2     # mortalidad natural de los herbívoros

    # --- Depredadores ---
    b: float = 0.05     # tasa de captura de herbívoros por depredador
    eC: float = 0.3     # eficiencia: cuánto herbívoro cazado se vuelve depredador
    mC: float = 0.1     # mortalidad natural de los depredadores


def derivadas(t, y, p):
    """
    Lado derecho del sistema: devuelve [dP/dt, dH/dt, dC/dt].

    Parámetros
    ----------
    t : tiempo (el modelo mínimo no depende de t, pero se deja el argumento
        porque los métodos numéricos y el clima de la Fase 3 lo necesitarán)
    y : lista o arreglo [P, H, C]
    p : objeto Parametros
    """
    P, H, C = y

    dP = p.rP * P * (1 - P / p.KP) - p.a * P * H - p.mP * P
    dH = p.eH * p.a * P * H - p.b * H * C - p.mH * H
    dC = p.eC * p.b * H * C - p.mC * C

    return [dP, dH, dC]


def equilibrio_coexistencia(p):
    """
    Punto de equilibrio donde las tres especies coexisten (dP = dH = dC = 0).

    Se obtiene despejando a mano:
        H* = mC / (eC * b)
        P* = KP * (1 - (a*H* + mP) / rP)
        C* = (eH * a * P* - mH) / b

    Devuelve (P*, H*, C*). Si algún valor sale negativo, no existe
    coexistencia con esos parámetros.
    """
    H_eq = p.mC / (p.eC * p.b)
    P_eq = p.KP * (1 - (p.a * H_eq + p.mP) / p.rP)
    C_eq = (p.eH * p.a * P_eq - p.mH) / p.b
    return P_eq, H_eq, C_eq
