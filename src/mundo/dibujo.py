"""
dibujo.py
=========
Dibuja el paisaje visto desde arriba. Solo dibuja: no calcula nada del modelo.

    - el suelo pasa de verde a marrón cuando falta agua
    - el lago se encoge cuando baja el agua W
    - los árboles se vuelven amarillentos con la sequía
    - un velo rojo aparece cuando sube la temperatura
    - caen gotas cuando llueve
"""

import math
import random

import pygame

from mundo import config as cfg

_azar = random.Random(11)
# Manchas fijas del suelo (x, y, radio_x, radio_y, más_claro?) para darle textura
MANCHAS = [(_azar.uniform(0, cfg.RECT_MUNDO[2]), _azar.uniform(0, cfg.RECT_MUNDO[3]),
            _azar.uniform(30, 90), _azar.uniform(18, 50), _azar.random() < 0.5) for _ in range(70)]


def _mezclar(color_a, color_b, f):
    """Mezcla dos colores: f=0 devuelve a, f=1 devuelve b."""
    f = max(0.0, min(1.0, f))
    return tuple(int(a + (b - a) * f) for a, b in zip(color_a, color_b))


def dibujar_paisaje(pantalla, rect, mundo, sim):
    x0, y0, ancho, alto = rect
    pantalla.set_clip(rect)

    agua_relativa = sim.agua / sim.referencia[3]
    sequedad = 1.0 - agua_relativa
    suelo = _mezclar(cfg.SUELO_HUMEDO, cfg.SUELO_SECO, sequedad * 1.2)
    _dibujar_suelo(pantalla, rect, suelo)
    _dibujar_lago(pantalla, x0, y0, agua_relativa)

    color_arbol = _mezclar(cfg.PLANTA, cfg.PLANTA_SECA, sequedad * 1.3)
    sombra = _mezclar(suelo, (0, 0, 0), 0.30)
    for px, py in mundo.plantas_visibles():
        _arbol(pantalla, x0 + px, y0 + py, color_arbol, sombra)
    for h in mundo.herbivoros:
        _herbivoro(pantalla, x0 + h.x, y0 + h.y, h.angulo)
    for c in mundo.depredadores:
        _depredador(pantalla, x0 + c.x, y0 + c.y, c.angulo)

    for efecto in mundo.efectos:
        _efecto(pantalla, x0 + efecto.x, y0 + efecto.y, efecto, suelo)

    _dibujar_lluvia(pantalla, rect, sim.lluvia)
    _dibujar_calor(pantalla, rect, sim.temperatura)
    pantalla.set_clip(None)


def _dibujar_suelo(pantalla, rect, suelo):
    x0, y0, _, _ = rect
    pantalla.fill(suelo, rect)
    claro, oscuro = _mezclar(suelo, (255, 255, 255), 0.07), _mezclar(suelo, (0, 0, 0), 0.07)
    for mx, my, rx, ry, es_claro in MANCHAS:
        pygame.draw.ellipse(pantalla, claro if es_claro else oscuro,
                            (int(x0 + mx - rx), int(y0 + my - ry), int(rx * 2), int(ry * 2)))


def _dibujar_lago(pantalla, x0, y0, agua_relativa):
    escala = max(0.15, min(1.3, agua_relativa))
    rx, ry = 90 * escala, 55 * escala
    orilla = _mezclar(cfg.LAGO, (255, 255, 255), 0.35)
    pygame.draw.ellipse(pantalla, orilla,
                        (int(x0 + 110 - rx - 4), int(y0 + 90 - ry - 4), int(rx * 2 + 8), int(ry * 2 + 8)))
    pygame.draw.ellipse(pantalla, cfg.LAGO, (int(x0 + 110 - rx), int(y0 + 90 - ry), int(rx * 2), int(ry * 2)))


