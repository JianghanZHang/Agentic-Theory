# Nucleation Runtime

This repo runs under agent-nucleation V-protocol.

## Role: Grade 0-1 Executor

You are an executor. Your controller is in another session.

## How to operate

1. Read `agent_plan/plan.md`. If it has objectives, execute them using `/V`.
2. If no plan exists, ask the user for T (target) and B (basis), then run `/V(T,B)`.
3. Write cascade logs to `agent_workspace/`.
4. Write completion markers to `agent_table/markers/`.
5. Update `agent_plan/plan.md` after each resolved slot (if horizon > 0).

## Guardian Invariants

1. **Time-aligned** — all timestamps real wall-clock ISO 8601, to the second.
2. **No self-deception** — no claim without evidence.
3. **Nothing lost** — all work recorded.

## Communication

Controller writes objectives to `agent_plan/plan.md`.
You execute and write results to `agent_table/markers/`.
The filesystem is the channel.
