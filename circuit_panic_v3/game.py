"""Lógica principal del serious game Circuit Panic."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time

import pygame

from constants import (
    BOARD_HEIGHT,
    BOARD_LEFT,
    BOARD_TOP,
    BOARD_WIDTH,
    CONTINUE_BUTTON_RECT,
    FINISH_BUTTON_RECT,
    NODE_HIT_RADIUS,
    REPAIR_BUTTON_RECT,
    RESTART_BUTTON_RECT,
    START_BUTTON_RECT,
    TIME_LIMIT_SECONDS,
    UPSKILLS_LAUNCH_BUTTON_RECT,
)
from stealth import StealthAssessment
from report_generator import generate_stealth_report


STATE_UPSKILLS_INTRO = "upskills_intro"
STATE_START = "start"
STATE_PLAYING = "playing"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_RESULTS = "results"


@dataclass
class Node:
    row: int
    col: int
    x: int
    y: int
    failed: bool = False
    inspected: bool = False
    selected: bool = False
    clue: str = ""

    @property
    def id(self) -> str:
        return f"{self.row},{self.col}"


@dataclass
class LevelConfig:
    number: int
    title: str
    rows: int
    cols: int
    root: tuple[int, int]
    failed_nodes: set[tuple[int, int]]
    ambiguity: int
    routes_enabled: bool = False
    source: tuple[int, int] = (0, 0)
    sink: tuple[int, int] = (4, 4)
    description: str = ""


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    radius: float = 4.0


class CircuitPanicGame:
    """Controla estados, niveles, nodos, intentos de reparación y resultados."""

    def __init__(self) -> None:
        self.state = STATE_UPSKILLS_INTRO
        self.levels = self._build_levels()
        self.level_index = 0
        self.config: LevelConfig | None = None
        self.nodes: dict[str, Node] = {}
        self.edges: list[tuple[str, str]] = []
        self.selected_node_id: str | None = None
        self.feedback = ""
        self.feedback_kind = "info"
        self.stealth: StealthAssessment | None = None
        self.level_results: list[dict] = []
        self.last_level_result: dict | None = None
        self.level_started_at = 0.0
        self.level_end_reason = ""
        self.particles: list[Particle] = []
        self.success_started_at = 0.0
        self.final_score = 0.0
        self.final_message = ""
        self._printed_results = False
        self.report_path: str | None = None
        self.should_exit = False

    def _build_levels(self) -> list[LevelConfig]:
        return [
            LevelConfig(
                number=1,
                title="Diagnóstico inicial",
                rows=5,
                cols=5,
                root=(2, 1),  # placeholder; randomized on load
                failed_nodes={(2, 1), (2, 2), (2, 3), (2, 4)},
                ambiguity=1,
                routes_enabled=False,
                description="Una ruta principal presenta una interrupción clara.",
            ),
            LevelConfig(
                number=2,
                title="Rutas paralelas",
                rows=5,
                cols=5,
                root=(1, 2),  # placeholder; randomized on load
                failed_nodes={(1, 2), (1, 3), (1, 4), (2, 2), (3, 2), (4, 2)},
                ambiguity=2,
                routes_enabled=True,
                description="La falla se propaga por ramificaciones verticales y horizontales.",
            ),
            LevelConfig(
                number=3,
                title="Señal ambigua",
                rows=5,
                cols=5,
                root=(3, 1),  # placeholder; randomized on load
                failed_nodes={(3, 1), (3, 2), (3, 3), (4, 1), (4, 2), (2, 1), (2, 2)},
                ambiguity=3,
                routes_enabled=True,
                description="Varias rutas parecen dañadas; se requiere deducción más cuidadosa.",
            ),
        ]

    def start_game(self) -> None:
        self.level_results = []
        self.last_level_result = None
        self.final_score = 0.0
        self.final_message = ""
        self._printed_results = False
        self.report_path = None
        self.should_exit = False
        self.load_level(0)

    def load_level(self, index: int) -> None:
        self.level_index = index
        self.config = self.levels[index]
        # Randomize the failure origin among all red (failed) nodes each load
        self.config.root = random.choice(sorted(self.config.failed_nodes))
        self.nodes = {}
        self.edges = []
        self.selected_node_id = None
        self.feedback = "Inspecciona nodos, deduce el origen y usa REPARAR. También puedes reparar con clic derecho."
        self.feedback_kind = "info"
        self.last_level_result = None
        self.level_end_reason = ""
        self.particles.clear()
        self.success_started_at = 0.0
        self._create_board()
        self.stealth = StealthAssessment(total_nodos=len(self.nodes), nivel=self.config.number)
        self.stealth.start()
        self.level_started_at = time.perf_counter()
        self.state = STATE_PLAYING

    def _create_board(self) -> None:
        assert self.config is not None
        rows, cols = self.config.rows, self.config.cols
        x_step = BOARD_WIDTH / (cols - 1)
        y_step = BOARD_HEIGHT / (rows - 1)

        for r in range(rows):
            for c in range(cols):
                node = Node(
                    row=r,
                    col=c,
                    x=int(BOARD_LEFT + c * x_step),
                    y=int(BOARD_TOP + r * y_step),
                    failed=(r, c) in self.config.failed_nodes,
                )
                node.clue = self._build_clue(node)
                self.nodes[node.id] = node

        for r in range(rows):
            for c in range(cols):
                current = f"{r},{c}"
                if c + 1 < cols:
                    self.edges.append((current, f"{r},{c + 1}"))
                if r + 1 < rows:
                    self.edges.append((current, f"{r + 1},{c}"))
                if self.config.routes_enabled and r + 1 < rows and c + 1 < cols and (r + c) % 2 == 0:
                    self.edges.append((current, f"{r + 1},{c + 1}"))

    def _build_clue(self, node: Node) -> str:
        assert self.config is not None
        root_id = f"{self.config.root[0]},{self.config.root[1]}"
        is_root = node.id == root_id
        dist_to_root = abs(node.row - self.config.root[0]) + abs(node.col - self.config.root[1])

        if self.config.ambiguity == 1:
            if is_root:
                return "Volt: 0.0V | Amp: 2.45A | Temp: 84°C"
            if node.failed:
                return "Volt: 0.0V | Amp: 0.00A | Temp: 22°C"
            if dist_to_root <= 1:
                return "Volt: 5.0V | Amp: 0.08A | Temp: 31°C"
            return "Volt: 5.0V | Amp: 0.08A | Temp: 23°C"

        if self.config.ambiguity == 2:
            if is_root:
                return "V_out: 1.2V | Tasa de error: 1.5e-1 | Temp: 76°C"
            if node.failed and dist_to_root == 1:
                return "Volt: 0.3V | Tasa de error: 1.0e-0 | Temp: 26°C"
            if node.failed:
                return "Volt: 0.0V | Tasa de error: 1.0e-0 | Temp: 21°C"
            if dist_to_root <= 2:
                return "Volt: 4.8V | Tasa de error: 1.0e-7 | Temp: 28°C"
            return "Volt: 5.0V | Tasa de error: 0.0 | Temp: 22°C"

        if is_root:
            return "Volt: 0.0V | Sonido/señal: 12dB | Temp: 29°C"
        if node.failed and dist_to_root == 1:
            return "Volt: 0.0V | Sonido/señal: 3dB | Temp: 29°C"
        if node.failed:
            return "Volt: 0.0V | Sonido/señal: 0dB | Temp: 20°C"
        if dist_to_root <= 2:
            return "Volt: 5.0V | Sonido: 32dB | Temp: 25°C"
        return "Volt: 5.0V | Sonido: 45dB | Temp: 22°C"

    def update(self, dt: float) -> None:
        self._update_particles(dt)
        if self.state == STATE_PLAYING and self.stealth is not None:
            if self.time_left <= 0:
                self._finish_level(correct=False, reason="Tiempo agotado")

    @property
    def elapsed_level_time(self) -> float:
        if self.stealth is None:
            return 0.0
        return max(0.0, time.perf_counter() - self.level_started_at)

    @property
    def time_left(self) -> float:
        return max(0.0, TIME_LIMIT_SECONDS - self.elapsed_level_time)

    def handle_mouse_down(self, pos: tuple[int, int], button: int) -> None:
        if self.state == STATE_UPSKILLS_INTRO:
            if pygame.Rect(UPSKILLS_LAUNCH_BUTTON_RECT).collidepoint(pos):
                self.state = STATE_START
            return

        if self.state == STATE_START:
            if pygame.Rect(START_BUTTON_RECT).collidepoint(pos):
                self.start_game()
            return

        if self.state == STATE_PLAYING:
            if pygame.Rect(REPAIR_BUTTON_RECT).collidepoint(pos):
                if self.selected_node_id:
                    self.attempt_repair(self.selected_node_id)
                else:
                    self.feedback = "Selecciona primero un nodo para intentar la reparación."
                    self.feedback_kind = "warn"
                return

            node = self.get_node_at_pos(pos)
            if node is None:
                return

            if button == 3:
                self.selected_node_id = node.id
                self._select_node(node.id)
                self.attempt_repair(node.id)
            else:
                self.inspect_node(node.id)
            return

        if self.state == STATE_LEVEL_COMPLETE:
            if pygame.Rect(CONTINUE_BUTTON_RECT).collidepoint(pos):
                if self.level_index + 1 < len(self.levels):
                    self.load_level(self.level_index + 1)
                else:
                    self.show_results()
            return

        if self.state == STATE_RESULTS:
            if pygame.Rect(RESTART_BUTTON_RECT).collidepoint(pos):
                self.start_game()
                return
            if pygame.Rect(FINISH_BUTTON_RECT).collidepoint(pos):
                self.finalize_game()
                return

    def handle_key_down(self, key: int) -> None:
        if self.state == STATE_UPSKILLS_INTRO and key in (pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_START
            return
        if self.state == STATE_PLAYING and key == pygame.K_r and self.selected_node_id:
            self.attempt_repair(self.selected_node_id)
        elif self.state == STATE_LEVEL_COMPLETE and key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.level_index + 1 < len(self.levels):
                self.load_level(self.level_index + 1)
            else:
                self.show_results()
        elif self.state == STATE_RESULTS and key == pygame.K_RETURN:
            self.start_game()
        elif self.state == STATE_RESULTS and key == pygame.K_f:
            self.finalize_game()

    def get_node_at_pos(self, pos: tuple[int, int]) -> Node | None:
        px, py = pos
        for node in self.nodes.values():
            if math.hypot(px - node.x, py - node.y) <= NODE_HIT_RADIUS:
                return node
        return None

    def inspect_node(self, node_id: str) -> None:
        node = self.nodes[node_id]
        self._select_node(node_id)
        node.inspected = True
        self.selected_node_id = node_id
        if self.stealth:
            self.stealth.inspect_node(node_id)
        self.feedback = node.clue
        self.feedback_kind = "info"

    def _select_node(self, node_id: str) -> None:
        for n in self.nodes.values():
            n.selected = False
        self.nodes[node_id].selected = True

    def attempt_repair(self, node_id: str) -> None:
        assert self.config is not None
        correct = node_id == f"{self.config.root[0]},{self.config.root[1]}"
        if self.stealth:
            self.stealth.record_attempt(node_id, correct)

        if correct:
            self.feedback = "Reparación correcta: el flujo de energía fue restaurado."
            self.feedback_kind = "success"
            self._finish_level(correct=True, reason="Reparación correcta")
        else:
            node = self.nodes[node_id]
            self.feedback = "Reparación incorrecta: el fallo persiste. Revisa la lógica de propagación."
            self.feedback_kind = "error"
            self._spawn_error_particles(node.x, node.y)

    def _finish_level(self, correct: bool, reason: str) -> None:
        if self.state != STATE_PLAYING:
            return
        self.level_end_reason = reason
        for node in self.nodes.values():
            node.failed = False if correct else node.failed
        if self.stealth:
            self.last_level_result = self.stealth.finish()
            if not correct and reason == "Tiempo agotado":
                self.last_level_result["intentos_incorrectos"] += 1
                self.last_level_result["score_resolucion_problemas"] = max(
                    0.0,
                    round(self.last_level_result["score_resolucion_problemas"] - 0.15, 3),
                )
            self.level_results.append(self.last_level_result)
        self.success_started_at = time.perf_counter()
        self.state = STATE_LEVEL_COMPLETE

    def show_results(self) -> None:
        if not self.level_results:
            self.final_score = 0.0
        else:
            self.final_score = sum(r["score_resolucion_problemas"] for r in self.level_results) / len(self.level_results)
        self.final_score = round(self.final_score, 3)
        self.final_message = self._qualitative_feedback(self.final_score)
        self.state = STATE_RESULTS
        if not self._printed_results:
            print("\n========== STEALTH DATA COMPLETO ==========")
            for result in self.level_results:
                print(result)
            print({"score_final_promedio": self.final_score, "mensaje": self.final_message})
            print("==========================================\n")
            self._printed_results = True

    def finalize_game(self) -> None:
        """Genera el reporte PDF final y marca el juego para cerrarse."""
        if not self.level_results:
            print("No hay datos de stealth assessment para generar el reporte.")
            self.should_exit = True
            return

        if not self.report_path:
            self.report_path = generate_stealth_report(
                level_results=self.level_results,
                final_score=self.final_score,
                final_message=self.final_message,
            )
            print(f"Reporte PDF generado correctamente: {self.report_path}")

        self.should_exit = True

    def _qualitative_feedback(self, score: float) -> str:
        if score >= 0.85:
            return "Abordas los problemas de forma sistemática, precisa y eficiente."
        if score >= 0.65:
            return "Tienes buen razonamiento diagnóstico; puedes mejorar reduciendo intentos impulsivos."
        if score >= 0.45:
            return "Muestras avances, pero conviene inspeccionar con más estrategia antes de decidir."
        return "Necesitas fortalecer el análisis de causa raíz y evitar reparar sin suficiente evidencia."

    def _spawn_error_particles(self, x: float, y: float) -> None:
        for _ in range(28):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 220)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(0.35, 0.75),
                    max_life=0.75,
                    radius=random.uniform(2.0, 4.5),
                )
            )

    def _update_particles(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy += 80 * dt
                alive.append(p)
        self.particles = alive

    def root_id(self) -> str:
        assert self.config is not None
        return f"{self.config.root[0]},{self.config.root[1]}"

    def current_level_number(self) -> int:
        return self.config.number if self.config else 0

    def selected_node(self) -> Node | None:
        if self.selected_node_id and self.selected_node_id in self.nodes:
            return self.nodes[self.selected_node_id]
        return None
