# Agent Workspace — Instructions for the Machine

You are a sub-agent running V(T,B). This is your workspace.

## What this directory is

The crystallization surface. You read from `pool/` and `skills/`.
You write HERE. Every file you create is a timestamped memory.

## Protocol

When you start work on a slot or sub-task:

1. CREATE a file: `YYYY-MM-DDTHH:MM:SS_<slot>_<status>.md`
   - slot = which dominos slot you are filling (e.g., `slot_A`, `slot_2`, `grade2_X`)
   - status = `demand`, `wip`, `resolved`, `failed`
   - Example: `2026-02-20T15:30:00_slot_A_demand.md`

2. WRITE into it:
   ```
   # Slot: [which slot]
   # Parent: [parent task T if you are a sub-agent]
   # Status: DEMAND | WIP | RESOLVED | FAILED
   # Sources: [files read from pool/ or skills/]

   [your work here]
   ```

3. When status changes, CREATE A NEW FILE with the new status.
   Do not overwrite. The timeline is the memory.

## File lifecycle

```
*_demand.md    → DEMAND fired, slot k needs filling
*_wip.md       → working on it
*_resolved.md  → slot filled, claim made, cascade can continue
*_failed.md    → could not resolve, DEMAND propagates upward
```

## Rules

- ONE file per state change. Never overwrite. Append to the timeline.
- TIMESTAMP is wall-clock time when you start the file. ISO 8601.
- CITE your sources. If you read from pool/, name the file.
- KEEP IT SHORT. The workspace is a log, not a paper. State what you did, what you found, what you claim.
- FINAL CASCADE VERIFY gets its own file: `*_cascade_verify.md`.

## After V() completes

The workspace contains the full record of the cascade:
- Which slots fired DEMAND
- What was tried
- What resolved
- What the final claim is
- How many rounds it took (K* = number of resolved files)

The user can read the workspace to see exactly what happened.
Or ignore it. The workspace is for transparency, not obligation.

## Cleanup

The user (or a new V() call) may clear the workspace at any time.
Old workspace files have no authority over new runs.
Each V() execution starts from the current state of pool/ and skills/.
