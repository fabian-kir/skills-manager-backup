# Neue Formelsammlung oder neues Hilfsblatt

## 1. Auftrag und Abnahmekriterien

Vor der Inhaltserstellung die expliziten Nutzerkriterien sammeln:

- Fach oder Kurs und gewünschter Geltungsbereich
- vollständige Sammlung oder fokussiertes Blatt
- zulässige Hilfsmittel und Prüfungsregeln
- Papierformat, Ausrichtung, Seitenlimit und Druckart
- Sprache, Notation und gewünschte Dateiformate
- vorhandenes Design oder Referenzdokument

Fehlt ein hartes Kriterium, nur dann nachfragen, wenn verschiedene Annahmen das Ergebnis wesentlich verändern würden. Sonst eine vernünftige Annahme festhalten und fortfahren.

## 2. Materialinventur

Alle Originale erfassen, bevor Inhalt priorisiert wird. Mindestens unterscheiden:

| Rolle | Beispiele | Prüffrage |
| --- | --- | --- |
| aktuelle Konventionsquelle | offizielles Hilfsblatt, neueste Folien | Welche Notation und Voraussetzungen gelten? |
| ausführliche Fachquelle | Skript, Lehrbuchauszug | Wo stehen Herleitungen und Definitionen? |
| Vorlesungsnähe | Mitschrift, Übungsblatt | Welche Betonungen und Lösungswege verlangt der Kurs? |
| Prüfungsquelle | Klausur, Lösung, Bewertungsraster | Was wurde tatsächlich verlangt und bepunktet? |
| Zusatzmaterial | private Blätter, Erinnerungsprotokolle | Was ist hilfreich, aber nicht offiziell belegt? |

Leere, unvollständige, scanlastige oder inoffizielle Dateien sichtbar markieren. Eingebettete Bilder und Formeln in DOCX oder PPTX visuell prüfen.

Eine leere oder defekte Klausurdatei erzeugt keinen Platzhalter-Datensatz. Den Blocker dokumentieren und den Klausurindex aussetzen, bis eine belastbare Quelle vorliegt. Ohne auswertbare Klausuren weder Häufigkeiten noch Punktgewichte erfinden und das Ergebnis nicht als klausuroptimierte Endfassung bezeichnen.

Für eine dauerhafte Arbeitsgrundlage kann folgende Struktur verwendet werden:

```text
KI-Arbeitsgrundlage/
|-- 00_START_HIER.md
|-- 01_Kursprofil_und_Konventionen.md
|-- 02_Themenkarte.md
|-- 03_Quellenkatalog.md
|-- Quelltext/
|   `-- _manifest.json
`-- Klausuren/
    |-- aufgaben.jsonl
    `-- 00_Aufgabenregister.md
