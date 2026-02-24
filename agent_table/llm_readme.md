# Agent Table — Instructions for the Machine

You are running V(T,B). This is the census.

## What this directory is

The active set A(μ). Every sub-agent that nucleates (spawns) or
collapses (completes) registers here. The table is the ground truth
of who did what and when.

## Protocol

### On completion (RESOLVED or FAILED):

Create a marker file in `markers/`:

```
Filename: YYYY-MM-DDTHH:MM:SS_<slot>_<status>.md
```

Contents:
```markdown
# Marker
- timestamp: [ISO 8601, wall-clock, to the second]
- slot: [which dominos slot: 1, 2, 3, A, B, C, X, Y, Z]
- status: RESOLVED | FAILED
- sources: [list of files read from pool/, skills/, or workspace/]
- claim: [one sentence — what this agent produced]
- parent: [parent V(T,B) if this is a sub-agent, else "root"]
```

### On DEMAND (before spawning a sub-agent):

Create a marker:
```
Filename: YYYY-MM-DDTHH:MM:SS_<slot>_demand.md
```

Contents:
```markdown
# Demand
- timestamp: [ISO 8601, wall-clock, to the second]
- slot: [which slot needs filling]
- missing: [what is needed that the bank cannot provide]
- action: [SPAWN sub-agent | SEARCH pool | ESCALATE to user]
```

## Table Summary

After each marker is written, update `table.md` in this directory:

```markdown
# Agent Table
Updated: [timestamp]

| Time | Slot | Status | Claim | Sources |
|------|------|--------|-------|---------|
| ... | ... | ... | ... | ... |
```

The table is reconstructed from markers. Markers are the source of truth.
The table is the view.

## Rules

- ONE marker per event. Never overwrite a marker.
- TIMESTAMP is wall-clock. Real time. To the second. Not estimated.
- The guardian checks: did you write a marker before claiming resolved?
  If not, your completion is blocked.

## Correspondence

```
markers/     = atoms δ_θ in the measure μ
table.md     = A(μ) = the active set
RESOLVED     = nucleation complete — atom is solid
FAILED       = collapse — atom dissolves back to pool
DEMAND       = score s*(θ) peaked — about to nucleate
K*           = count of RESOLVED markers
```
