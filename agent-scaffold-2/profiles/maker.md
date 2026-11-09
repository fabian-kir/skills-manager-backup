Machine and materials (the facts every agent needs): {{MACHINE_FACTS}}

```
projects/<slug>/source/     editable sources (.blend, .step, .svg, .qgz) — the truth
projects/<slug>/exports/    .3mf/.stl derived from source — regenerate, don't hand-edit
projects/<slug>/gcode/      sliced output; filename = <export>_<nozzle>_<material>_<layer>.gcode.3mf
projects/<slug>/PROJECT.md  file guide + attempt log (agents/templates/PROJECT.md) — the only prose per project
profiles/                   slicer/material presets exported from the slicer, named <machine>_<nozzle>_<material>.json
experiments/<slug>/         sample map (id → parameters), results, photos; outcome → propose.py lesson
```

After every print attempt: one row in the project's attempt log (date, file, nozzle, material, key settings, result, photo, what to change). An attempt that fails is still a row.
What you keep telling agents: `propose.py rule` so it becomes a standing rule here, not a thing repeated in prompts. Proven settings → `propose.py example --file <gcode.3mf> --settings nozzle=0.4 layer=0.2 ...`; the examples index is the first thing to read before slicing anything.
Loose files at the root are a smell: inventory with `agents/scripts/inventory.py`, propose moves, move only on approval. Never delete a source; supersede with a dated export.
Shared layer above projects: `agents/registers/lessons/` is where "do this differently next time" lives and transfers between projects.
