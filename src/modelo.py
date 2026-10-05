"""
modelo.py
=========
Modelo matemático del proyecto "Mundo artificial".

Este archivo contiene SOLO la matemática (no dibuja nada). Tiene dos niveles:

FASE 1 - modelo mínimo, 3 variables:
    P(t): plantas        H(t): herbívoros        C(t): depredadores

    dP/dt = rP * P * (1 - P/KP) - a*P*H - mP*P
    dH/dt = eH * a * P * H - b*H*C - mH*H
    dC/dt = eC * b * H * C - mC*C

FASE 2 - modelo con recursos, 5 variables (se agregan agua y nutrientes):
    W(t): agua           N(t): nutrientes

    fW(W) = W / (KW + W)          saturación del agua
    fN(N) = N / (KN + N)          saturación de los nutrientes

    dP/dt = rP * P * (1 - P/KP) * fW * fN - a*P*H - mP*P
    dH/dt = eH * a * P * H - b*H*C - mH*H
    dC/dt = eC * b * H * C - mC*C
    dW/dt = R0 * lluvia(t) - lW*W - uW*P*fW
    dN/dt = SN + rho*(a*P*H + b*H*C + mP*P + mH*H + mC*C) - uN*P*fN - lN*N

En la Fase 2 las plantas dependen de los recursos, y los recursos dependen de
las plantas. La temperatura se agregará en la Fase 3.
"""

from dataclasses import dataclass
from typing import Callable, Optional


# ===========================================================================
# FASE 1: modelo mínimo (P, H, C)
# ===========================================================================

@dataclass
class Parametros:
    """Parámetros del modelo mínimo (unidades arbitrarias por mes)."""

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
    Lado derecho del modelo mínimo: devuelve [dP/dt, dH/dt, dC/dt].

    t : tiempo (este modelo no depende de t, pero los métodos numéricos
        siempre lo pasan y el clima de la Fase 3 lo necesitará)
    y : [P, H, C]
    p : objeto Parametros
    """
    P, H, C = y

    dP = p.rP * P * (1 - P / p.KP) - p.a * P * H - p.mP * P
    dH = p.eH * p.a * P * H - p.b * H * C - p.mH * H
    dC = p.eC * p.b * H * C - p.mC * C

    return [dP, dH, dC]


def equilibrio_coexistencia(p):
    """
    Punto de equilibrio del modelo mínimo donde las tres especies coexisten
    (dP = dH = dC = 0). Se obtiene despejando a mano:

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


# ===========================================================================
# FASE 2: modelo con recursos (P, H, C, W, N)
# ===========================================================================

@dataclass
class ParametrosCompleto(Parametros):
    """
    Parámetros del modelo con recursos. Hereda todos los de la Fase 1
    (rP, KP, mP, a, eH, mH, b, eC, mC) y agrega los del agua y los nutrientes.
    """

    # --- Saturación: con cuánto recurso la planta crece a la mitad de su máximo ---
    KW: float = 20.0    # constante de saturación del agua
    KN: float = 10.0    # constante de saturación de los nutrientes

    # --- Agua ---
    R0: float = 6.0     # lluvia base (entrada de agua por mes)
    lW: float = 0.1     # pérdida de agua (evaporación, drenaje)
    uW: float = 0.1     # consumo de agua por las plantas

    # --- Nutrientes ---
    SN: float = 1.0     # reposición natural de nutrientes
    rho: float = 0.1    # fracción de materia que se recicla a nutrientes
    uN: float = 0.02    # consumo de nutrientes por las plantas
    lN: float = 0.05    # pérdida de nutrientes (lavado del suelo)

    # --- Perturbación opcional de lluvia ---
    # Función lluvia(t) que multiplica a R0. Ejemplo: lambda t: 0.2 si hay
    # sequía y 1.0 si no. Si es None, la lluvia es constante.
    factor_lluvia: Optional[Callable[[float], float]] = None


def _lado_derecho(y, p, factor):
    """Ecuaciones del modelo con recursos, con el factor de lluvia ya calculado."""
    P, H, C, W, N = y

    fW = W / (p.KW + W)   # entre 0 (sin agua) y 1 (agua de sobra)
    fN = N / (p.KN + N)   # entre 0 (sin nutrientes) y 1 (nutrientes de sobra)

    dP = p.rP * P * (1 - P / p.KP) * fW * fN - p.a * P * H - p.mP * P
    dH = p.eH * p.a * P * H - p.b * H * C - p.mH * H
    dC = p.eC * p.b * H * C - p.mC * C

    dW = p.R0 * factor - p.lW * W - p.uW * P * fW

    reciclaje = p.a * P * H + p.b * H * C + p.mP * P + p.mH * H + p.mC * C
    dN = p.SN + p.rho * reciclaje - p.uN * P * fN - p.lN * N

    return [dP, dH, dC, dW, dN]


def derivadas_completo(t, y, p):
    """
    Lado derecho del modelo con recursos: devuelve [dP/dt, dH/dt, dC/dt, dW/dt, dN/dt].

    t : tiempo (se usa para la lluvia variable)
    y : [P, H, C, W, N]
    p : objeto ParametrosCompleto
    """
    factor = p.factor_lluvia(t) if p.factor_lluvia is not None else 1.0
    return _lado_derecho(y, p, factor)


def equilibrio_completo(p, y_inicial=(50.0, 10.0, 5.0, 30.0, 30.0)):
    """
    Busca el equilibrio del modelo con recursos (todas las derivadas = 0,
    con lluvia normal) resolviendo el sistema de ecuaciones no lineales.

    Devuelve un arreglo [P*, H*, C*, W*, N*]. Con otros parámetros puede
    ser necesario cambiar y_inicial para que el método encuentre el equilibrio.
    """
    from scipy.optimize import fsolve

    def f(y):
        return _lado_derecho(y, p, 1.0)

    return fsolve(f, y_inicial, xtol=1e-12)
