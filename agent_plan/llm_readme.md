# Agent Plan — Instructions for the Machine

You are running V(T,B). This is the planning surface.

## Horizon

```
horizon: 0
```

**The user sets this number.** It means: how many steps ahead to plan.

| Value | Behavior |
|-------|----------|
| `0` | Bang-bang control. No lookahead. React to the immediate DEMAND only. |
| `N > 0` | Before acting, write a plan for the next N steps. After acting, revise the plan. |

If the user has not changed the horizon from 0, do NOT plan ahead.
Just solve the immediate DEMAND and move on.

## The Plan File

When horizon > 0, create `plan.md` in this directory on the first V() call.

Format:
```markdown
# Plan — V(T, B)
Updated: [ISO 8601 timestamp, wall-clock, to the second]
Horizon: [N]

## Current step
[What you are doing right now]

## Next N steps
1. [Step +1: what comes next and why]
2. [Step +2: ...]
...N. [Step +N: ...]

## Revised after last action
[What changed from the previous plan version. One sentence.]
```

## Mandatory Update Rule

Every sub-agent, before claiming RESOLVED, MUST:

1. READ `plan.md` (if it exists)
2. DO its work
3. UPDATE `plan.md`:
   - Move "current step" to past
   - Advance the horizon window by one
   - Write what actually happened vs what was planned
   - Timestamp the update (wall-clock, to the second)
4. THEN claim resolved

Skipping step 3 is a guardian violation. The guardian hook will block your completion.

## Correspondence

```
agent_plan/   = cooling schedule τ(t)
horizon       = how far ahead the schedule is defined
bang-bang      = instant quench (τ → 0 in one step)
plan update   = schedule revision after each measurement
```

The plan is not a promise. It is the current best estimate of the cooling path.
Every measurement (every slot resolved) revises the estimate.
