"""
interfaz.py
===========
Los botones y el panel lateral con los datos en vivo.
"""

import pygame

from mundo import config as cfg


def contiene(rect, pos):
    """True si el punto (x, y) está dentro del rectángulo (x, y, ancho, alto)."""
    x, y, ancho, alto = rect
    return x <= pos[0] <= x + ancho and y <= pos[1] <= y + alto


class Boton:
    def __init__(self, rect, texto, accion):
        self.rect, self.texto, self.accion = rect, texto, accion

    def dibujar(self, pantalla, fuente, posicion_raton):
        color = cfg.BOTON_SOBRE if contiene(self.rect, posicion_raton) else cfg.BOTON
        pygame.draw.rect(pantalla, color, self.rect, border_radius=8)
        etiqueta = fuente.render(self.texto, True, cfg.TEXTO)
        pantalla.blit(etiqueta, etiqueta.get_rect(center=(self.rect[0] + self.rect[2] // 2,
                                                          self.rect[1] + self.rect[3] // 2)))

    def clic(self, posicion):
        if contiene(self.rect, posicion):
            self.accion()
            return True
        return False


def crear_botones(acciones):
    """`acciones` es un diccionario {nombre: función}. Devuelve la lista de botones."""
    x, y0, ancho = cfg.RECT_PANEL[0] + 20, 60, 360
    botones = []
    principales = [("1  Normal", "normal"), ("2  Sequía", "sequia"), ("3  Ola de calor", "calor"),
                   ("4  Extinción de depredadores", "extincion"), ("R  Reiniciar", "reiniciar")]
    for i, (texto, clave) in enumerate(principales):
        botones.append(Boton((x, y0 + i * 52, ancho, 42), texto, acciones[clave]))
    y = y0 + len(principales) * 52 + 6
    botones.append(Boton((x, y, 110, 36), "Más lento", acciones["mas_lento"]))
    botones.append(Boton((x + 125, y, 110, 36), "Pausa", acciones["pausa"]))
    botones.append(Boton((x + 250, y, 110, 36), "Más rápido", acciones["mas_rapido"]))
    return botones


def dibujar_panel(pantalla, fuentes, sim, botones, posicion_raton, velocidad, pausado):
    pantalla.fill(cfg.PANEL, cfg.RECT_PANEL)
    x = cfg.RECT_PANEL[0] + 20
    pantalla.blit(fuentes["titulo"].render("Mundo artificial", True, cfg.TEXTO), (x, 16))
    for b in botones:
        b.dibujar(pantalla, fuentes["normal"], posicion_raton)

    y = 60 + 5 * 52 + 6 + 36 + 14
    anio, mes = int(sim.tiempo // 12) + 1, int(sim.tiempo % 12) + 1
    texto_tiempo = f"Año {anio}, mes {mes}   ·   {velocidad} meses/s" + ("   (pausa)" if pausado else "")
    pantalla.blit(fuentes["normal"].render(texto_tiempo, True, cfg.TEXTO), (x, y))
    pantalla.blit(fuentes["normal"].render(f"Temperatura {sim.temperatura:4.1f} °C   Lluvia {sim.lluvia:3.1f}",
                                           True, cfg.TEXTO_SUAVE), (x, y + 24))
    pantalla.blit(fuentes["normal"].render("Estado: " + _estado(sim), True, cfg.TEXTO), (x, y + 48))

    y += 84
    filas = [("Plantas", cfg.COLOR_P), ("Herbívoros", cfg.COLOR_H), ("Depredadores", cfg.COLOR_C),
             ("Agua", cfg.COLOR_W), ("Nutrientes", cfg.COLOR_N)]
    for i, (nombre, color) in enumerate(filas):
        valor, ref = sim.y[i], sim.referencia[i]
        fila_y = y + i * 26
        pygame.draw.rect(pantalla, color, (x, fila_y + 3, 12, 12))
        pantalla.blit(fuentes["pequena"].render(f"{nombre}", True, cfg.TEXTO), (x + 20, fila_y))
        pantalla.blit(fuentes["pequena"].render(f"{valor:6.1f}", True, cfg.TEXTO), (x + 130, fila_y))
        largo = int(min(valor / ref, 2.0) * 60)
        pygame.draw.rect(pantalla, (60, 68, 84), (x + 200, fila_y + 4, 120, 10))
        pygame.draw.rect(pantalla, color, (x + 200, fila_y + 4, largo, 10))
        pygame.draw.line(pantalla, cfg.TEXTO, (x + 260, fila_y + 1), (x + 260, fila_y + 17), 1)
    pantalla.blit(fuentes["pequena"].render("La barra mide el estado normal en la línea blanca.",
                                            True, cfg.TEXTO_SUAVE), (x, y + 5 * 26 + 4))


def _estado(sim):
    p, t = sim.perturbaciones, sim.t
    partes = []
    if p.activo("sequia", t):
        partes.append(f"sequía ({p.meses_restantes('sequia', t):.0f} meses)")
    if p.activo("calor", t):
        partes.append(f"ola de calor ({p.meses_restantes('calor', t):.0f} meses)")
    extintas = [n for i, n in enumerate(("plantas", "herbívoros", "depredadores")) if i in sim.extintas]
    if extintas:
        partes.append("extintos: " + ", ".join(extintas))
    return " + ".join(partes) if partes else "normal"
