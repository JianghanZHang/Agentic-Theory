# Independent Volume — Agent Instructions

## Compilation

Each volume compiles independently. Use `xelatex`:

```bash
cd independent_volume/<name> && xelatex main.tex
```

## Invariants

1. **No backward references.** The root `main.tex` and `sections/` must never `\input`, `\include`, `\ref`, or `\cite` anything inside `independent_volume/`. Never modify root project files to accommodate a volume.

2. **Forward references are fine.** A volume may cite or reference the main paper by name, theorem number, etc.

3. **Self-contained.** Each volume has its own preamble, macros, and assets. Do not rely on the root project's build system.

4. **Template.** When creating a new volume, use `unknown_artist/` as a structural template.

5. **No cross-volume dependencies.** Volumes do not reference each other.
