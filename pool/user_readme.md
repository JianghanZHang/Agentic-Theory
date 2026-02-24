# Pool — Instructions for the Human

This is your portable knowledge bank. Drop files here.

## What to put in

Anything you want V() to know about your domain:

- **Notes** — research notes, brainstorms, fragments
- **Papers** — PDFs, LaTeX, markdown drafts
- **Code** — scripts, libraries, snippets
- **Data** — tables, measurements, logs
- **References** — links, citations, reading lists

No format requirement. No organization requirement. Just drop it.

## What happens

When you call `/V(T, B)` and the built-in skills cannot resolve a step, V() searches this directory for relevant material. If it finds something, it uses it. If not, it tells you what's missing.

Your pool is the liquid. V() crystallizes what it needs from it.

## Examples

```
pool/
├── llm_readme.md          ← (this stays — instructions for the LLM)
├── user_readme.md          ← (this stays — you're reading it)
├── my_thesis_notes.md      ← your stuff
├── experiment_results.csv  ← your stuff
├── reference_paper.pdf     ← your stuff
└── ideas/
    ├── sketch_1.md         ← subdirectories are fine
    └── sketch_2.md
```

## Tips

1. **More is fine.** V() only reads what it needs. Extra files cost nothing.
2. **Messy is fine.** V() will extract what's usable and skip what's not.
3. **Any language is fine.** English, Chinese, math, code — all readable.
4. **Update anytime.** Add, remove, replace files as your work evolves.
5. **Don't organize for the machine.** Organize for yourself (or don't). The LLM reads the llm_readme.md and knows how to search.

## What NOT to put in

- Secrets, credentials, API keys (pool/ may be pushed to a public repo)
- Files larger than your LLM's context window can handle
- Nothing. An empty pool means V() can only use its built-in skills.
