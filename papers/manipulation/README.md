# Manipulation Paper (IJRR spinoff)

Source for the standalone IJRR submission *Toward Interface Elimination
in Robotic Manipulation: A Five-Phase Architecture from Force to Vision*.

## Build

```bash
cd papers/manipulation
latexmk -pdf main.tex
```

Until the bibliography is populated, a `Package natbib Warning: Empty
'thebibliography' environment` is expected. No errors should appear.

To clean intermediate files:

```bash
latexmk -C
```

## Layout

- `main.tex`         document root (loads preamble, macros, sections, appendices, bib)
- `preamble.tex`     package imports, theorem environments
- `macros.tex`       symbol macros (notation table backing)
- `bib.bib`          BibTeX database
- `sections/`        section bodies 01--10
- `appendices/`      appendices A--C
- `figures/`         TikZ / external figures

## Codebase mapping

The four experimental stages reference codebase directories at the
agentic-theory repo root. Codebase directories retain their original
names per spec.

| Stage | Paper name                       | Codebase directory |
|-------|----------------------------------|--------------------|
| I     | Force Interface                  | `grjl/`            |
| II    | Continuous-rho Interface         | `grjl2/`           |
| III   | Kinematic Interface              | `grjl3/`           |
| IV    | Visual Interface                 | `grjl4/`           |
