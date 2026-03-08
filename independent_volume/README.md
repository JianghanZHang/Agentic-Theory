# Independent Volumes

Each subdirectory is a **standalone document** that compiles independently of the root `main.tex`.

## Rules

1. **Independent compilation.** Every volume compiles on its own:
   ```bash
   cd independent_volume/<name> && xelatex main.tex
   ```
   Each volume carries its own `\documentclass`, preamble, macros, and bibliography. No shared build dependency on the root project.

2. **Forward reference only.** A volume *may* reference or cite the main document (e.g. "see Theorem 3.2 of the main paper"). The main document must **never** reference back into an independent volume. The dependency arrow is one-way:
   ```
   independent_volume/<name>  -->  main paper    (allowed)
   main paper                 -->  independent_volume/<name>  (forbidden)
   ```

3. **Self-contained assets.** Any figures, data files, or bibliographies a volume needs live inside its own directory.

## Structure

```
independent_volume/
  README.md          # this file
  CLAUDE.md          # instructions for Claude
  unknown_artist/    # first volume
    main.tex
```

## Adding a new volume

Create a new subdirectory, place a `main.tex` inside, and ensure it compiles independently with `xelatex`.
