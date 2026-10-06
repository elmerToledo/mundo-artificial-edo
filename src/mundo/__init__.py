"""
Paquete `mundo`: la parte visual del proyecto (Fase 7).

Está dividido por responsabilidades para que cada archivo se entienda solo:

    config.py       constantes: tamaños, colores, escalas, duración de eventos
    escenarios.py   sequía, ola de calor y extinción como funciones del tiempo
    simulacion.py   avanza las ecuaciones paso a paso (NO usa Pygame)
    entidades.py    plantas, herbívoros y depredadores que se mueven (NO usa Pygame)
    mundo.py        mantiene la cantidad de seres igual a lo que dicen las EDO
    dibujo.py       dibuja el paisaje con Pygame
    graficas.py     dibuja la gráfica en vivo con Pygame
    interfaz.py     botones y panel de datos con Pygame
    main.py         ventana, eventos del teclado/ratón y bucle principal
"""
