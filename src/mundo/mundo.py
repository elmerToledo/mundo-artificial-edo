"""
mundo.py
========
Conecta las ecuaciones con el dibujo.

Cuántos seres hay lo dicen las poblaciones del modelo (sincronizar). Además,
las capturas y los nacimientos que se ven siguen las TASAS de la ecuación de
los herbívoros:

    nacen   = e_H a P H      -> aparece un herbívoro nuevo (anillo verde)
    comidos = b H C          -> un depredador atrapa a uno (anillo rojo)

Cada tasa va llenando un "permiso". Un depredador solo puede comerse a un
herbívoro cuando lo alcanza Y hay un permiso disponible. Así, si la ecuación
dice que se comen pocos herbívoros (por ejemplo en una sequía), se ven pocas
capturas. Cuando no hay depredadores, no hay capturas. El resto del ajuste
(muerte natural, redondeos) lo hace `sincronizar`.
"""

import math
import random

from mundo.config import (ANIMALES_POR_DEPREDADOR, ANIMALES_POR_HERBIVORO,
                          CAPACIDAD_PLANTAS, MAX_ANIMALES, MAX_PLANTAS_DIBUJADAS)
from mundo.entidades import Depredador, Efecto, Herbivoro

MAX_PERMISOS = 3.0   # no se acumulan más de 3 eventos pendientes


class Mundo:
    def __init__(self, ancho, alto, semilla=7):
        self.ancho, self.alto = ancho, alto
        azar = random.Random(semilla)
        # Posiciones fijas: cuando bajan las plantas desaparecen las últimas de la
        # lista y, al recuperarse, reaparecen en el mismo sitio.
        self.posiciones_plantas = [
            (azar.uniform(15, ancho - 15), azar.uniform(15, alto - 15))
            for _ in range(MAX_PLANTAS_DIBUJADAS)
        ]
        self.n_plantas = 0
        self.herbivoros = []
        self.depredadores = []
        self.efectos = []
        self.permisos_caza = 0.0
        self.permisos_nacimiento = 0.0
        self.capturas = 0     # total de capturas mostradas (para comprobar)

    # --- Cantidad de seres según el modelo --------------------------------------
    def sincronizar(self, plantas, herbivoros, depredadores):
        """Ajusta la cantidad de seres dibujados a las poblaciones del modelo."""
        n = round(plantas / CAPACIDAD_PLANTAS * MAX_PLANTAS_DIBUJADAS)
        self.n_plantas = max(0, min(MAX_PLANTAS_DIBUJADAS, n))
        self._ajustar(self.herbivoros, round(herbivoros * ANIMALES_POR_HERBIVORO), Herbivoro)
        self._ajustar(self.depredadores, round(depredadores * ANIMALES_POR_DEPREDADOR), Depredador)

    def _ajustar(self, lista, deseados, clase):
        deseados = max(0, min(MAX_ANIMALES, deseados))
        while len(lista) < deseados:
            lista.append(clase(self.ancho, self.alto))
        while len(lista) > deseados:
            lista.pop(random.randrange(len(lista)))

    # --- Movimiento, capturas y nacimientos ---------------------------------------
    def actualizar(self, segundos, meses, flujos):
        """
        segundos: tiempo real del cuadro (para mover los dibujos)
        meses   : tiempo simulado del cuadro (para acumular capturas y nacimientos)
        flujos  : (nacen, comidos, mueren) por mes, de Simulacion.flujos_herbivoros()
        """
        nacen, comidos, _ = flujos
        self.permisos_caza = min(MAX_PERMISOS, self.permisos_caza + comidos * ANIMALES_POR_HERBIVORO * meses)
        self.permisos_nacimiento = min(MAX_PERMISOS, self.permisos_nacimiento + nacen * ANIMALES_POR_HERBIVORO * meses)

        presas = self._asignar_presas()
        capturados = []
        for depredador, presa in zip(self.depredadores, presas):
            depredador.actualizar(segundos, presa, self.depredadores)
            if (presa is not None and self.permisos_caza >= 1 and presa not in capturados
                    and depredador.puede_capturar(presa)):
                capturados.append(presa)
                depredador.empezar_a_comer()
                self.permisos_caza -= 1
                self.efectos.append(Efecto(presa.x, presa.y, "captura"))
                self.capturas += 1
        for h in self.herbivoros:
            h.actualizar(segundos, self.depredadores)
        self.herbivoros = [h for h in self.herbivoros if h not in capturados]

        self._nacimientos()
        for efecto in self.efectos:
            efecto.edad += segundos
        self.efectos = [e for e in self.efectos if e.vivo]

    def _asignar_presas(self):
        """A cada depredador le toca un herbívoro distinto (si hay suficientes)."""
        ocupados, presas = set(), []
        for c in self.depredadores:
            libres = [h for h in self.herbivoros if id(h) not in ocupados] or self.herbivoros
            presa = min(libres, key=lambda h: math.hypot(h.x - c.x, h.y - c.y), default=None)
            if presa is not None:
                ocupados.add(id(presa))
            presas.append(presa)
        return presas

    def _nacimientos(self):
        while self.permisos_nacimiento >= 1 and self.herbivoros and len(self.herbivoros) < MAX_ANIMALES:
            padre = random.choice(self.herbivoros)
            cria = Herbivoro(self.ancho, self.alto)
            cria.x = min(max(padre.x + random.uniform(-15, 15), 10), self.ancho - 10)
            cria.y = min(max(padre.y + random.uniform(-15, 15), 10), self.alto - 10)
            self.herbivoros.append(cria)
            self.efectos.append(Efecto(cria.x, cria.y, "nacimiento"))
            self.permisos_nacimiento -= 1

    def plantas_visibles(self):
        return self.posiciones_plantas[:self.n_plantas]
