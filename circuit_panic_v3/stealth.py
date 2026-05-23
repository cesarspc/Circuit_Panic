"""Módulo de stealth assessment para Circuit Panic."""
from __future__ import annotations

import time
from typing import Any


class StealthAssessment:
    """Registra métricas silenciosas de resolución de problemas por nivel."""

    def __init__(self, total_nodos: int, nivel: int) -> None:
        self.total_nodos = total_nodos
        self.nivel = nivel
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.inspected_nodes: set[str] = set()
        self.backtracking = 0
        self.intentos_incorrectos = 0
        self.first_attempt_time: float | None = None
        self.first_click_correct: bool | None = None

    def start(self) -> None:
        self.start_time = time.perf_counter()
        self.end_time = None
        self.inspected_nodes.clear()
        self.backtracking = 0
        self.intentos_incorrectos = 0
        self.first_attempt_time = None
        self.first_click_correct = None

    def _elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        stop = self.end_time if self.end_time is not None else time.perf_counter()
        return max(0.0, stop - self.start_time)

    def inspect_node(self, node_id: str) -> None:
        if node_id in self.inspected_nodes:
            self.backtracking += 1
        else:
            self.inspected_nodes.add(node_id)

    def record_attempt(self, node_id: str, correct: bool) -> None:
        # Aquí ocurre la medición silenciosa del primer intento y los errores.
        if self.first_attempt_time is None:
            self.first_attempt_time = self._elapsed()
            self.first_click_correct = bool(correct)
        if not correct:
            self.intentos_incorrectos += 1

    def finish(self) -> dict[str, Any]:
        self.end_time = time.perf_counter()
        tiempo_total = self._elapsed()
        nodos_inspeccionados = len(self.inspected_nodes)
        ratio_eficiencia = nodos_inspeccionados / self.total_nodos if self.total_nodos else 0.0
        primer_clic_correcto = bool(self.first_click_correct) if self.first_click_correct is not None else False
        tiempo_hasta_primer_intento = (
            self.first_attempt_time if self.first_attempt_time is not None else tiempo_total
        )

        score = max(
            0.0,
            1.0
            - (self.intentos_incorrectos * 0.15)
            - (self.backtracking * 0.05)
            - (tiempo_total / 120 * 0.3)
            + (primer_clic_correcto * 0.2),
        )
        score = min(1.0, score)

        return {
            "nivel": self.nivel,
            "tiempo_total_segundos": round(tiempo_total, 2),
            "intentos_incorrectos": int(self.intentos_incorrectos),
            "nodos_inspeccionados": int(nodos_inspeccionados),
            "primer_clic_correcto": primer_clic_correcto,
            "ratio_eficiencia": round(ratio_eficiencia, 3),
            "tiempo_hasta_primer_intento": round(tiempo_hasta_primer_intento, 2),
            "backtracking": int(self.backtracking),
            "score_resolucion_problemas": round(score, 3),
        }
