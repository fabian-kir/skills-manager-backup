---
name: formelsammlung-erstellen
description: Erstellt oder überarbeitet fachunabhängig quellentreue, klausuroptimierte Formelsammlungen und fokussierte Hilfsblätter aus lokalen Vorlesungsunterlagen, Übungen und Altklausuren. Verwenden, wenn aus einem Kursordner ein reproduzierbares LaTeX- oder PDF-Artefakt entstehen oder eine bestehende Sammlung eng geprüft und gepflegt werden soll. Nicht für eine einzelne Fachfrage ohne Dokumentauftrag.
---

# Formelsammlungen erstellen

Erzeuge ein anwendbares Prüfungswerkzeug aus den lokalen Originalquellen. Übernimm die Arbeitsweise des Systemdynamik-Ordners, nicht dessen Fachinhalt. Die große vorhandene Referenzsammlung dort war eine Eingangsquelle. Reproduzierbar erstellt wurden fokussierte Blätter nach Quellenanalyse, Klausurindex und visueller PDF-Prüfung.

## Modus wählen

- **Neue Sammlung:** Materialbestand, Klausuren und Konventionen erst aufarbeiten. Danach Inhalt planen und setzen. [Neuanlage lesen](references/neuanlage.md).
- **Fokussiertes Hilfsblatt:** Den gleichen Quellenweg auf ein enges Aufgabengebiet anwenden. Nur die dafür nötigen Quellen und Klausuren auswerten. [Neuanlage lesen](references/neuanlage.md).
- **Bestehende Sammlung pflegen:** Zuerst im kanonischen Quelltext suchen. Nur den kleinsten passenden Block ändern. [Abnahme und Pflege lesen](references/abnahme-und-pflege.md).

Vor jeder PDF-Erstellung oder PDF-Änderung [Abnahme und Pflege](references/abnahme-und-pflege.md) lesen. Wenn ein Klausurregister oder eine Abdeckungsmatrix nötig ist, zusätzlich [Datenmodelle](references/datenmodelle.md) lesen.

## Verbindliche Grundsätze

1. Originalunterlagen unverändert lassen. Suchtexte, Indizes, Arbeitsdateien und Endausgaben getrennt speichern.
2. Vor einer größeren Neuerstellung inventarisieren. Nicht direkt mit dem Layout beginnen.
3. Extrahierter Text ist ein Suchindex. Formeln, Matrizen, Diagramme, Vorzeichen und genaue Aufgabenwörter auf der genannten Originalseite prüfen.
4. Eine Quellenhierarchie festlegen. Aktuelle offizielle Kurskonventionen und die konkrete Aufgabenformulierung haben Vorrang vor Standardnotation aus dem Gedächtnis.
5. Klausurrelevanz aus Aufgabenarten, Häufigkeit, Punkten, Aktualität und typischen Fehlern ableiten. Keine Scheingenauigkeit bei wenigen oder unsicheren Klausuren. Ohne belastbare Klausurevidenz das Ergebnis als quellenorientierten Entwurf kennzeichnen, nicht als klausuroptimierte Endfassung.
6. Jede Formelgruppe möglichst mit Erkennungssignal, Voraussetzungen, Symbolbedeutung, Vorgehen, Randfall und Kontrolle schreiben. Verdichtete Abschrift ohne Anwendungshilfe vermeiden.
7. Genau eine primäre editierbare Datei als inhaltliche Wahrheit pro Blatt festlegen. Separat erzeugte Grafiken dürfen eigene, versionierte Quelldateien haben; sie sind deklarierte Abhängigkeiten der Primärdatei. Generatoren, Markdown-Fassungen und TeX-Dateien dürfen nicht unkontrolliert auseinanderlaufen.
8. Diagramme nie als ASCII-Grafik erstellen. Matplotlib, LaTeX-Grafik, SVG oder ein anderes echtes Grafikformat verwenden und Achsen, Einheiten, Richtungen und Signalnamen beschriften.
9. Ein erfolgreicher Build genügt nicht. Jede finale Seite rendern und visuell prüfen.

