#!/usr/bin/env python3
"""Erzeugt eine durchsuchbare Markdown-Schicht über Kursunterlagen.

Die Ausgabe ist ein Suchindex. Formeln, Diagramme und genaue Formulierungen
müssen weiterhin auf der genannten Originalseite geprüft werden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_EXCLUDED_PARTS = {
    ".agents",
    ".codex",
    ".git",
    "KI-Arbeitsgrundlage",
    "__pycache__",
    "output",
    "tmp",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in normalized.splitlines()]
    return "\n".join(lines).strip()


def yaml_string(value: str) -> str:
    return json.dumps(unicodedata.normalize("NFC", value), ensure_ascii=False)


def slug(relative_path: Path) -> str:
    raw = "__".join(relative_path.with_suffix("").parts)
    ascii_name = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    result = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_name).strip("_").lower()
    return (result or "quelle") + ".md"


def frontmatter(path: Path, relative_path: Path, source_format: str, **extra: Any) -> list[str]:
    lines = [
        "---",
        "typ: quelltext-extraktion",
        f"quelle: {yaml_string(relative_path.as_posix())}",
        f"format: {source_format}",
        f"bytes: {path.stat().st_size}",
        f"sha256: {sha256(path)}",
    ]
    for key, value in extra.items():
        if isinstance(value, str):
            lines.append(f"{key}: {yaml_string(value)}")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", ""])
    return lines


def extract_pdf(path: Path, relative_path: Path) -> tuple[str, dict[str, Any]]:
    if path.stat().st_size == 0:
        lines = frontmatter(
            path,
            relative_path,
            "pdf",
            status="leer",
            seiten=0,
            hinweis="Die Quelldatei hat 0 Byte und enthält keinen auswertbaren Inhalt.",
        )
        lines.extend(
            [
                f"# Leere Quelle: {relative_path.name}",
                "",
                "Die Datei muss vor einer fachlichen Auswertung erneut synchronisiert oder ersetzt werden.",
                "",
            ]
        )
        return "\n".join(lines), {"status": "leer", "seiten": 0, "zeichen": 0}

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Für PDF-Quellen wird das Paket pypdf benötigt.") from exc

    reader = PdfReader(str(path))
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise RuntimeError("PDF ist verschlüsselt und kann nicht ohne Kennwort gelesen werden.")

    page_texts = [clean_text(page.extract_text() or "") for page in reader.pages]
    total_chars = sum(len(text) for text in page_texts)
    pages_with_text = sum(len(text) >= 40 for text in page_texts)
    likely_scans = [index for index, text in enumerate(page_texts, start=1) if len(text) < 40]
    lines = frontmatter(
        path,
        relative_path,
        "pdf",
        status="extrahiert",
        seiten=len(page_texts),
        seiten_mit_text=pages_with_text,
        moegliche_scanseiten=likely_scans,
        zeichen=total_chars,
        verifikation="Original-PDF-Seite für Formeln, Diagramme und Lesereihenfolge prüfen",
    )
    lines.extend(
        [
            f"# Suchtext: {relative_path.name}",
            "",
            "> Automatisch extrahierter Suchtext. Formeln, Spaltenreihenfolge und Sonderzeichen können beschädigt sein.",
            "",
        ]
    )
    for number, text in enumerate(page_texts, start=1):
        lines.extend([f"## PDF-Seite {number}", "", text or "_Kein extrahierbarer Text._", ""])
    return "\n".join(lines), {
        "status": "extrahiert",
        "seiten": len(page_texts),
        "seiten_mit_text": pages_with_text,
        "moegliche_scanseiten": likely_scans,
        "zeichen": total_chars,
    }


def table_as_markdown(rows: Iterable[Iterable[str]]) -> list[str]:
    normalized_rows = [
        [clean_text(cell).replace("\n", "<br>").replace("|", "\\|") for cell in row]
        for row in rows
    ]
    if not normalized_rows:
        return ["_Leere Tabelle._"]
    width = max(len(row) for row in normalized_rows)
    padded = [row + [""] * (width - len(row)) for row in normalized_rows]
    return [
        "| " + " | ".join(padded[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
        *["| " + " | ".join(row) + " |" for row in padded[1:]],
    ]


def extract_docx(path: Path, relative_path: Path) -> tuple[str, dict[str, Any]]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Für DOCX-Quellen wird das Paket python-docx benötigt.") from exc

    document = Document(str(path))
    paragraphs = [clean_text(paragraph.text) for paragraph in document.paragraphs]
    paragraphs = [text for text in paragraphs if text]
    image_count = len(document.inline_shapes)
    lines = frontmatter(
        path,
        relative_path,
        "docx",
        status="extrahiert",
        absaetze=len(paragraphs),
        tabellen=len(document.tables),
        inline_bilder=image_count,
        verifikation="Original-DOCX oder gerenderte Seiten für Formeln, Bilder und Layout prüfen",
    )
    lines.extend(
        [
            f"# Suchtext: {relative_path.name}",
            "",
            "> Text und Tabellen wurden extrahiert. Eingebettete Formeln und Bilder können fehlen.",
            "",
        ]
    )
    for number, text in enumerate(paragraphs, start=1):
        lines.extend([f"## Absatz {number}", "", text, ""])
    for number, table in enumerate(document.tables, start=1):
        rows = ([cell.text for cell in row.cells] for row in table.rows)
        lines.extend([f"## Tabelle {number}", "", *table_as_markdown(rows), ""])
    return "\n".join(lines), {
        "status": "extrahiert",
        "seiten": None,
        "absaetze": len(paragraphs),
        "tabellen": len(document.tables),
        "inline_bilder": image_count,
        "zeichen": sum(len(text) for text in paragraphs),
    }


def extract_pptx(path: Path, relative_path: Path) -> tuple[str, dict[str, Any]]:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise RuntimeError("Für PPTX-Quellen wird das Paket python-pptx benötigt.") from exc

    presentation = Presentation(str(path))
    slide_texts: list[str] = []
    image_count = 0
    for slide in presentation.slides:
        texts: list[str] = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                text = clean_text(shape.text)
                if text:
                    texts.append(text)
            if int(shape.shape_type) == 13:
                image_count += 1
        slide_texts.append("\n\n".join(texts))

    lines = frontmatter(
        path,
        relative_path,
        "pptx",
        status="extrahiert",
        folien=len(slide_texts),
        bilder=image_count,
        verifikation="Originalfolie für Formeln, Diagramme, Animationen und räumliche Zuordnung prüfen",
    )
    lines.extend(
        [
            f"# Suchtext: {relative_path.name}",
            "",
            "> Textfelder wurden extrahiert. Bilder, Formeln und Animationen sind nicht vollständig abgebildet.",
            "",
        ]
    )
    for number, text in enumerate(slide_texts, start=1):
        lines.extend([f"## Folie {number}", "", text or "_Kein extrahierbarer Text._", ""])
    return "\n".join(lines), {
        "status": "extrahiert",
        "folien": len(slide_texts),
        "bilder": image_count,
        "zeichen": sum(len(text) for text in slide_texts),
    }


def extract_image(path: Path, relative_path: Path) -> tuple[str, dict[str, Any]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Für Bildquellen wird das Paket Pillow benötigt.") from exc

    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
    lines = frontmatter(
        path,
        relative_path,
        path.suffix.lower().lstrip("."),
        status="bildindex",
        breite_px=width,
        hoehe_px=height,
        farbmodus=mode,
        verifikation="Bild visuell prüfen; es wird bewusst kein OCR-Text als fachlich verbindlich ausgegeben",
    )
    lines.extend(
        [
            f"# Bildquelle: {relative_path.name}",
            "",
            f"- Abmessungen: {width} x {height} px",
            f"- Farbmodus: {mode}",
            "- Inhalt: visuell am Original prüfen und kuratiert beschreiben.",
            "",
        ]
    )
    return "\n".join(lines), {
        "status": "bildindex",
        "breite_px": width,
        "hoehe_px": height,
        "farbmodus": mode,
    }


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Kurswurzel, Standard ist das aktuelle Verzeichnis")
    parser.add_argument("--output", type=Path, required=True, help="Zielordner für Suchtexte und Manifest")
    parser.add_argument("--exclude", action="append", default=[], help="Zusätzlicher auszuschließender Pfadteil, mehrfach möglich")
    parser.add_argument("--check", action="store_true", help="Nur prüfen, ob alle generierten Dateien aktuell sind")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = args.output if args.output.is_absolute() else root / args.output
    output_dir = output_dir.resolve()
    excluded_parts = DEFAULT_EXCLUDED_PARTS | set(args.exclude)

    if not root.is_dir():
        parser.error(f"Kurswurzel ist kein Verzeichnis: {root}")

    sources: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if path_is_within(path, output_dir):
            continue
        relative = path.relative_to(root)
        if any(part in excluded_parts for part in relative.parts[:-1]):
            continue
        if path.name == ".DS_Store":
            continue
        sources.append(path)

    generated_names: set[str] = set()
    manifest: list[dict[str, Any]] = []
    mismatches: list[str] = []
    extraction_errors: list[str] = []

    if not args.check:
        output_dir.mkdir(parents=True, exist_ok=True)

    for path in sources:
        relative = path.relative_to(root)
        destination_name = slug(relative)
        if destination_name in generated_names:
            raise ValueError(f"Namenskollision bei extrahierten Quellen: {relative}")
        generated_names.add(destination_name)

        try:
            if path.suffix.lower() == ".pdf":
                content, metadata = extract_pdf(path, relative)
            elif path.suffix.lower() == ".docx":
                content, metadata = extract_docx(path, relative)
            elif path.suffix.lower() == ".pptx":
                content, metadata = extract_pptx(path, relative)
            else:
                content, metadata = extract_image(path, relative)
        except Exception as exc:  # Der Katalog soll trotz einer defekten Quelle weiter entstehen.
            message = f"{relative}: {exc}"
            extraction_errors.append(message)
            metadata = {"status": "fehler", "fehler": str(exc)}
            content = "\n".join(
                frontmatter(path, relative, path.suffix.lower().lstrip("."), **metadata)
                + [f"# Nicht extrahierbare Quelle: {relative.name}", "", str(exc), ""]
            )

        content = content.rstrip() + "\n"
        destination = output_dir / destination_name
        if args.check:
            if not destination.exists() or destination.read_text(encoding="utf-8") != content:
                mismatches.append(str(destination.relative_to(root) if path_is_within(destination, root) else destination))
        else:
            destination.write_text(content, encoding="utf-8")

        manifest.append(
            {
                "quelle": unicodedata.normalize("NFC", relative.as_posix()),
                "ausgabe": destination.name,
                "format": path.suffix.lower().lstrip("."),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                **metadata,
            }
        )

    manifest_path = output_dir / "_manifest.json"
    manifest_content = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not manifest_path.exists() or manifest_path.read_text(encoding="utf-8") != manifest_content:
            mismatches.append(str(manifest_path.relative_to(root) if path_is_within(manifest_path, root) else manifest_path))
        if mismatches:
            print("Nicht aktuell:", file=sys.stderr)
            for mismatch in mismatches:
                print(f"- {mismatch}", file=sys.stderr)
            return 1
        print(f"OK: {len(sources)} Quellen und Manifest sind aktuell.")
    else:
        manifest_path.write_text(manifest_content, encoding="utf-8")
        print(f"{len(sources)} Quellen nach {output_dir} extrahiert.")

    if extraction_errors:
        print("Extraktionsfehler:", file=sys.stderr)
        for error in extraction_errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
