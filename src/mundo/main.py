"""
main.py
=======
Ventana, teclado, ratón y bucle principal. Solo coordina: la lógica está en
simulacion.py y mundo.py, y el dibujo en dibujo.py, graficas.py e interfaz.py.

Teclas:  1 Normal   2 Sequía   3 Calor   4 Extinción   R Reiniciar
         ESPACIO pausa   flechas arriba/abajo velocidad   ESC salir
"""

import pygame

from mundo import config as cfg
from mundo.dibujo import dibujar_paisaje
from mundo.graficas import dibujar_grafica
from mundo.interfaz import crear_botones, dibujar_panel
from mundo.mundo import Mundo
from mundo.simulacion import Simulacion


class Aplicacion:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Emergencia y estabilidad en un ecosistema artificial")
        self.pantalla = pygame.display.set_mode((cfg.ANCHO, cfg.ALTO))
        self.reloj = pygame.time.Clock()
        self.fuentes = {"titulo": pygame.font.SysFont("arial", 26, bold=True),
                        "normal": pygame.font.SysFont("arial", 18),
                        "pequena": pygame.font.SysFont("arial", 14)}
        self.sim = Simulacion()
        self.mundo = Mundo(cfg.RECT_MUNDO[2], cfg.RECT_MUNDO[3])
        self.mundo.sincronizar(*self.sim.y[:3])
        self.indice_velocidad = cfg.VELOCIDAD_INICIAL
        self.pausado = False
        self.corriendo = True
        self.botones = crear_botones({
            "normal": self.sim.volver_a_normal, "sequia": self.sim.provocar_sequia,
            "calor": self.sim.provocar_calor, "extincion": self.sim.extinguir_depredadores,
            "reiniciar": self.reiniciar, "mas_lento": lambda: self._cambiar_velocidad(-1),
            "mas_rapido": lambda: self._cambiar_velocidad(1), "pausa": self._alternar_pausa,
        })
        self.atajos = {pygame.K_1: self.sim.volver_a_normal, pygame.K_2: self.sim.provocar_sequia,
                       pygame.K_3: self.sim.provocar_calor, pygame.K_4: self.sim.extinguir_depredadores,
                       pygame.K_r: self.reiniciar, pygame.K_SPACE: self._alternar_pausa,
                       pygame.K_UP: lambda: self._cambiar_velocidad(1),
                       pygame.K_DOWN: lambda: self._cambiar_velocidad(-1),
                       pygame.K_ESCAPE: self._salir}

    # --- Acciones --------------------------------------------------------------
    def reiniciar(self):
        self.sim.reiniciar()
        self.mundo.sincronizar(*self.sim.y[:3])

    def _cambiar_velocidad(self, paso):
        self.indice_velocidad = max(0, min(len(cfg.VELOCIDADES) - 1, self.indice_velocidad + paso))

    def _alternar_pausa(self):
        self.pausado = not self.pausado

    def _salir(self):
        self.corriendo = False

    # --- Bucle -------------------------------------------------------------------
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self._salir()
            elif evento.type == pygame.KEYDOWN and evento.key in self.atajos:
                self.atajos[evento.key]()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for boton in self.botones:
                    if boton.clic(evento.pos):
                        break

    def actualizar(self, segundos):
        if self.pausado:
            return
        meses = segundos * cfg.VELOCIDADES[self.indice_velocidad]
        self.sim.avanzar(meses)
        self.mundo.actualizar(segundos, meses, self.sim.flujos_herbivoros())
        self.mundo.sincronizar(*self.sim.y[:3])

    def dibujar(self):
        self.pantalla.fill(cfg.FONDO)
        dibujar_paisaje(self.pantalla, cfg.RECT_MUNDO, self.mundo, self.sim)
        dibujar_grafica(self.pantalla, cfg.RECT_GRAFICA, self.sim, self.fuentes)
        dibujar_panel(self.pantalla, self.fuentes, self.sim, self.botones, pygame.mouse.get_pos(),
                      cfg.VELOCIDADES[self.indice_velocidad], self.pausado)
        pygame.display.flip()

    def ejecutar(self):
        while self.corriendo:
            segundos = min(self.reloj.tick(cfg.FPS) / 1000.0, 0.1)  # tope por si se traba
            self.manejar_eventos()
            self.actualizar(segundos)
            self.dibujar()
        pygame.quit()


def ejecutar():
    Aplicacion().ejecutar()
