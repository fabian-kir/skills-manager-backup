#!/usr/bin/env python3
"""Validiert ein Klausur-JSONL und erzeugt Terminansichten sowie ein Register."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "termin",
    "aufgabe",
    "titel",
    "primaer",
    "tags",
    "kern",
    "verlangt",
    "methoden",
    "hinweis",
    "quelle_aufgabe",
}


def anchor(value: str) -> str:
    normalized = value.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9-]+", "", normalized)


def filename_for_term(term: str) -> str:
    normalized = term.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized).strip("_")
    return (safe or "Termin") + ".md"


def natural_key(value: Any) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", str(value))]


def source_pages(value: dict[str, Any] | None) -> str:
    if value is None:
        return "nicht vorhanden"
    filename = value.get("datei")
    pages = value.get("seiten")
    if not isinstance(filename, str) or not isinstance(pages, list) or not all(isinstance(page, int) and page > 0 for page in pages):
        raise ValueError(f"Ungültiger Quellenanker: {value!r}")
    label = "Seite" if len(pages) == 1 else "Seiten"
    return f"`{filename}`, {label} " + ", ".join(str(page) for page in pages)


def bullets(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- Keine belastbare Angabe in der Quelle."]


def points_label(value: Any) -> str:
    return "?" if value is None else str(value)


def validate_task(task: dict[str, Any], line_number: int) -> None:
    missing = sorted(REQUIRED_FIELDS - task.keys())
    if missing:
        raise ValueError(f"Zeile {line_number}: Felder fehlen: {', '.join(missing)}")
    if not isinstance(task["id"], str) or not task["id"].strip():
        raise ValueError(f"Zeile {line_number}: id muss eine nichtleere Zeichenkette sein")
    if not isinstance(task["termin"], str) or not task["termin"].strip():
        raise ValueError(f"Zeile {line_number}: termin muss eine nichtleere Zeichenkette sein")
    if task.get("punkte") is not None and (not isinstance(task["punkte"], (int, float)) or task["punkte"] < 0):
        raise ValueError(f"Zeile {line_number}: punkte muss null oder eine nichtnegative Zahl sein")
    for field in ("tags", "verlangt", "methoden"):
        if not isinstance(task[field], list) or not all(isinstance(item, str) for item in task[field]):
            raise ValueError(f"Zeile {line_number}: {field} muss eine Liste von Zeichenketten sein")
    source_pages(task["quelle_aufgabe"])
    source_pages(task.get("quelle_loesung"))


def read_tasks(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            task = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Zeile {line_number}: ungültiges JSON: {exc}") from exc
        if not isinstance(task, dict):
            raise ValueError(f"Zeile {line_number}: Ein Datensatz muss ein JSON-Objekt sein")
        task.setdefault("typ", "altklausur")
        task.setdefault("punkte", None)
        validate_task(task, line_number)
        tasks.append(task)

    ids = [task["id"] for task in tasks]
    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError("Doppelte Aufgaben-ID: " + ", ".join(duplicates))
    return tasks


def render_term(course_title: str, term: str, tasks: list[dict[str, Any]]) -> str:
    numeric_points = [float(task["punkte"]) for task in tasks if task["punkte"] is not None]
    points_meta = sum(numeric_points) if len(numeric_points) == len(tasks) else "unvollstaendig"
    lines = [
        "---",
        "typ: klausurindex",
        f"kurs: {json.dumps(course_title, ensure_ascii=False)}",
        f"termin: {json.dumps(term, ensure_ascii=False)}",
        f"aufgaben: {len(tasks)}",
        f"punkte: {points_meta}",
        "---",
        "",
        f"# {course_title}: {term}",
        "",
        "> Kuratierter Schnellindex. Für Zahlen, Formeln, Diagramme und genaue Formulierungen die genannten Originalseiten öffnen.",
        "",
        "| ID | Aufgabe | Punkte | Primärgebiet |",
        "| --- | --- | ---: | --- |",
    ]
    for task in tasks:
        lines.append(f"| [{task['id']}](#{anchor(task['id'])}) | {task['titel']} | {points_label(task['punkte'])} | {task['primaer']} |")

    for task in tasks:
        lines.extend(
            [
                "",
                f"<a id=\"{anchor(task['id'])}\"></a>",
                f"## {task['id']} - {task['titel']} ({points_label(task['punkte'])} P)",
                "",
                f"**Kern.** {task['kern']}",
                "",
                "**Verlangt.**",
                "",
                *bullets(task["verlangt"]),
                "",
                "**Typische Werkzeuge.**",
                "",
                *bullets(task["methoden"]),
                "",
                f"**Klausurhinweis.** {task['hinweis']}",
                "",
                "**Tags.** " + ", ".join(f"`{tag}`" for tag in task["tags"]),
                "",
                f"**Aufgabenquelle.** {source_pages(task['quelle_aufgabe'])}",
                "",
                f"**Lösungsquelle.** {source_pages(task.get('quelle_loesung'))}",
            ]
        )
        if task.get("qualitaet"):
            lines.extend(["", f"**Quellenstatus.** `{task['qualitaet']}`"])
    return "\n".join(lines).rstrip() + "\n"


def render_register(course_title: str, tasks: list[dict[str, Any]], term_files: dict[str, str]) -> str:
    historical = [task for task in tasks if task.get("typ") == "altklausur"]
    primary_count = Counter(str(task["primaer"]) for task in historical)
    primary_points: Counter[str] = Counter()
    known_points_total = 0.0
    for task in historical:
        if task["punkte"] is not None:
            primary_points[str(task["primaer"])] += float(task["punkte"])
            known_points_total += float(task["punkte"])

    tags: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for tag in task["tags"]:
            tags[tag].append(task["id"])

    lines = [
        "---",
        "typ: klausurregister",
        f"kurs: {json.dumps(course_title, ensure_ascii=False)}",
        f"datensaetze: {len(tasks)}",
        f"historische_aufgaben: {len(historical)}",
        "---",
        "",
        f"# Aufgabenregister {course_title}",
        "",
        "> Einstieg nach Termin, Aufgabentyp und Tag. Das kanonische Maschinenformat bleibt die JSONL-Datei.",
        "",
        "## Termine",
        "",
    ]
    for term in sorted(term_files, key=natural_key):
        lines.append(f"- [{term}]({term_files[term]})")

    lines.extend(
        [
            "",
            "## Historisches Gewicht",
            "",
            "Primärgebiete sind pro Aufgabe exklusiv. Querschnittstags dürfen überlappen. Punktanteile beziehen sich nur auf bekannte Punktzahlen.",
            "",
            "| Primärgebiet | Aufgaben | bekannte Punkte | Anteil an bekannten Punkten |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    categories = sorted(primary_count, key=lambda category: (-primary_points[category], -primary_count[category], category))
    for category in categories:
        points = primary_points[category]
        share = f"{100 * points / known_points_total:.1f}%" if known_points_total else "-"
        lines.append(f"| {category} | {primary_count[category]} | {points:g} | {share} |")

    lines.extend(["", "## Alle Aufgaben", "", "| ID | Termin | Titel | P | Primärgebiet | Tags |", "| --- | --- | --- | ---: | --- | --- |"])
    for task in tasks:
        term = task["termin"]
        lines.append(
            f"| [{task['id']}]({term_files[term]}#{anchor(task['id'])}) | {term} | {task['titel']} | {points_label(task['punkte'])} | "
            f"{task['primaer']} | " + ", ".join(f"`{tag}`" for tag in task["tags"]) + " |"
        )

    lines.extend(["", "## Tag-Suche", ""])
    for tag in sorted(tags):
        lines.append(f"- `{tag}`: " + ", ".join(tags[tag]))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Kanonische JSONL-Datei")
    parser.add_argument("--output-dir", type=Path, required=True, help="Zielordner für Register und Terminansichten")
    parser.add_argument("--course-title", required=True, help="Anzeigename des Kurses")
    parser.add_argument("--check", action="store_true", help="Nur prüfen, ob die generierten Ansichten aktuell sind")
    args = parser.parse_args()

    if not args.data.is_file():
        parser.error(f"JSONL-Datei fehlt: {args.data}")
    tasks = read_tasks(args.data)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[task["termin"]].append(task)
    for term_tasks in grouped.values():
        term_tasks.sort(key=lambda task: natural_key(task["aufgabe"]))

    term_files = {term: filename_for_term(term) for term in grouped}
    if len(set(term_files.values())) != len(term_files):
        raise ValueError("Mehrere Termine würden denselben Dateinamen erhalten")

    outputs = {
        args.output_dir / term_files[term]: render_term(args.course_title, term, grouped[term])
        for term in grouped
    }
    outputs[args.output_dir / "00_Aufgabenregister.md"] = render_register(args.course_title, tasks, term_files)

    stale: list[str] = []
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for destination, content in outputs.items():
        if args.check:
            if not destination.exists() or destination.read_text(encoding="utf-8") != content:
                stale.append(destination.name)
        else:
            destination.write_text(content, encoding="utf-8")

    if stale:
        print("Nicht aktuell: " + ", ".join(sorted(stale)), file=sys.stderr)
        return 1
    if args.check:
        print(f"OK: {len(tasks)} Aufgaben in {len(grouped)} Terminansichten sind aktuell.")
    else:
        print(f"{len(tasks)} Aufgaben in {len(grouped)} Terminansichten erzeugt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
