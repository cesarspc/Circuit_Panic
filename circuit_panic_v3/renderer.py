"""Renderer de Circuit Panic."""
from __future__ import annotations

import math
import random

import pygame

from constants import (
    BACKGROUND,
    BLACK,
    BLUE,
    BOARD_HEIGHT,
    BOARD_LEFT,
    BOARD_TOP,
    BOARD_WIDTH,
    CABLE,
    CABLE_DIM,
    CONTINUE_BUTTON_RECT,
    FINISH_BUTTON_RECT,
    FONT_FALLBACK,
    FONT_MAIN,
    HEIGHT,
    NEON_GREEN,
    NEON_RED,
    NODE_RADIUS,
    PANEL_BG,
    PANEL_BORDER,
    REPAIR_BUTTON_RECT,
    RESTART_BUTTON_RECT,
    SIDE_PANEL_H,
    SIDE_PANEL_W,
    SIDE_PANEL_X,
    SIDE_PANEL_Y,
    START_BUTTON_RECT,
    TEXT,
    TEXT_MUTED,
    WHITE,
    WIDTH,
    YELLOW,
)
from game import STATE_LEVEL_COMPLETE, STATE_PLAYING, STATE_RESULTS, STATE_START, CircuitPanicGame


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = self._font(54, bold=True)
        self.font_h1 = self._font(34, bold=True)
        self.font_h2 = self._font(24, bold=True)
        self.font_body = self._font(18)
        self.font_small = self._font(14)
        self.font_button = self._font(19, bold=True)
        self.data_points = [
            [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(18, 55)]
            for _ in range(75)
        ]

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        font = pygame.font.SysFont(FONT_MAIN, size, bold=bold)
        if font is None:
            font = pygame.font.SysFont(FONT_FALLBACK, size, bold=bold)
        return font

    def draw(self, game: CircuitPanicGame, dt: float) -> None:
        self.draw_background(dt)
        if game.state == STATE_START:
            self.draw_start_screen()
        elif game.state == STATE_PLAYING:
            self.draw_game_screen(game)
        elif game.state == STATE_LEVEL_COMPLETE:
            self.draw_level_complete(game)
        elif game.state == STATE_RESULTS:
            self.draw_results(game)

    def draw_background(self, dt: float) -> None:
        self.screen.fill(BACKGROUND)
        for x in range(0, WIDTH, 45):
            pygame.draw.line(self.screen, (18, 28, 38), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 45):
            pygame.draw.line(self.screen, (18, 28, 38), (0, y), (WIDTH, y), 1)

        for point in self.data_points:
            point[1] += point[2] * dt
            if point[1] > HEIGHT:
                point[0] = random.randint(0, WIDTH)
                point[1] = -8
                point[2] = random.uniform(18, 55)
            alpha_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(alpha_surface, (*NEON_GREEN, 70), (4, 4), 2)
            self.screen.blit(alpha_surface, (point[0], point[1]))

    def draw_start_screen(self) -> None:
        self._draw_centered_text("CIRCUIT PANIC", self.font_title, NEON_GREEN, 160)
        self._draw_centered_text("Bienvenido al juego", self.font_h2, TEXT, 230)

        descripcion = (
            "Analiza el circuito, identifica los nodos problemáticos y repara el sistema antes de que se acabe el tiempo. "
        )
        y = 300
        for line in self._wrap_text(descripcion, self.font_body, 760):
            self._draw_centered_text(line, self.font_body, TEXT_MUTED, y)
            y += 28

        self._draw_button(pygame.Rect(START_BUTTON_RECT), "Iniciar", NEON_GREEN)
        self._draw_centered_text("Python + pygame | Stealth assessment", self.font_small, TEXT_MUTED, 500)

    def draw_game_screen(self, game: CircuitPanicGame) -> None:
        assert game.config is not None
        self._draw_header(game)
        self._draw_board_frame()
        self._draw_edges(game, success=False)
        self._draw_nodes(game)
        self._draw_particles(game)
        self._draw_side_panel(game)

    def draw_level_complete(self, game: CircuitPanicGame) -> None:
        assert game.config is not None
        self._draw_header(game)
        self._draw_board_frame()
        self._draw_edges(game, success=True)
        self._draw_nodes(game, force_green=True)
        self._draw_particles(game)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(210, 180, 480, 360)
        self._draw_panel(card)
        self._draw_centered_text(f"Nivel {game.current_level_number()} completado", self.font_h1, NEON_GREEN, 220)
        reason = game.level_end_reason or "Circuito restaurado"
        self._draw_centered_text(reason, self.font_body, TEXT, 270)

        if game.last_level_result:
            score = game.last_level_result["score_resolucion_problemas"]
            self._draw_centered_text(f"Score del nivel: {score:.2f}", self.font_h2, TEXT, 325)
            self._draw_progress_bar(pygame.Rect(300, 365, 300, 24), score)

        label = "Siguiente" if game.level_index + 1 < len(game.levels) else "Ver resultados"
        self._draw_button(pygame.Rect(CONTINUE_BUTTON_RECT), label, NEON_GREEN)
        self._draw_centered_text("Enter o espacio para continuar", self.font_small, TEXT_MUTED, 610)

    def draw_results(self, game: CircuitPanicGame) -> None:
        self._draw_centered_text("Tu perfil de resolución de problemas", self.font_h1, NEON_GREEN, 115)
        score = game.final_score
        self._draw_centered_text(f"Score final: {score:.2f}", self.font_h2, TEXT, 180)
        self._draw_progress_bar(pygame.Rect(250, 225, 400, 32), score)

        wrapped = self._wrap_text(game.final_message, self.font_body, 620)
        y = 305
        for line in wrapped:
            self._draw_centered_text(line, self.font_body, TEXT, y)
            y += 28

        note = "Al finalizar, se generará un PDF con los datos completos del stealth assessment."
        for line in self._wrap_text(note, self.font_small, 650):
            self._draw_centered_text(line, self.font_small, TEXT_MUTED, y + 24)
            y += 20

        y += 45
        if game.level_results:
            self._draw_centered_text("Resumen visual por nivel", self.font_h2, TEXT, y)
            y += 38
            for result in game.level_results:
                label = f"Nivel {result['nivel']}"
                self._draw_text(label, self.font_body, TEXT_MUTED, 305, y)
                self._draw_progress_bar(pygame.Rect(395, y + 1, 200, 18), result["score_resolucion_problemas"])
                y += 30

        self._draw_button(pygame.Rect(RESTART_BUTTON_RECT), "Reiniciar", NEON_GREEN)
        self._draw_button(pygame.Rect(FINISH_BUTTON_RECT), "Finalizar y generar PDF", NEON_RED)
        self._draw_centered_text("También puedes presionar F para finalizar.", self.font_small, TEXT_MUTED, 660)

    def _draw_header(self, game: CircuitPanicGame) -> None:
        assert game.config is not None
        title = f"Nivel {game.config.number}: {game.config.title}"
        self._draw_text(title, self.font_h2, NEON_GREEN, 70, 30)

        # Se envuelve la descripción para que no se meta debajo del cronómetro ni del recuadro.
        y = 66
        for line in self._wrap_text(game.config.description, self.font_small, 560):
            self._draw_text(line, self.font_small, TEXT_MUTED, 70, y)
            y += 18

        time_left = game.time_left
        color = NEON_RED if time_left <= 20 else TEXT
        timer_text = f"Tiempo: {int(time_left):03d}s"
        self._draw_text(timer_text, self.font_h2, color, 690, 30)
        self._draw_text("Click: inspeccionar | Clic derecho o R: reparar", self.font_small, TEXT_MUTED, 70, 92)

    def _draw_board_frame(self) -> None:
        frame = pygame.Rect(BOARD_LEFT - 45, BOARD_TOP - 55, BOARD_WIDTH + 90, BOARD_HEIGHT + 110)
        self._draw_panel(frame)
        self._draw_text("Mapa de circuito", self.font_small, TEXT_MUTED, frame.x + 18, frame.y + 14)

    def _draw_edges(self, game: CircuitPanicGame, success: bool) -> None:
        ticks = pygame.time.get_ticks()
        for i, (a, b) in enumerate(game.edges):
            n1 = game.nodes[a]
            n2 = game.nodes[b]
            base_color = CABLE_DIM if (n1.failed or n2.failed) and not success else CABLE
            pygame.draw.line(self.screen, base_color, (n1.x, n1.y), (n2.x, n2.y), 3)

            if success:
                phase = ((ticks / 900.0) + i * 0.08) % 1.0
                seg_len = 0.32
                start_t = max(0.0, phase - seg_len / 2)
                end_t = min(1.0, phase + seg_len / 2)
                sx = n1.x + (n2.x - n1.x) * start_t
                sy = n1.y + (n2.y - n1.y) * start_t
                ex = n1.x + (n2.x - n1.x) * end_t
                ey = n1.y + (n2.y - n1.y) * end_t
                pygame.draw.line(self.screen, NEON_GREEN, (sx, sy), (ex, ey), 5)

    def _draw_nodes(self, game: CircuitPanicGame, force_green: bool = False) -> None:
        ticks = pygame.time.get_ticks()
        for node in game.nodes.values():
            pulse = 0.5 + 0.5 * math.sin(ticks / 210 + node.row * 0.7 + node.col * 0.5)
            radius = NODE_RADIUS
            color = NEON_GREEN

            if not force_green:
                if node.failed:
                    radius = int(NODE_RADIUS + pulse * 5)
                    color = NEON_RED
                elif node.inspected:
                    color = BLUE
                else:
                    color = (75, 95, 110)

            if node.failed and not force_green:
                glow = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*NEON_RED, int(55 + pulse * 70)), (35, 35), radius + 10)
                self.screen.blit(glow, (node.x - 35, node.y - 35))

            pygame.draw.circle(self.screen, color, (node.x, node.y), radius)
            pygame.draw.circle(self.screen, BLACK, (node.x, node.y), radius, 2)

            if node.selected:
                pygame.draw.circle(self.screen, YELLOW, (node.x, node.y), radius + 7, 3)
            elif node.inspected:
                pygame.draw.circle(self.screen, BLUE, (node.x, node.y), radius + 4, 2)

            label = f"{node.row + 1}{node.col + 1}"
            self._draw_centered_on(label, self.font_small, BLACK, node.x, node.y - 7)

    def _draw_side_panel(self, game: CircuitPanicGame) -> None:
        panel = pygame.Rect(SIDE_PANEL_X, SIDE_PANEL_Y, SIDE_PANEL_W, SIDE_PANEL_H)
        self._draw_panel(panel)
        self._draw_text("Diagnóstico", self.font_h2, TEXT, panel.x + 18, panel.y + 16)
        self._draw_text("Pista:", self.font_small, TEXT_MUTED, panel.x + 18, panel.y + 62)

        clue = game.feedback or "Selecciona un nodo para inspeccionar."
        color = TEXT
        if game.feedback_kind == "error":
            color = NEON_RED
        elif game.feedback_kind == "success":
            color = NEON_GREEN
        elif game.feedback_kind == "warn":
            color = YELLOW

        y = panel.y + 95
        for line in self._wrap_text(clue, self.font_body, panel.width - 36):
            self._draw_text(line, self.font_body, color, panel.x + 18, y)
            y += 25

        selected = game.selected_node()
        y = min(y + 22, panel.y + 312)
        if selected:
            self._draw_text(f"Nodo: {selected.row + 1}-{selected.col + 1}", self.font_body, TEXT, panel.x + 18, y)
        else:
            self._draw_text("Nodo: ninguno", self.font_body, TEXT_MUTED, panel.x + 18, y)

        self._draw_button(pygame.Rect(REPAIR_BUTTON_RECT), "REPARAR", NEON_RED if selected else PANEL_BORDER)
    

    def _draw_particles(self, game: CircuitPanicGame) -> None:
        for p in game.particles:
            alpha = int(255 * max(0, p.life / p.max_life))
            surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*NEON_RED, alpha), (8, 8), int(p.radius))
            self.screen.blit(surf, (p.x - 8, p.y - 8))

    def _draw_panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, 2, border_radius=16)

    def _draw_button(self, rect: pygame.Rect, label: str, color: tuple[int, int, int]) -> None:
        enabled = color != PANEL_BORDER
        fill = (20, 30, 38) if enabled else (35, 42, 48)
        pygame.draw.rect(self.screen, fill, rect, border_radius=12)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=12)
        self._draw_centered_on(label, self.font_button, color if enabled else TEXT_MUTED, rect.centerx, rect.centery)

    def _draw_progress_bar(self, rect: pygame.Rect, value: float) -> None:
        value = max(0.0, min(1.0, value))
        pygame.draw.rect(self.screen, (29, 39, 50), rect, border_radius=12)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, 2, border_radius=12)
        inner = rect.inflate(-4, -4)
        fill = pygame.Rect(inner.x, inner.y, int(inner.width * value), inner.height)
        if fill.width > 0:
            pygame.draw.rect(self.screen, NEON_GREEN, fill, border_radius=10)
        percent = f"{int(value * 100)}%"
        self._draw_centered_on(percent, self.font_small, WHITE, rect.centerx, rect.centery - 8)

    def _draw_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], x: int, y: int) -> None:
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def _draw_centered_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], y: int) -> None:
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(surface, rect)

    def _draw_centered_on(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], x: int, y: int) -> None:
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(x, y))
        self.screen.blit(surface, rect)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = word if not current else f"{current} {word}"
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
