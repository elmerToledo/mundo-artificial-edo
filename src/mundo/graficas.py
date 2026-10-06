"""
graficas.py
===========
Gráfica en vivo de las tres poblaciones, en porcentaje del estado normal
(100% = lo que hay en el mundo sin perturbaciones). Las franjas de color marcan
cuándo hubo sequía o calor, y una línea roja marca la extinción provocada.
"""

import pygame

from mundo import config as cfg

MARGEN_IZQ, MARGEN_DER, MARGEN_SUP, MARGEN_INF = 55, 15, 30, 28
SERIES = [(1, "Plantas", cfg.COLOR_P), (2, "Herbívoros", cfg.COLOR_H), (3, "Depredadores", cfg.COLOR_C)]
COLORES_EVENTO = {"sequia": cfg.EVENTO_SEQUIA, "calor": cfg.EVENTO_CALOR}


def dibujar_grafica(pantalla, rect, sim, fuentes):
    x0, y0, ancho, alto = rect
    pantalla.fill(cfg.PANEL, rect)
    izq, der = x0 + MARGEN_IZQ, x0 + ancho - MARGEN_DER
    arriba, abajo = y0 + MARGEN_SUP, y0 + alto - MARGEN_INF

    datos = list(sim.historial)
    ahora = sim.tiempo
    t_min = max(0.0, ahora - cfg.VENTANA_GRAFICA)
    t_max = max(ahora, cfg.VENTANA_GRAFICA)
    maximo = max(150.0, _valor_maximo(datos, sim))

    def px(t):
        return izq + (t - t_min) / (t_max - t_min) * (der - izq)

    def py(porcentaje):
        return abajo - porcentaje / maximo * (abajo - arriba)

    _franjas_de_eventos(pantalla, sim, izq, der, arriba, abajo, t_min, t_max, px)
    _ejes(pantalla, fuentes, izq, der, arriba, abajo, maximo, py, px, t_min, t_max)

    # --- Series ------------------------------------------------------------------
    for indice, _, color in SERIES:
        referencia = sim.referencia[indice - 1]
        puntos = [(px(f[0]), py(f[indice] / referencia * 100.0)) for f in datos if f[0] >= t_min]
        if len(puntos) >= 2:
            pygame.draw.lines(pantalla, color, False, puntos, 2)

    # --- Leyenda -----------------------------------------------------------------
    x = izq + 10
    for _, nombre, color in SERIES:
        pygame.draw.rect(pantalla, color, (x, y0 + 9, 14, 10))
        etiqueta = fuentes["pequena"].render(nombre, True, cfg.TEXTO)
        pantalla.blit(etiqueta, (x + 20, y0 + 6))
        x += 30 + etiqueta.get_width() + 20


def _valor_maximo(datos, sim):
    mejor = 0.0
    for f in datos:
        for indice, _, _ in SERIES:
            mejor = max(mejor, f[indice] / sim.referencia[indice - 1] * 100.0)
    return mejor * 1.1


def _franjas_de_eventos(pantalla, sim, izq, der, arriba, abajo, t_min, t_max, px):
    capa = pygame.Surface((der - izq, abajo - arriba), pygame.SRCALPHA)
    for e in sim.perturbaciones.eventos:
        inicio, fin = e.inicio - sim.t_inicio, min(e.fin, sim.t) - sim.t_inicio
        if fin < t_min:
            continue
        if e.tipo == "extincion":
            x = px(inicio) - izq
            pygame.draw.line(capa, (*cfg.EVENTO_EXTINCION, 220), (x, 0), (x, abajo - arriba), 2)
        else:
            a, b = px(max(inicio, t_min)) - izq, px(fin) - izq
            capa.fill((*COLORES_EVENTO[e.tipo], 55), (int(a), 0, int(max(1, b - a)), abajo - arriba))
    pantalla.blit(capa, (izq, arriba))


def _ejes(pantalla, fuentes, izq, der, arriba, abajo, maximo, py, px, t_min, t_max):
    pygame.draw.line(pantalla, cfg.TEXTO_SUAVE, (izq, arriba), (izq, abajo), 1)
    pygame.draw.line(pantalla, cfg.TEXTO_SUAVE, (izq, abajo), (der, abajo), 1)
    # Líneas horizontales cada 50%; la de 100% (estado normal) más marcada
    valor = 0
    while valor <= maximo:
        y = py(valor)
        pygame.draw.line(pantalla, cfg.TEXTO if valor == 100 else (60, 68, 84), (izq, y), (der, y), 1)
        pantalla.blit(fuentes["pequena"].render(f"{valor}%", True, cfg.TEXTO_SUAVE), (izq - 45, y - 8))
        valor += 50
    # Marcas de tiempo: una por año
    anio = int(t_min // 12) + 1
    while anio * 12 <= t_max:
        x = px(anio * 12)
        pygame.draw.line(pantalla, cfg.TEXTO_SUAVE, (x, abajo), (x, abajo + 4), 1)
        pantalla.blit(fuentes["pequena"].render(f"año {anio}", True, cfg.TEXTO_SUAVE), (x - 18, abajo + 6))
        anio += 1
