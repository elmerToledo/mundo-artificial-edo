"""
config.py
=========
Todas las constantes del mundo visual en un solo lugar. Si quieres cambiar un
color, la velocidad o cuánto dura la sequía, se hace aquí y no en el resto.
"""

# --- Ventana (x, y, ancho, alto) ---------------------------------------------
ANCHO, ALTO = 1280, 720
FPS = 60
RECT_MUNDO = (0, 0, 880, 470)      # el paisaje
RECT_GRAFICA = (0, 470, 880, 250)  # la gráfica en vivo
RECT_PANEL = (880, 0, 400, 720)    # botones y datos

# --- Tiempo ------------------------------------------------------------------
# El modelo mide el tiempo en meses. Estas son las velocidades de la demo
# (meses simulados por cada segundo real) y se cambian con los botones.
VELOCIDADES = [1, 2, 4, 8, 16]
VELOCIDAD_INICIAL = 2              # posición en la lista: 4 meses por segundo
PASO_INTEGRACION = 0.05            # paso h de RK4, en meses
MESES_PRECALENTAMIENTO = 480       # el mundo arranca ya estabilizado (40 años)
INTERVALO_HISTORIAL = 0.5          # cada cuántos meses se guarda un punto
VENTANA_GRAFICA = 96               # meses que muestra la gráfica (8 años)

# --- Perturbaciones (los mismos valores de las fases 2, 3 y 5) ---------------
SEQUIA_FACTOR_LLUVIA = 0.2         # llueve el 20% de lo normal
SEQUIA_DURACION = 50               # meses
CALOR_GRADOS = 8.0                 # °C que se suman
CALOR_DURACION = 12                # meses
UMBRAL_EXTINCION = 0.05            # población mínima viable (ver README)

# Estado inicial del modelo: plantas, herbívoros, depredadores, agua, nutrientes
Y_INICIAL = (50.0, 10.0, 2.0, 50.0, 20.0)

# --- Cuántos dibujos representa cada población -------------------------------
CAPACIDAD_PLANTAS = 100            # el modelo usa K_P = 100
MAX_PLANTAS_DIBUJADAS = 100
ANIMALES_POR_HERBIVORO = 3         # cada unidad de H se dibuja como 3 puntos
ANIMALES_POR_DEPREDADOR = 2
MAX_ANIMALES = 120

# --- Colores (R, G, B) -------------------------------------------------------
FONDO = (24, 28, 36)
PANEL = (34, 40, 52)
TEXTO = (235, 238, 245)
TEXTO_SUAVE = (150, 158, 175)
SUELO_HUMEDO = (70, 130, 60)
SUELO_SECO = (176, 150, 96)
LAGO = (60, 120, 190)
PLANTA = (30, 105, 45)
PLANTA_SECA = (130, 125, 60)
HERBIVORO = (245, 160, 40)
DEPREDADOR = (220, 50, 50)
COLOR_P, COLOR_H, COLOR_C = PLANTA, HERBIVORO, DEPREDADOR
COLOR_W, COLOR_N = LAGO, (150, 110, 80)
BOTON = (58, 68, 88)
BOTON_SOBRE = (80, 94, 122)
EVENTO_SEQUIA = (255, 200, 0)
EVENTO_CALOR = (255, 90, 20)
EVENTO_EXTINCION = (255, 60, 60)
