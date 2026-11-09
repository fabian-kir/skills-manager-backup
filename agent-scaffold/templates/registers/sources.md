# Source register (append-only)

One source per line. Append with `agents/scripts/append.sh agents/registers/sources.md "<line>"`. Never edit existing lines.
Source id = your agent prefix + a number (e.g. `SA12`, `SE201`) so parallel agents never collide; check with `grep -c '^| SA' agents/registers/sources.md` and add a margin.
Type: primary (filing, official site, press release, measured data) | secondary (reputable press, analyst) | tertiary (blog, wiki) | internal (team material).

| id | type | title | url or locator | publisher | published | accessed | used in | note |
|---|---|---|---|---|---|---|---|---|
