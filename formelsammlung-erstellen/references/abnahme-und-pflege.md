# Abnahme und Pflege

## Vor dem ersten Build

- Kanonische Quelldatei benennen.
- Ziel-PDF, Papierformat, Ausrichtung und Seitenlimit festhalten.
- Jede inhaltlich neue Formel auf einer Originalseite prüfen.
- Neue Symbole definieren und Kollisionen mit lokaler Notation ausschließen.
- Externe Bilddateien dauerhaft ablegen und reproduzierbar erzeugen.
- Keine Generatorquelle unter einem flüchtigen `tmp`-Ordner als einzige Wahrheit belassen.

Verlangt der Nutzer nur Analyse, Planung oder einen Test ohne Änderung, weder Kursordner noch kanonische Artefakte beschreiben. Falls ein Werkzeuglauf nötig ist, ein eigenes temporäres Ausgabeziel verwenden und danach belegen, dass die Originale unverändert sind.

## Technische PDF-Abnahme

Bei einem eigenständigen LaTeX-Dokument den eingebauten LaTeX-Compiler verwenden, sofern verfügbar. Andernfalls den vorhandenen Projekt-Build wiederverwenden. Keine zusätzliche TeX-Installation nur für diese Aufgabe einrichten.

Nach jedem inhaltlich oder räumlich relevanten Stand:

1. PDF neu erzeugen.
2. Buildprotokoll auf `LaTeX Error`, `Emergency stop`, `Fatal error`, fehlende Referenzen, Schriftprobleme und `Overfull` prüfen.
3. Seitenzahl, Papierformat und Ausrichtung prüfen.
4. Alle Seiten in PNG rendern.
5. Jedes Seitenbild ansehen.

Das mitgelieferte Prüfskript kann die mechanischen Schritte bündeln:

```sh
python scripts/pdf_abnahme.py PFAD/ZUR/SAMMLUNG.pdf \
  --expected-pages 2 \
  --expected-size A4 \
  --latex-log PFAD/ZUR/SAMMLUNG.log \
  --render-dir tmp/pdfs/abnahme
```

Das Skript bestätigt keine visuelle Korrektheit. Es erzeugt nur prüfbare Metadaten und Seitenbilder.

## Visuelle Abnahme

Jede finale Seite in Farbe prüfen. Bei Farbcodierung zusätzlich Graustufe oder Schwarzweiß simulieren. Kontrollieren:

- abgeschnittene Formeln, Boxen, Tabellen oder Fußzeilen
- Überlagerungen und falscher Spaltenfluss
- zu kleine Indizes, Exponenten und Matrixeinträge
- lesbare Kontraste und unterscheidbare Hinweiskategorien
- konsistente Abstände, Überschriften und Seitenübergänge
- scharfe Diagramme mit Achsen, Einheiten, Pfeilen und Legende
- unerwartete schwarze Kästen oder fehlende Glyphen
- ausreichend Rand für Druck und Duplexbetrieb

Eine kleine `Overfull`-Warnung nicht allein aufgrund der Punktzahl akzeptieren. Den betroffenen Bereich im Render prüfen. Eine unkritische `Underfull`-Warnung darf bleiben, wenn der Render sauber ist und der Abschlussbericht sie nennt.

## Fachliche Abnahme

Für jeden priorisierten Aufgabentyp eine Anwendungssimulation durchführen. Dabei nur die Formelsammlung und die konkrete Aufgabenstellung verwenden. Prüfen:

- richtige Auswahlregel
- vollständige Voraussetzungen
- konsistente Einheiten und Objektarten
- notwendige Zwischenschritte
- Randfälle und Kontrollrechnung
- Übereinstimmung mit der lokalen Kursnotation

Erkennt die Simulation eine allgemeine Lücke, das Blatt ergänzen und erneut bauen. Eine aufgabenspezifische Zahl oder Musterlösung nur aufnehmen, wenn der Nutzer ausdrücklich ein Beispielblatt verlangt.

## Bestehende Sammlung eng pflegen

1. Bestehenden Quelltext mit exakten Begriffen und Varianten durchsuchen.
2. Feststellen, ob der Inhalt bereits kursnah und ausreichend vorhanden ist. Dann nicht duplizieren.
3. Kleinsten thematischen Anker und lokale Notation bestimmen.
4. Nur den angeforderten Block ändern. Keine beiläufige Neuordnung oder globale Umformatierung.
5. Wenn der Nutzer zuerst nur eine Einschätzung verlangt, Änderungsvorschlag beschreiben und auf Freigabe warten.
6. Neu bauen und harte Kriterien erneut prüfen.
7. Betroffene Seite und angrenzenden Spalten- oder Seitenfluss visuell prüfen. Bei festem Seitenlimit alle Seiten kurz kontrollieren.
8. Genau berichten, was geändert und was verifiziert wurde.

## Abschlussbericht

Knapp dokumentieren:

- gelieferte Artefakte und kanonische Quelle
- erfüllte harte Kriterien
- Build- und PDF-Metadaten
- Umfang der visuellen Prüfung
- durchgeführte Anwendungssimulationen
- verbleibende Quellenkonflikte oder Warnungen

Keine vollständige Sicherheit behaupten, wenn Scans, inoffizielle Lösungen oder fehlende Seiten die Quellenlage begrenzen.
