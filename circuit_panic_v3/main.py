"""Entry point de Circuit Panic.

Ejecución:
    python main.py

Controles adicionales:
    F11 -> alternar pantalla completa
    Botón maximizar de Windows -> agrandar ventana
"""
from __future__ import annotations

import sys

import pygame

from constants import BACKGROUND, FPS, HEIGHT, WIDTH
from game import CircuitPanicGame
from renderer import Renderer


def get_viewport(window_size: tuple[int, int]) -> tuple[float, int, int, int, int]:
    """Escala el juego base de 900x700 manteniendo la proporción."""
    window_w, window_h = window_size
    scale = min(window_w / WIDTH, window_h / HEIGHT)
    render_w = int(WIDTH * scale)
    render_h = int(HEIGHT * scale)
    offset_x = (window_w - render_w) // 2
    offset_y = (window_h - render_h) // 2
    return scale, offset_x, offset_y, render_w, render_h


def screen_to_game_position(
    mouse_pos: tuple[int, int],
    viewport: tuple[float, int, int, int, int],
) -> tuple[int, int] | None:
    """Convierte clicks de una ventana escalada a coordenadas internas del juego."""
    scale, offset_x, offset_y, render_w, render_h = viewport
    mouse_x, mouse_y = mouse_pos

    if not (offset_x <= mouse_x <= offset_x + render_w):
        return None
    if not (offset_y <= mouse_y <= offset_y + render_h):
        return None

    game_x = int((mouse_x - offset_x) / scale)
    game_y = int((mouse_y - offset_y) / scale)
    return game_x, game_y


def create_window(fullscreen: bool = False) -> pygame.Surface:
    if fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Circuit Panic - Serious Game")

    fullscreen = False
    window = create_window(fullscreen)
    game_surface = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    game = CircuitPanicGame()
    renderer = Renderer(game_surface)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        viewport = get_viewport(window.get_size())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    window = create_window(fullscreen)
                else:
                    game.handle_key_down(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                logical_pos = screen_to_game_position(event.pos, viewport)
                if logical_pos is not None:
                    game.handle_mouse_down(logical_pos, event.button)

        if game.should_exit:
            running = False
            continue

        game.update(dt)
        renderer.draw(game, dt)

        scale, offset_x, offset_y, render_w, render_h = get_viewport(window.get_size())
        window.fill(BACKGROUND)
        scaled_surface = pygame.transform.smoothscale(game_surface, (render_w, render_h))
        window.blit(scaled_surface, (offset_x, offset_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
