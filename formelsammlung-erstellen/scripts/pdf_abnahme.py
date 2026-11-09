#!/usr/bin/env python3
"""Prüft PDF-Metadaten und LaTeX-Log und rendert Seiten für Sichtprüfung."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


POINTS_PER_MM = 72.0 / 25.4
PAGE_SIZES_MM = {
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "LETTER": (215.9, 279.4),
}
FATAL_LOG_PATTERNS = {
    "latex_error": re.compile(r"LaTeX Error", re.IGNORECASE),
    "emergency_stop": re.compile(r"Emergency stop", re.IGNORECASE),
    "fatal_error": re.compile(r"Fatal error", re.IGNORECASE),
    "undefined_control_sequence": re.compile(r"Undefined control sequence", re.IGNORECASE),
    "missing_glyph": re.compile(r"Missing character", re.IGNORECASE),
}
REVIEW_LOG_PATTERNS = {
    "overfull": re.compile(r"Overfull \\[hv]box", re.IGNORECASE),
    "underfull": re.compile(r"Underfull \\[hv]box", re.IGNORECASE),
    "undefined_references": re.compile(r"undefined references", re.IGNORECASE),
}


def page_dimensions_mm(page: Any) -> tuple[float, float]:
    width = float(page.mediabox.width) / POINTS_PER_MM
    height = float(page.mediabox.height) / POINTS_PER_MM
    rotation = int(page.get("/Rotate", 0) or 0) % 360
    if rotation in {90, 270}:
        width, height = height, width
    return width, height


def size_matches(width: float, height: float, expected: tuple[float, float], tolerance: float) -> bool:
    actual_sorted = sorted((width, height))
    expected_sorted = sorted(expected)
    return all(abs(actual - target) <= tolerance for actual, target in zip(actual_sorted, expected_sorted))


def scan_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fatal = {name: len(pattern.findall(text)) for name, pattern in FATAL_LOG_PATTERNS.items()}
    review = {name: len(pattern.findall(text)) for name, pattern in REVIEW_LOG_PATTERNS.items()}
    return {"path": str(path), "fatal": fatal, "review": review}


def render_pdf(pdf: Path, render_dir: Path, dpi: int, grayscale: bool) -> list[str]:
    executable = shutil.which("pdftoppm")
    if executable is None:
        raise RuntimeError("pdftoppm wurde nicht gefunden")
    render_dir.mkdir(parents=True, exist_ok=True)
    prefix = render_dir / "page"
    command = [executable, "-png", "-r", str(dpi)]
    if grayscale:
        command.append("-gray")
    command.extend([str(pdf), str(prefix)])
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return [str(path) for path in sorted(render_dir.glob("page-*.png"))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Zu prüfende PDF-Datei")
    parser.add_argument("--expected-pages", type=int, help="Exakt erwartete Seitenzahl")
    parser.add_argument("--expected-size", choices=sorted(PAGE_SIZES_MM), help="Erwartetes Papierformat")
    parser.add_argument("--expected-orientation", choices=("portrait", "landscape"), help="Erwartete Ausrichtung")
    parser.add_argument("--tolerance-mm", type=float, default=1.0, help="Toleranz für Papierformat, Standard 1 mm")
    parser.add_argument("--latex-log", type=Path, help="Optionales LaTeX-Protokoll")
    parser.add_argument("--allow-overfull", action="store_true", help="Overfull-Warnungen nicht als fehlgeschlagen werten")
    parser.add_argument("--render-dir", type=Path, help="Zielordner für farbige Seitenbilder")
    parser.add_argument("--render-grayscale", action="store_true", help="Zusätzlich Graustufenbilder erzeugen")
    parser.add_argument("--dpi", type=int, default=160, help="Renderauflösung, Standard 160 dpi")
    parser.add_argument("--report", type=Path, help="JSON-Bericht zusätzlich speichern")
    args = parser.parse_args()

    if not args.pdf.is_file():
        parser.error(f"PDF-Datei fehlt: {args.pdf}")
    if args.expected_pages is not None and args.expected_pages <= 0:
        parser.error("--expected-pages muss positiv sein")
    if args.tolerance_mm < 0:
        parser.error("--tolerance-mm darf nicht negativ sein")
    if args.dpi <= 0:
        parser.error("--dpi muss positiv sein")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Für die PDF-Abnahme wird das Paket pypdf benötigt.") from exc

    reader = PdfReader(str(args.pdf))
    dimensions = [page_dimensions_mm(page) for page in reader.pages]
    failures: list[str] = []
    review_items: list[str] = []

    if args.expected_pages is not None and len(reader.pages) != args.expected_pages:
        failures.append(f"Seitenzahl {len(reader.pages)} statt {args.expected_pages}")

    if args.expected_size:
        expected = PAGE_SIZES_MM[args.expected_size]
        for number, (width, height) in enumerate(dimensions, start=1):
            if not size_matches(width, height, expected, args.tolerance_mm):
                failures.append(f"Seite {number}: {width:.1f} x {height:.1f} mm statt {args.expected_size}")

    if args.expected_orientation:
        for number, (width, height) in enumerate(dimensions, start=1):
            orientation = "landscape" if width > height else "portrait"
            if orientation != args.expected_orientation:
                failures.append(f"Seite {number}: Ausrichtung {orientation} statt {args.expected_orientation}")

    log_result = None
    if args.latex_log:
        if not args.latex_log.is_file():
            failures.append(f"LaTeX-Protokoll fehlt: {args.latex_log}")
        else:
            log_result = scan_log(args.latex_log)
            for name, count in log_result["fatal"].items():
                if count:
                    failures.append(f"LaTeX-Protokoll: {count} Treffer für {name}")
            for name, count in log_result["review"].items():
                if count:
                    review_items.append(f"LaTeX-Protokoll: {count} Treffer für {name}")
            if log_result["review"].get("overfull", 0) and not args.allow_overfull:
                failures.append("LaTeX-Protokoll enthält Overfull-Boxen")

    renders: dict[str, list[str]] = {}
    if args.render_dir:
        try:
            renders["color"] = render_pdf(args.pdf, args.render_dir / "color", args.dpi, grayscale=False)
            if args.render_grayscale:
                renders["grayscale"] = render_pdf(args.pdf, args.render_dir / "grayscale", args.dpi, grayscale=True)
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            failures.append(f"Rendern fehlgeschlagen: {exc}")

    report = {
        "pdf": str(args.pdf.resolve()),
        "pages": len(reader.pages),
        "page_dimensions_mm": [
            {"page": number, "width": round(width, 2), "height": round(height, 2)}
            for number, (width, height) in enumerate(dimensions, start=1)
        ],
        "latex_log": log_result,
        "renders": renders,
        "review_items": review_items,
        "failures": failures,
        "status": "failed" if failures else ("needs_visual_review" if args.render_dir or review_items else "passed_metadata_only"),
        "visual_review_required": True,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_text, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
