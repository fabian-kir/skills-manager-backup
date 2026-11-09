# Datenmodelle für Quellen, Klausuren und Abdeckung

## Materialübersicht

Das Extraktionsskript erzeugt ein technisches Manifest. Ergänzend eine kuratierte Tabelle führen:

| Quelle | Stand | Umfang | Rolle | Autorität | Textqualität | Visuell geprüft | Einschränkung |
| --- | --- | ---: | --- | --- | --- | --- | --- |

`Autorität` beschreibt zum Beispiel `offiziell-aktuell`, `offiziell-alt`, `Übung`, `studentisch` oder `inoffiziell-unsicher`.

## Kanonischer Klausurdatensatz

Eine JSON-Zeile pro Aufgabe verwenden:

```json
{"id":"KURS-WS2025-A1","typ":"altklausur","termin":"WS2025","aufgabe":1,"titel":"Kurztitel","punkte":20,"primaer":"Hauptgebiet","tags":["unterthema","methode"],"kern":"Fachlicher Kern der Aufgabe.","verlangt":["abstrakte Teilleistung"],"methoden":["typischer Lösungsweg"],"hinweis":"Darstellungsanforderung, Näherung oder typische Falle.","quelle_aufgabe":{"datei":"Klausur.pdf","seiten":[1,2]},"quelle_loesung":{"datei":"Loesung.pdf","seiten":[3]},"qualitaet":"offiziell"}
```

Regeln:

- IDs müssen eindeutig und stabil sein.
- Ein exklusives `primaer` erleichtert die Gewichtung. Querschnittsthemen stehen zusätzlich in `tags`.
- `punkte` darf `null` sein, wenn die Quelle keine belastbare Angabe enthält.
- `kern` beschreibt die erforderliche Denkleistung hinter dem Aufgabentitel.
- `verlangt` abstrahiert die tatsächlichen Teilaufgaben.
- `hinweis` erfasst Punktabzüge, grafische Anforderungen, Näherungen und Quellenrisiken.
- Aufgaben- und Lösungsseiten nie zusammenwerfen.
- Unleserliche oder fehlende Angaben nicht rekonstruieren. `qualitaet` setzen und die Lücke benennen.

Das Register erzeugen:

```sh
python scripts/klausurindex_erzeugen.py \
  --data KI-Arbeitsgrundlage/Klausuren/aufgaben.jsonl \
  --output-dir KI-Arbeitsgrundlage/Klausuren \
  --course-title "Kursname"
```

Danach mit `--check` prüfen, dass die Ansichten zum JSONL passen.

## Abdeckungsmatrix

Für den Prüfungsabgleich eine Zeile pro wiederkehrender Aufgabenfamilie verwenden:

| Aufgabenfamilie | Evidenz | Gewicht | Erkennung | Voraussetzungen | Formel oder Route | Randfall | Originalquelle | Blattanker | Status |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |

Mögliche Statuswerte:

- `abgedeckt`
- `teilweise`
- `bewusst-ausgelassen`
- `quelle-unsicher`
- `noch-zu-pruefen`

`Gewicht` darf Punkte, Häufigkeit und Aktualität kombinieren. Die Berechnungsart im Dokument erklären. Bei wenig Daten qualitative Begriffe verwenden, statt Prozentwerte vorzutäuschen.

## Quellenanker im Blatt

Die Formelsammlung selbst soll knapp bleiben. Quellen können als kurze Kommentare im Quelltext oder in `Pruefungsabgleich.md` stehen. Ein Anker enthält:

- Originaldatei
- PDF-Seite, Dokumentseite oder Foliennummer
- Abschnitt oder Aufgaben-ID
- Status der Quelle
- Hinweis auf abweichende Konventionen

Zeilennummern in generierten TeX-Dateien sind keine stabilen Quellenanker.
