"""
escenarios.py
=============
Las perturbaciones del mundo (sequía, ola de calor, extinción) como funciones
del tiempo. NO modifican las poblaciones a mano: solo cambian la lluvia o la
temperatura que entran a las ecuaciones. El efecto sobre plantas y animales lo
calcula el modelo.
"""

import math
from dataclasses import dataclass

from mundo.config import (CALOR_DURACION, CALOR_GRADOS, SEQUIA_DURACION,
                          SEQUIA_FACTOR_LLUVIA)

SUAVIZADO = 0.5   # meses que tarda en subir/bajar la temperatura (evita saltos)
RETRASO_CALOR = 2.0  # la subida de temperatura se centra 2 meses después del clic


@dataclass
class Evento:
    tipo: str        # "sequia", "calor" o "extincion"
    inicio: float    # mes absoluto en que empieza
    fin: float       # mes absoluto en que termina (igual a inicio en extinción)


class Perturbaciones:
    """Lista de eventos activos y las dos funciones que se conectan al modelo."""

    def __init__(self):
        self.eventos = []

    def limpiar(self):
        self.eventos = []

    # --- Crear eventos -------------------------------------------------------
    def iniciar_sequia(self, t):
        self.eventos.append(Evento("sequia", t, t + SEQUIA_DURACION))

    def iniciar_calor(self, t):
        inicio = t
        self.eventos.append(Evento("calor", inicio, inicio + RETRASO_CALOR + CALOR_DURACION))

    def marcar_extincion(self, t):
        self.eventos.append(Evento("extincion", t, t))

    def terminar_activos(self, t):
        """Botón "Normal": termina la sequía o el calor que estén en curso."""
        for e in self.eventos:
            if e.tipo == "sequia" and e.inicio <= t < e.fin:
                e.fin = t
            elif e.tipo == "calor" and e.inicio <= t < e.fin:
                e.fin = t + RETRASO_CALOR

    # --- Consultas -----------------------------------------------------------
    def activo(self, tipo, t):
        return any(e.tipo == tipo and e.inicio <= t < e.fin for e in self.eventos)

    def meses_restantes(self, tipo, t):
        restos = [e.fin - t for e in self.eventos if e.tipo == tipo and e.inicio <= t < e.fin]
        return max(restos) if restos else 0.0

    # --- Funciones que recibe el modelo (ParametrosClima) --------------------
    def factor_lluvia(self, t):
        """Multiplica la lluvia normal: 1.0 normal, 0.2 durante una sequía."""
        factor = 1.0
        for e in self.eventos:
            if e.tipo == "sequia" and e.inicio <= t < e.fin:
                factor = min(factor, SEQUIA_FACTOR_LLUVIA)
        return factor

    def delta_temperatura(self, t):
        """°C que se suman a la temperatura estacional (subida y bajada suaves)."""
        total = 0.0
        for e in self.eventos:
            if e.tipo != "calor":
                continue
            sube = math.tanh((t - (e.inicio + RETRASO_CALOR)) / SUAVIZADO)
            baja = math.tanh((t - e.fin) / SUAVIZADO)
            total += CALOR_GRADOS * 0.5 * (sube - baja)
        return total
