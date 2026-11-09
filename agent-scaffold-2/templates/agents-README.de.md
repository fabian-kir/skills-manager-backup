# Der Ordner `agents/` — was das ist, in einfachen Worten

Dieser Ordner gehört den KI-Agenten, die in diesem Projekt arbeiten. Du musst ihn nie öffnen,
darfst aber alles lesen. Alles außerhalb von `agents/` ist für Menschen: Inputs, Arbeitsergebnisse,
Deliverables.

**Wie die Sicherung funktioniert, ohne dass du etwas sagen musst.** `AGENTS.md` im Projektroot wird
in jede Agent-Session geladen. Dort steht: Nichts zählt, bis es in einer Datei ist; jeder Agent
besitzt eigene Dateien; geteilte Listen sind append-only; alles, was bleiben soll, läuft durch ein
Skript, das es entweder als *Vorschlag* für einen Kurator ablegt oder – wo das Projekt es erlaubt –
sofort in die Wissensbasis schreibt, als ungeprüft markiert. Ein kleines Skript sagt jeder Session,
ob ein Aufräumen fällig ist.

**Was hier liegt**

| Ordner / Datei | Bedeutung |
|---|---|
| `STATUS.md` | Ziel, aktueller Stand, Checkpoints, wer woran arbeitet. Hier zuerst nachsehen. |
| `LOG.md` | Eine Zeile pro Agent-Aktion. Von unten lesen. |
| `registers/decisions/` | Eine Datei pro Entscheidung, die jemand später rückgängig machen könnte, ohne zu wissen warum. `INDEX.md` wird generiert und zeigt nur geltende Entscheidungen. |
| `registers/lessons/` | Was Agenten gelernt haben, inkl. deiner Korrekturen als feste Regeln. Ebenfalls indexiert. |
| `registers/examples/` | Das jeweils beste aktuelle Beispiel pro Ausgabetyp, eins pro Name, keine Versionen. |
| `registers/questions.md`, `sources.md`, `glossary.md` | Offene Fragen, alle genutzten Quellen, ein Begriff = eine Bedeutung. |
| `inbox/` | Vorschläge, die auf einen Kurator warten. `tentative`-Einträge gelten schon; nur markierte brauchen dein Ja. Einträge, die ein Agent direkt ins Register geschrieben hat, tragen `attested: author`, bis ein Kurator sie angesehen hat. |
| `scratch/` | Unfertige Experimente („Spikes“). Nicht verbindlich. Wird aufgeräumt. |
| `templates/`, `scripts/`, `roles/` | Was Agenten kopieren, was sie ausführen, wie sich jede Rolle verhält. |

**Was du tust**

- Wenn ein Agent eine Antwort mit „Aufräumen ist fällig — Kurator-Lauf starten?“ beendet, sag bei
  Gelegenheit ja. Dauert wenige Minuten, endet mit einer kurzen Zusammenfassung; du antwortest pro
  zurückgehaltenem Punkt mit ja/nein.
- Korrigiere einen Agenten einmal; er sollte eine feste Regel vorschlagen. Passiert es trotzdem
  wieder, bitte um einen Kurator-Lauf.
- `python3 -I agents/scripts/status.py` zeigt den Stand in einer Zeile; `lint.py` zeigt, was unordentlich ist.

Erstellt am {{DATE}} mit dem Skill agent-scaffold, Profil `{{PROFILE}}`. Der Ordner funktioniert auch ohne installierten Skill.
