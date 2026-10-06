"""
entidades.py
============
Los seres que se mueven por el paisaje. Aquí solo hay posición y movimiento
(no hay Pygame). Cuántos hay lo decide `mundo.py` según las ecuaciones.
"""

import math
import random

DISTANCIA_HUIDA = 70.0   # a esta distancia un herbívoro nota al depredador


class Animal:
    """Base: se mueve en línea con pequeños giros al azar y rebota en los bordes."""

    velocidad = 30.0

    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.x = random.uniform(20, ancho - 20)
        self.y = random.uniform(20, alto - 20)
        self.angulo = random.uniform(0, 2 * math.pi)

    def _vagar(self, dt):
        self.angulo += random.uniform(-3.0, 3.0) * dt

    def _avanzar(self, dt, velocidad):
        self.x += math.cos(self.angulo) * velocidad * dt
        self.y += math.sin(self.angulo) * velocidad * dt
        if self.x < 10 or self.x > self.ancho - 10:
            self.angulo = math.pi - self.angulo
        if self.y < 10 or self.y > self.alto - 10:
            self.angulo = -self.angulo
        self.x = min(max(self.x, 10), self.ancho - 10)
        self.y = min(max(self.y, 10), self.alto - 10)

    def _empuje_bordes(self, vx, vy, margen=90.0, fuerza=1.5):
        """Suma a la dirección (vx, vy) un empujón hacia el centro cerca de las paredes."""
        if self.x < margen:
            vx += (margen - self.x) / margen * fuerza
        elif self.x > self.ancho - margen:
            vx -= (self.x - (self.ancho - margen)) / margen * fuerza
        if self.y < margen:
            vy += (margen - self.y) / margen * fuerza
        elif self.y > self.alto - margen:
            vy -= (self.y - (self.alto - margen)) / margen * fuerza
        return vx, vy

    def _mas_cercano(self, otros):
        """Devuelve (animal, distancia) del más cercano, o (None, inf) si no hay."""
        mejor, mejor_d = None, float("inf")
        for o in otros:
            d = math.hypot(o.x - self.x, o.y - self.y)
            if d < mejor_d:
                mejor, mejor_d = o, d
        return mejor, mejor_d


class Herbivoro(Animal):
    velocidad = 30.0
    velocidad_huida = 85.0

    def actualizar(self, dt, depredadores):
        cercano, d = self._mas_cercano(depredadores)
        if cercano is not None and d < DISTANCIA_HUIDA:
            # huye en dirección contraria al depredador, pero sin chocar con la pared
            vx, vy = self.x - cercano.x, self.y - cercano.y
            norma = math.hypot(vx, vy) or 1.0
            vx, vy = self._empuje_bordes(vx / norma, vy / norma)
            self.angulo = math.atan2(vy, vx)
            self._avanzar(dt, self.velocidad_huida)
        else:
            self._vagar(dt)
            self._avanzar(dt, self.velocidad)


class Depredador(Animal):
    velocidad = 40.0
    velocidad_caza = 60.0
    DISTANCIA_ALCANCE = 16.0     # a esta distancia puede atrapar a su presa
    DISTANCIA_SEPARACION = 30.0  # los depredadores se apartan entre sí
    SEGUNDOS_COMIENDO = 1.2      # descansa un momento después de atrapar

    def __init__(self, ancho, alto):
        super().__init__(ancho, alto)
        self.comiendo = 0.0

    def puede_capturar(self, presa):
        distancia = math.hypot(presa.x - self.x, presa.y - self.y)
        return self.comiendo <= 0 and distancia < self.DISTANCIA_ALCANCE

    def empezar_a_comer(self):
        self.comiendo = self.SEGUNDOS_COMIENDO

    def actualizar(self, dt, presa, depredadores):
        """`presa` es el herbívoro que le tocó perseguir (o None si no hay)."""
        if self.comiendo > 0:                        # quieto, comiendo
            self.comiendo -= dt
            self._avanzar(dt, 5.0)
            return
        if presa is None:
            self._vagar(dt)
            self._avanzar(dt, self.velocidad * 0.5)
            return
        vx, vy = presa.x - self.x, presa.y - self.y
        norma = math.hypot(vx, vy) or 1.0
        vx, vy = vx / norma, vy / norma
        for otro in depredadores:                    # separación entre depredadores
            dx, dy = self.x - otro.x, self.y - otro.y
            dist = math.hypot(dx, dy)
            if otro is not self and 0 < dist < self.DISTANCIA_SEPARACION:
                vx += dx / dist * 0.8
                vy += dy / dist * 0.8
        vx, vy = self._empuje_bordes(vx, vy, margen=60.0, fuerza=1.0)
        self.angulo = math.atan2(vy, vx)
        self._avanzar(dt, self.velocidad_caza)


class Efecto:
    """Anillo que se expande un instante: rojo en una captura, verde en un nacimiento."""

    def __init__(self, x, y, tipo, duracion=0.8):
        self.x, self.y, self.tipo = x, y, tipo
        self.duracion, self.edad = duracion, 0.0

    @property
    def progreso(self):
        return min(1.0, self.edad / self.duracion)

    @property
    def vivo(self):
        return self.edad < self.duracion
