"""
fase7_mundo.py
==============
Mundo visual interactivo (Fase 7). Abre una ventana donde se ve el ecosistema
resolverse en tiempo real a partir de las ecuaciones.

Cómo ejecutarlo (desde la carpeta principal del proyecto):
    python src/fase7_mundo.py

Teclas:  1 Normal   2 Sequía   3 Calor   4 Extinción   R Reiniciar
         ESPACIO pausa   flechas arriba/abajo velocidad   ESC salir
"""

from mundo.main import ejecutar

if __name__ == "__main__":
    ejecutar()
