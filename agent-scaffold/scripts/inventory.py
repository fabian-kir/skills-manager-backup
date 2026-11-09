#!/usr/bin/env python3
"""Inventory loose files so an agent can PROPOSE moves (it never moves without approval).

  inventory.py [--root DIR] [--json]

Groups files outside agents/ and outside the profile's work folders by normalised stem
(case-folded, version/copy suffixes stripped), so "Monitor Halterung.3mf" and
"Monitor Halterung V2.3mf" land in one group with a suggested project slug.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

VERSION_RE = re.compile(r"[\s_\-]*(v\d+|\(\d+\)|final|copy|kopie|edit|neu|new|alt|old|test\d*|repariert|fixed)\b", re.I)
SOURCE_EXT = {".blend", ".step", ".stp", ".f3d", ".scad", ".svg", ".qgz", ".xcf", ".psd", ".ai", ".skp"}
EXPORT_EXT = {".3mf", ".stl", ".obj", ".mtl", ".ply", ".amf", ".dxf", ".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".gpkg"}
GCODE_EXT = {".gcode"}
SKIP_NAMES = {".DS_Store", "AGENTS.md", "CLAUDE.md", "README.md"}


def classify(p: Path) -> str:
    s = p.suffix.lower()
    if p.name.lower().endswith(".gcode.3mf") or s in GCODE_EXT:
        return "gcode"
    if s in SOURCE_EXT or p.name.lower().endswith(".blend1"):
        return "source"
    if s in EXPORT_EXT:
        return "export"
    return "other"


def norm_stem(p: Path) -> str:
    stem = p.name
    for ext in (".gcode.3mf", ".blend1"):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    else:
        stem = p.stem
    prev = None
    while prev != stem:
        prev = stem
        stem = VERSION_RE.sub("", stem).strip(" _-+")
    return re.sub(r"[\s_+]+", " ", stem).strip().lower() or p.stem.lower()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--depth", type=int, default=2, help="how deep below root to look (default 2)")
    a = ap.parse_args()
    L = C.Layout(C.find_root(a.root))
    work = set(L.config.get("work_folders", {}).keys())
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in L.root.rglob("*"):
        rel = p.relative_to(L.root)
        if not p.is_file() or p.name in SKIP_NAMES or p.name.startswith("."):
            continue
        if len(rel.parts) > a.depth or rel.parts[0] in ("agents", ".claude", ".git") or rel.parts[0] in work:
            continue
        groups[norm_stem(p)].append({"path": str(rel), "kind": classify(p), "size_kb": round(p.stat().st_size / 1024, 1)})
    out = []
    for stem, files in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        kinds = sorted({f["kind"] for f in files})
        out.append({"suggested_project": C.slugify(stem), "stem": stem, "files": files, "kinds": kinds,
                    "suggest": "projects/<slug>/" if any(k in ("source", "export", "gcode") for k in kinds) else "review"})
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    total = sum(len(g["files"]) for g in out)
    print(f"{total} loose file(s) in {len(out)} group(s). Proposed moves (nothing moved):\n")
    for g in out:
        print(f"{g['suggested_project']:40s} {', '.join(g['kinds']):22s} → {g['suggest']}")
        for f in g["files"]:
            print(f"    {f['kind']:7s} {f['path']}  ({f['size_kb']} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
