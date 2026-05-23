"""Constantes visuales y de configuración para Circuit Panic."""

WIDTH = 900
HEIGHT = 700
FPS = 60
TIME_LIMIT_SECONDS = 120

# Paleta dark / hacker
BACKGROUND = (13, 17, 23)
PANEL_BG = (18, 24, 33)
PANEL_BORDER = (46, 61, 77)
NEON_GREEN = (0, 255, 136)
NEON_RED = (255, 68, 85)
CABLE = (51, 68, 85)
CABLE_DIM = (32, 43, 55)
TEXT = (226, 232, 240)
TEXT_MUTED = (148, 163, 184)
YELLOW = (255, 209, 102)
BLUE = (88, 166, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Tablero: ajustado para que no se monte sobre el panel derecho ni el encabezado.
BOARD_LEFT = 80
BOARD_TOP = 170
BOARD_WIDTH = 500
BOARD_HEIGHT = 360
NODE_RADIUS = 17
NODE_HIT_RADIUS = 24

# Panel lateral: separado del tablero.
SIDE_PANEL_X = 655
SIDE_PANEL_Y = 125
SIDE_PANEL_W = 215
SIDE_PANEL_H = 440

# Botones
START_BUTTON_RECT = (350, 405, 200, 56)
REPAIR_BUTTON_RECT = (675, 470, 175, 44)
CONTINUE_BUTTON_RECT = (350, 530, 200, 56)
RESTART_BUTTON_RECT = (220, 585, 200, 52)
FINISH_BUTTON_RECT = (470, 585, 300, 52)

# Tipografías del sistema. No requiere archivos externos.
FONT_MAIN = "consolas"
FONT_FALLBACK = "couriernew"