def _arbol(pantalla, x, y, color, sombra):
    """Árbol visto desde arriba: sombra, tronco y copa con un brillo."""
    radio = 8 + int(x * 7 + y * 13) % 4          # el tamaño varía de un árbol a otro
    pygame.draw.ellipse(pantalla, sombra, (int(x - radio), int(y + 1), radio * 2, int(radio * 0.9)))
    pygame.draw.rect(pantalla, (95, 65, 40), (int(x) - 1, int(y) - 2, 3, 8))
    pygame.draw.circle(pantalla, _mezclar(color, (0, 0, 0), 0.25), (int(x), int(y) - 4), radio + 1)
    pygame.draw.circle(pantalla, color, (int(x), int(y) - 4), radio)
    pygame.draw.circle(pantalla, _mezclar(color, (255, 255, 255), 0.25), (int(x) - 3, int(y) - 7), radio // 3)


def _herbivoro(pantalla, x, y, angulo):
    """Herbívoro: cuerpo, cabeza hacia donde va, ojo y colita blanca."""
    dx, dy = math.cos(angulo), math.sin(angulo)
    pygame.draw.circle(pantalla, (150, 85, 10), (int(x), int(y)), 8)
    pygame.draw.circle(pantalla, cfg.HERBIVORO, (int(x), int(y)), 7)
    pygame.draw.circle(pantalla, (255, 255, 255), (int(x - dx * 8), int(y - dy * 8)), 3)
    cx, cy = x + dx * 8, y + dy * 8
    pygame.draw.circle(pantalla, cfg.HERBIVORO, (int(cx), int(cy)), 5)
    pygame.draw.circle(pantalla, (20, 20, 20), (int(cx + dx * 2), int(cy + dy * 2)), 1)


def _depredador(pantalla, x, y, angulo):
    """Depredador: cuerpo oscuro, cabeza con orejas puntiagudas, cola y ojos amarillos."""
    dx, dy = math.cos(angulo), math.sin(angulo)
    px, py = -dy, dx                              # perpendicular, para abrir las orejas
    pygame.draw.line(pantalla, (110, 20, 20), (x - dx * 8, y - dy * 8), (x - dx * 18, y - dy * 18), 4)
    pygame.draw.circle(pantalla, (90, 15, 15), (int(x), int(y)), 11)
    pygame.draw.circle(pantalla, cfg.DEPREDADOR, (int(x), int(y)), 10)
    cx, cy = x + dx * 11, y + dy * 11
    for lado in (-1, 1):
        oreja = [(cx + px * lado * 6 - dx * 2, cy + py * lado * 6 - dy * 2),
                 (cx + px * lado * 2 - dx * 3, cy + py * lado * 2 - dy * 3),
                 (cx + px * lado * 5 - dx * 9, cy + py * lado * 5 - dy * 9)]
        pygame.draw.polygon(pantalla, (150, 25, 25), oreja)
    pygame.draw.circle(pantalla, cfg.DEPREDADOR, (int(cx), int(cy)), 7)
    for lado in (-1, 1):
        pygame.draw.circle(pantalla, (255, 230, 80),
                           (int(cx + dx * 2 + px * lado * 3), int(cy + dy * 2 + py * lado * 3)), 2)


def _efecto(pantalla, x, y, efecto, suelo):
    """Anillo que crece y se desvanece: rojo = captura, verde = nacimiento."""
    f = efecto.progreso
    base = (255, 50, 50) if efecto.tipo == "captura" else (130, 255, 130)
    color = _mezclar(base, suelo, f * 0.85)
    pygame.draw.circle(pantalla, color, (int(x), int(y)), int(6 + f * 24), 3)
    if efecto.tipo == "captura" and f < 0.5:      # destello en el centro
        pygame.draw.circle(pantalla, (255, 255, 255), (int(x), int(y)), int(7 * (1 - f * 2)) + 1)


def _dibujar_lluvia(pantalla, rect, lluvia):
    x0, y0, ancho, alto = rect
    for _ in range(int(max(0.0, lluvia - 1.0) * 5)):
        gx, gy = x0 + random.uniform(0, ancho), y0 + random.uniform(0, alto)
        pygame.draw.line(pantalla, (170, 200, 240), (gx, gy), (gx - 2, gy + 8), 1)


def _dibujar_calor(pantalla, rect, temperatura):
    x0, y0, ancho, alto = rect
    alfa = int(max(0.0, min(1.0, (temperatura - 28.0) / 12.0)) * 110)
    if alfa > 0:
        velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        velo.fill((255, 70, 0, alfa))
        pantalla.blit(velo, (x0, y0))
