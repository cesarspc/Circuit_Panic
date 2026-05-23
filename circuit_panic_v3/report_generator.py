"""Generador de reporte PDF para el stealth assessment de Circuit Panic.

No usa dependencias externas: crea un PDF simple y organizado con librería estándar.
El reporte se genera al finalizar el juego desde el botón "Finalizar juego".
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean
from textwrap import wrap
from typing import Any


class SimplePDF:
    """Pequeño generador PDF suficiente para reportes de texto y tablas simples."""

    def __init__(self, title: str = "Reporte") -> None:
        self.title = title
        self.width = 612  # Letter width, points
        self.height = 792  # Letter height, points
        self.margin = 48
        self.y = self.height - self.margin
        self.pages: list[list[str]] = []
        self.current: list[str] = []
        self.add_page()

    def add_page(self) -> None:
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = self.height - self.margin
        self.set_stroke_color(0.18, 0.24, 0.30)
        self.set_fill_color(0.05, 0.07, 0.10)

    def finish_pages(self) -> None:
        if self.current:
            self.pages.append(self.current)
            self.current = []

    def ensure_space(self, needed: float) -> None:
        if self.y - needed < self.margin:
            self.add_page()

    @staticmethod
    def _escape(text: Any) -> str:
        value = str(text)
        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("\r", " ")
            .replace("\n", " ")
        )

    def set_fill_color(self, r: float, g: float, b: float) -> None:
        self.current.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_color(self, r: float, g: float, b: float) -> None:
        self.current.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def text(self, text: Any, x: float, y: float, size: int = 10, bold: bool = False) -> None:
        # Se usa Helvetica estándar. El parámetro bold queda reservado para compatibilidad visual.
        safe = self._escape(text)
        font = "/F2" if bold else "/F1"
        self.current.append(f"BT {font} {size} Tf {x:.2f} {y:.2f} Td ({safe}) Tj ET")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.current.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def rect(self, x: float, y: float, w: float, h: float, fill: bool = False) -> None:
        op = "f" if fill else "S"
        self.current.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def heading(self, text: str, size: int = 18) -> None:
        self.ensure_space(size + 20)
        self.set_fill_color(0.00, 0.55, 0.33)
        self.text(text, self.margin, self.y, size=size, bold=True)
        self.y -= size + 10
        self.set_stroke_color(0.00, 0.55, 0.33)
        self.line(self.margin, self.y, self.width - self.margin, self.y)
        self.y -= 18
        self.set_fill_color(0.10, 0.12, 0.15)

    def subheading(self, text: str) -> None:
        self.ensure_space(28)
        self.set_fill_color(0.05, 0.25, 0.19)
        self.text(text, self.margin, self.y, size=13, bold=True)
        self.y -= 22
        self.set_fill_color(0.10, 0.12, 0.15)

    def paragraph(self, text: str, size: int = 10, max_chars: int = 95, gap: int = 14) -> None:
        lines = wrap(str(text), width=max_chars) or [""]
        self.ensure_space(len(lines) * gap + 6)
        self.set_fill_color(0.10, 0.12, 0.15)
        for line in lines:
            self.text(line, self.margin, self.y, size=size)
            self.y -= gap
        self.y -= 6

    def key_value(self, key: str, value: Any, x: float, y: float, w: float) -> None:
        self.set_fill_color(0.93, 0.96, 0.94)
        self.rect(x, y - 20, w, 28, fill=True)
        self.set_stroke_color(0.80, 0.85, 0.82)
        self.rect(x, y - 20, w, 28, fill=False)
        self.set_fill_color(0.10, 0.12, 0.15)
        self.text(key, x + 8, y - 3, size=8, bold=True)
        self.text(value, x + 8, y - 15, size=9)

    def summary_cards(self, cards: list[tuple[str, Any]]) -> None:
        self.ensure_space(90)
        card_w = 158
        card_h = 40
        gap = 12
        x0 = self.margin
        y0 = self.y
        for i, (key, value) in enumerate(cards):
            col = i % 3
            row = i // 3
            x = x0 + col * (card_w + gap)
            y = y0 - row * (card_h + 10)
            self.key_value(key, value, x, y, card_w)
        rows = (len(cards) + 2) // 3
        self.y -= rows * (card_h + 10) + 8

    def table(self, headers: list[str], rows: list[list[Any]], col_widths: list[float]) -> None:
        row_h = 23
        table_w = sum(col_widths)
        x0 = self.margin

        def draw_header() -> None:
            self.set_fill_color(0.05, 0.25, 0.19)
            self.rect(x0, self.y - row_h + 5, table_w, row_h, fill=True)
            self.set_fill_color(1.0, 1.0, 1.0)
            x = x0 + 4
            for header, width in zip(headers, col_widths):
                self.text(header, x, self.y - 10, size=7, bold=True)
                x += width
            self.y -= row_h
            self.set_fill_color(0.10, 0.12, 0.15)

        self.ensure_space(row_h * 3)
        draw_header()
        for idx, row in enumerate(rows):
            if self.y - row_h < self.margin:
                self.add_page()
                draw_header()
            if idx % 2 == 0:
                self.set_fill_color(0.96, 0.98, 0.97)
                self.rect(x0, self.y - row_h + 5, table_w, row_h, fill=True)
            self.set_fill_color(0.10, 0.12, 0.15)
            x = x0 + 4
            for value, width in zip(row, col_widths):
                text_value = str(value)
                max_len = max(5, int(width / 4.7))
                if len(text_value) > max_len:
                    text_value = text_value[: max_len - 1] + "..."
                self.text(text_value, x, self.y - 10, size=7)
                x += width
            self.set_stroke_color(0.82, 0.86, 0.84)
            self.line(x0, self.y - row_h + 5, x0 + table_w, self.y - row_h + 5)
            self.y -= row_h
        self.y -= 10

    def progress_bar(self, label: str, value: float) -> None:
        self.ensure_space(42)
        value = max(0.0, min(1.0, float(value)))
        x = self.margin
        w = 260
        h = 14
        self.set_fill_color(0.10, 0.12, 0.15)
        self.text(label, x, self.y, size=10, bold=True)
        self.text(f"{value:.3f} / 1.000", x + w + 18, self.y, size=10)
        self.y -= 20
        self.set_stroke_color(0.75, 0.80, 0.78)
        self.rect(x, self.y, w, h, fill=False)
        self.set_fill_color(0.00, 0.55, 0.33)
        self.rect(x + 2, self.y + 2, max(0, (w - 4) * value), h - 4, fill=True)
        self.y -= 28

    def save(self, path: str | Path) -> Path:
        self.finish_pages()
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        objects: list[bytes] = []
        # 1 catalog, 2 pages, 3 font normal, 4 font bold, pages/content desde 5.
        page_refs: list[int] = []
        for page_idx, _content in enumerate(self.pages):
            page_obj_num = 5 + page_idx * 2
            page_refs.append(page_obj_num)

        kids = " ".join(f"{num} 0 R" for num in page_refs)
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(self.pages)} >>".encode("cp1252"))
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

        for page_idx, content_lines in enumerate(self.pages):
            page_obj_num = 5 + page_idx * 2
            content_obj_num = page_obj_num + 1
            content = "\n".join(content_lines).encode("cp1252", errors="replace")
            page_obj = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {content_obj_num} 0 R >>"
            ).encode("cp1252")
            stream_obj = b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"
            objects.append(page_obj)
            objects.append(stream_obj)

        pdf = bytearray()
        pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for idx, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")

        xref_pos = len(pdf)
        total_objects = len(objects) + 1
        pdf.extend(f"xref\n0 {total_objects}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer\n<< /Size {total_objects} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )
        output_path.write_bytes(bytes(pdf))
        return output_path


def _fmt_bool(value: Any) -> str:
    return "Sí" if bool(value) else "No"


def _fmt_num(value: Any, decimals: int = 2) -> str:
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def generate_stealth_report(
    level_results: list[dict[str, Any]],
    final_score: float,
    final_message: str,
    output_dir: str | Path = "reports",
) -> str:
    """Genera el PDF final del stealth assessment y devuelve la ruta absoluta."""
    output_dir = Path(output_dir)
    timestamp = datetime.now()
    filename = f"reporte_stealth_circuit_panic_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = output_dir / filename

    total_time = sum(float(r.get("tiempo_total_segundos", 0)) for r in level_results)
    total_errors = sum(int(r.get("intentos_incorrectos", 0)) for r in level_results)
    total_inspected = sum(int(r.get("nodos_inspeccionados", 0)) for r in level_results)
    total_backtracking = sum(int(r.get("backtracking", 0)) for r in level_results)
    avg_efficiency = _safe_mean([float(r.get("ratio_eficiencia", 0)) for r in level_results])
    avg_first_attempt = _safe_mean([float(r.get("tiempo_hasta_primer_intento", 0)) for r in level_results])

    pdf = SimplePDF(title="Reporte de Stealth Assessment")
    pdf.heading("Reporte de Stealth Assessment - Circuit Panic", size=18)
    pdf.paragraph(
        "Documento generado automáticamente al finalizar el serious game Circuit Panic. "
        "El reporte consolida las métricas silenciosas recolectadas durante la partida "
        "para apoyar el análisis académico de habilidades de resolución de problemas."
    )
    pdf.paragraph(f"Fecha y hora de generación: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    pdf.subheading("1. Resumen general")
    pdf.summary_cards(
        [
            ("Score final", _fmt_num(final_score, 3)),
            ("Niveles jugados", len(level_results)),
            ("Tiempo total", f"{_fmt_num(total_time, 2)} s"),
            ("Intentos incorrectos", total_errors),
            ("Nodos inspeccionados", total_inspected),
            ("Backtracking total", total_backtracking),
        ]
    )
    pdf.progress_bar("Barra de desempeño global", final_score)
    pdf.paragraph(f"Retroalimentación cualitativa: {final_message}")

    pdf.subheading("2. Datos recolectados por nivel")
    headers = [
        "Nivel",
        "Tiempo",
        "Errores",
        "Nodos",
        "1er acierto",
        "Eficiencia",
        "1er intento",
        "Back",
        "Score",
    ]
    rows: list[list[Any]] = []
    for result in level_results:
        rows.append(
            [
                result.get("nivel", ""),
                f"{_fmt_num(result.get('tiempo_total_segundos', 0), 2)}s",
                result.get("intentos_incorrectos", 0),
                result.get("nodos_inspeccionados", 0),
                _fmt_bool(result.get("primer_clic_correcto", False)),
                _fmt_num(result.get("ratio_eficiencia", 0), 3),
                f"{_fmt_num(result.get('tiempo_hasta_primer_intento', 0), 2)}s",
                result.get("backtracking", 0),
                _fmt_num(result.get("score_resolucion_problemas", 0), 3),
            ]
        )
    pdf.table(headers, rows, [35, 55, 50, 50, 70, 65, 70, 38, 55])

    pdf.subheading("3. Indicadores agregados")
    pdf.summary_cards(
        [
            ("Eficiencia promedio", _fmt_num(avg_efficiency, 3)),
            ("Tiempo medio 1er intento", f"{_fmt_num(avg_first_attempt, 2)} s"),
            ("Errores por nivel", _fmt_num(total_errors / len(level_results), 2) if level_results else "0.00"),
        ]
    )

    pdf.subheading("4. Criterio de cálculo")
    pdf.paragraph(
        "El score de resolución de problemas se calcula por nivel con la fórmula: "
        "score = max(0.0, 1.0 - errores*0.15 - backtracking*0.05 - "
        "tiempo_total/120*0.3 + primer_clic_correcto*0.2). Luego se limita a máximo 1.0."
    )
    pdf.paragraph(
        "Interpretación general: valores cercanos a 1.0 indican mayor precisión, menor número "
        "de intentos incorrectos, menor retroceso y mejor administración del tiempo antes de decidir."
    )

    pdf.subheading("5. Datos crudos")
    for result in level_results:
        pdf.paragraph(f"Nivel {result.get('nivel', '')}: {result}", size=8, max_chars=112, gap=11)

    saved_path = pdf.save(output_path)
    return str(saved_path.resolve())