## Standardablauf

1. Kurswurzel und lokale Anweisungen finden. Vorhandene Arbeitsgrundlagen, Formelsammlungen, Buildskripte und Ausgabeordner wiederverwenden.
2. Ziel und harte Kriterien festhalten. Dazu gehören erlaubte Hilfsmittel, Sprache, Papierformat, Ausrichtung, Seitenlimit, Druckart, Farbe oder Graustufe und gewünschte Quelldatei. Nachfragen, wenn eine offene Wahl das Layout wesentlich verändert.
3. Materialien inventarisieren und bei Bedarf eine seitenweise Suchschicht erzeugen. Das mitgelieferte Skript `scripts/materialien_extrahieren.py` ist ein fachneutrales Startwerkzeug.
4. Quellenhierarchie, Kursnotation, Voraussetzungen und Darstellungsanforderungen kuratieren.
5. Altklausuren aufgabenweise erfassen. Aufgaben- und Lösungsseiten getrennt halten. `scripts/klausurindex_erzeugen.py` erzeugt daraus lesbare Ansichten.
6. Eine Abdeckungsmatrix erstellen. Sie verbindet Aufgabentypen mit benötigten Formeln, Lösungsrouten, Quellen, Randfällen und geplanten Blattankern.
7. Erst jetzt die Sammlung setzen. Für dichte Mathematik LaTeX bevorzugen. Bei grafiklastigen Einseitern darf ein reproduzierbarer Python- oder ReportLab-Generator sinnvoller sein.
8. Repräsentative Klausuraufgaben mit dem Blatt probeweise lösen. Fehlende Brücken und missverständliche Symbole im Blatt korrigieren.
9. PDF technisch und visuell abnehmen. `scripts/pdf_abnahme.py` prüft Metadaten, optionale harte Kriterien und erzeugt Seitenbilder. Die Bilder anschließend selbst ansehen.

## Mitgelieferte Ressourcen

- `scripts/materialien_extrahieren.py` erzeugt seitenweise Suchtexte und ein Manifest mit Dateigröße, Status und SHA-256.
- `scripts/klausurindex_erzeugen.py` erzeugt aus einem kanonischen JSONL-Register Jahresansichten und ein Gesamtregister.
- `scripts/pdf_abnahme.py` prüft Seitenzahl und Format, scannt ein optionales LaTeX-Protokoll und rendert die PDF-Seiten.
- `assets/kompakt-a4.tex` ist ein optionaler, kompakter LaTeX-Startpunkt. Bestehendes Kursdesign hat Vorrang.

Die Skripte zuerst mit `--help` aufrufen. Für PDF-, DOCX- oder PPTX-Verarbeitung die gebündelten Workspace-Abhängigkeiten verwenden, falls der normale Python-Lauf Pakete vermisst.

## Ausgabe und Abschluss

Für eine große Neuerstellung einen eigenen Ausgabeordner verwenden. Übliche Endartefakte sind PDF, kanonische Quelldatei, Materialübersicht, Prüfungsabgleich und kurzer Abschlussbericht. Bei einem fokussierten Blatt reichen Quelldatei, PDF und nachvollziehbare Quellenanker.

Eine Aufgabe ist erst abgeschlossen, wenn:

- alle harten Nutzerkriterien nachweislich erfüllt sind,
- jede fachlich wichtige Aussage auf eine Originalquelle oder eine offen gekennzeichnete Herleitung zurückgeht,
- die kanonische Quelle die gelieferte PDF reproduziert,
- die letzten Seitenbilder frei von Überlagerungen, abgeschnittenen Inhalten und unlesbaren Formeln sind,
- verbleibende Quellenunsicherheiten im Abschluss genannt werden.
