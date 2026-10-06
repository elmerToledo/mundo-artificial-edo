"""
simulacion.py
=============
Avanza el sistema de ecuaciones (el mismo modelo de las fases 1 a 6) paso a
paso, para poder verlo en tiempo real. No usa Pygame.

Los números que salen de aquí son los que luego se dibujan: la pantalla no
inventa nada.
"""

from collections import deque

import numpy as np

from modelo import ParametrosClima, derivadas_clima, lluvia, temperatura
from mundo.config import (INTERVALO_HISTORIAL, MESES_PRECALENTAMIENTO,
                          PASO_INTEGRACION, UMBRAL_EXTINCION, VENTANA_GRAFICA,
                          Y_INICIAL)
from mundo.escenarios import Perturbaciones

NOMBRES = ["Plantas", "Herbívoros", "Depredadores", "Agua", "Nutrientes"]


class Simulacion:
    def __init__(self):
        self.perturbaciones = Perturbaciones()
        # El modelo consulta estas dos funciones en cada paso (ver modelo.py)
        self.params = ParametrosClima(
            factor_lluvia=self.perturbaciones.factor_lluvia,
            delta_temperatura=self.perturbaciones.delta_temperatura,
        )
        self.reiniciar()

    # --- Arranque ------------------------------------------------------------
    def reiniciar(self):
        """Vuelve al mundo normal, ya estabilizado en su ciclo anual."""
        self.perturbaciones.limpiar()
        self.t = 0.0
        self.y = np.array(Y_INICIAL, dtype=float)
        self.extintas = set()
        # Se deja correr el mundo sin perturbaciones hasta que se estabilice
        self.avanzar(MESES_PRECALENTAMIENTO, registrar=False)
        # Un año más para medir el estado normal (sirve de referencia 100%)
        suma, pasos = np.zeros(5), 0
        resto = 12.0
        while resto > 1e-9:
            self._paso(min(PASO_INTEGRACION, resto))
            resto -= PASO_INTEGRACION
            suma += self.y
            pasos += 1
        self.referencia = suma / pasos
        self.t_inicio = self.t
        self.historial = deque(maxlen=int(VENTANA_GRAFICA / INTERVALO_HISTORIAL) + 20)
        self._proximo_registro = self.t
        self._registrar()

    # --- Integración (RK4, igual que en solver.py) ---------------------------
    def _paso(self, h):
        f, p, t, y = derivadas_clima, self.params, self.t, self.y
        k1 = np.array(f(t, y, p))
        k2 = np.array(f(t + h / 2, y + h / 2 * k1, p))
        k3 = np.array(f(t + h / 2, y + h / 2 * k2, p))
        k4 = np.array(f(t + h, y + h * k3, p))
        y = np.maximum(y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4), 0.0)
        for i in range(3):                      # extinción: población mínima viable
            if y[i] < UMBRAL_EXTINCION:
                y[i] = 0.0
                self.extintas.add(i)
        self.y = y
        self.t = t + h

    def avanzar(self, meses, registrar=True):
        """Avanza `meses` de tiempo simulado."""
        resto = meses
        while resto > 1e-9:
            h = min(PASO_INTEGRACION, resto)
            self._paso(h)
            resto -= h
            if registrar and self.t >= self._proximo_registro:
                self._registrar()
                self._proximo_registro += INTERVALO_HISTORIAL

    def _registrar(self):
        self.historial.append((self.t - self.t_inicio, *self.y,
                               self.temperatura, self.lluvia))

    # --- Acciones de los botones ---------------------------------------------
    def provocar_sequia(self):
        self.perturbaciones.iniciar_sequia(self.t)

    def provocar_calor(self):
        self.perturbaciones.iniciar_calor(self.t)

    def extinguir_depredadores(self):
        self.y[2] = 0.0
        self.extintas.add(2)
        self.perturbaciones.marcar_extincion(self.t)

    def volver_a_normal(self):
        self.perturbaciones.terminar_activos(self.t)

    def flujos_herbivoros(self):
        """
        Los tres términos de la ecuación de los herbívoros, en unidades por mes:
            nacen   = e_H * a * P * H     (crecen comiendo plantas)
            comidos = b * H * C           (los atrapan los depredadores)
            mueren  = m_H * H             (muerte natural)
        El dibujo los usa para saber cuántas capturas y nacimientos mostrar.
        """
        P, H, C = self.y[0], self.y[1], self.y[2]
        p = self.params
        return p.eH * p.a * P * H, p.b * H * C, p.mH * H

    # --- Lecturas ------------------------------------------------------------
    @property
    def tiempo(self):
        """Meses transcurridos desde que empezó la demostración."""
        return self.t - self.t_inicio

    @property
    def temperatura(self):
        return temperatura(self.t, self.params)

    @property
    def lluvia(self):
        return lluvia(self.t, self.params)

    @property
    def plantas(self):
        return self.y[0]

    @property
    def herbivoros(self):
        return self.y[1]

    @property
    def depredadores(self):
        return self.y[2]

    @property
    def agua(self):
        return self.y[3]