```

Die Struktur ist eine Empfehlung. Eine vorhandene, gleichwertige Ordnung nicht unnötig ersetzen.

## 3. Suchschicht und Originalprüfung

Eine seitenweise Suchschicht beschleunigt die Navigation. Sie ersetzt keine Originalquelle.

Mit dem mitgelieferten Skript:

```sh
python scripts/materialien_extrahieren.py --root KURSWURZEL --output KI-Arbeitsgrundlage/Quelltext
python scripts/materialien_extrahieren.py --root KURSWURZEL --output KI-Arbeitsgrundlage/Quelltext --check
```

Treffer immer auf der zugehörigen PDF-Seite, DOCX-Seite oder Folie bestätigen, wenn Exponenten, Brüche, Matrizen, Diagramme, Vorzeichen oder genaue Formulierungen zählen.

## 4. Kursprofil und Quellenhierarchie

Kuratieren, statt den gesamten Stoff zu duplizieren. Festhalten:

- verbindliche Symbolbelegung und Objektarten
- Normalisierungen, Vorzeichen und Transformationskonventionen
- Voraussetzungen, die in Standardformeln leicht fehlen
- verlangte Darstellungsformen, zum Beispiel grafischer Rechenweg
- typische Unterschiede zwischen offiziellen Quellen
- Reihenfolge, in der widersprüchliche Quellen aufgelöst werden

Konflikte nicht still entscheiden. Quelle, Stelle, gewählte Fassung und verbleibende Unsicherheit dokumentieren.

Eine Formelsammlung aus einem anderen Fach darf als Layoutreferenz dienen. Ihre Formeln, Prioritäten und Konventionen sind keine Fachquelle für den neuen Kurs.

## 5. Klausurregister und Gewichtung

Jede Aufgabe als eigenen Datensatz erfassen. Aufgaben- und Lösungsseiten getrennt angeben. Die genaue Struktur steht in [Datenmodelle](datenmodelle.md).

Bei der Priorisierung zusammen betrachten:

- wiederkehrende Aufgabentypen
- Punkte und Umfang
- Aktualität
- offizielle oder unsichere Herkunft
- benötigte Grundformeln und Verbindungsschritte
- typische Punktverluste, Randfälle und Darstellungsanforderungen

Ein Thema mit wenigen Aufgaben kann trotzdem unverzichtbar sein, wenn es Grundlage mehrerer anderer Aufgabentypen ist.

## 6. Abdeckungsmatrix und Seitenbudget

Vor dem Setzen eine Matrix anlegen, die mindestens diese Fragen beantwortet:

- Welcher Aufgabentyp soll mit dem Blatt lösbar sein?
- Woran erkennt man ihn im Aufgabentext oder Diagramm?
- Welche Voraussetzungen gelten?
- Welche Formel oder Lösungsroute wird gebraucht?
- Welche Symbole müssen erklärt werden?
- Welcher Randfall oder Fehler ist klausurrelevant?
- Welche Originalquelle und Seite belegen den Inhalt?
- Wo steht der Inhalt später im Blatt?

Danach Platz je Themenblock vergeben. Seltene Details verdrängen keine häufig gebrauchten Brückenformeln oder Entscheidungshilfen.

## 7. Blattinhalt schreiben

Für einen typischen Block diese Reihenfolge verwenden, soweit sie fachlich passt:

1. Erkennungssignal oder Einsatzfrage
2. Voraussetzungen
3. Formel mit definierten Symbolen und Einheiten
4. kurze, direkt ausführbare Schrittfolge
5. Randfall oder typische Falle
6. Plausibilitäts- oder Ergebnischeck
7. kompakter Quellenanker im Quelltext oder Begleitdokument

Kursnotation beibehalten. Standardnotation nur ergänzen, wenn sie die Nutzung verbessert und keine Verwechslung erzeugt.

Für Formeln und dichtes Layout ist LaTeX der Standard. Für ein visuelles Einseitenblatt kann ein reproduzierbarer Python-Generator passend sein. In beiden Fällen genau eine primäre kanonische Inhaltsquelle festlegen. Separat erzeugte Grafiken samt Generator als deklarierte Abhängigkeiten dauerhaft außerhalb eines flüchtigen `tmp`-Ordners speichern.

## 8. Anwendungssimulation

Vor der Endabnahme pro wichtigem Aufgabentyp mindestens eine repräsentative Aufgabe mit der Sammlung bearbeiten. Prüfen:

- Lässt sich die richtige Formel allein anhand des Blatts auswählen?
- Sind alle benötigten Zwischenschritte und Symbolbedeutungen vorhanden?
- Deckt das Blatt den erwartbaren Randfall ab?
- Führt die lokale Kursnotation ohne stillen Wechsel zum Ergebnis?
- Ist die Lösung innerhalb des Seiten- und Platzbudgets lesbar?

Nur allgemeine, wiederverwendbare Lücken in die Sammlung aufnehmen. Eine einzelne Musterlösung nicht als allgemeine Regel tarnen.

## 9. Ausgabeordner

Für eine umfangreiche Sammlung ist diese Form sinnvoll:

```text
output/pdf/FORMELSAMMLUNG_NAME/
|-- FORMELSAMMLUNG_NAME.tex
|-- FORMELSAMMLUNG_NAME.pdf
|-- Materialuebersicht.md
|-- Pruefungsabgleich.md
`-- Abschlussbericht.md
```

Bei einem fokussierten Blatt die Dokumentation schlank halten. Quelldatei und PDF bleiben trotzdem gemeinsam reproduzierbar.
