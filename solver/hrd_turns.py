#!/usr/bin/env python3
"""华容道 — minimize PIECE TURNS, not individual moves.

A "turn" = switching to a different piece.
Moving the same piece consecutively (any direction, any distance) = 0 cost.
This is a 0/1 BFS (deque-based Dijkstra).

If this gives 81, the traditional counting is "piece turns."
"""
from collections import deque

W, H = 4, 5
SHAPES = [(2,2), (2,1), (1,2), (1,2), (1,2), (1,2), (1,1), (1,1), (1,1), (1,1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def cells_of(pos, shape):
    c, r = pos
    w, h = shape
    return frozenset((c+dc, r+dr) for dc in range(w) for dr in range(h))


def canon(st):
    return (st[0], st[1], tuple(sorted(st[2:6])), tuple(sorted(st[6:])))


def free_cells(st):
    occ = set()
    for i, pos in enumerate(st):
        occ |= cells_of(pos, SHAPES[i])
    return frozenset((c, r) for c in range(W) for r in range(H) if (c, r) not in occ)


def gen_single(st):
    """Single-cell moves. Yield (new_state, piece_index)."""
    fr = free_cells(st)
    for i, (c, r) in enumerate(st):
        w, h = SHAPES[i]
        old = cells_of((c,r), SHAPES[i])
        for dc, dr in DIRS:
            nc, nr = c + dc, r + dr
            if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                continue
            new = cells_of((nc,nr), SHAPES[i])
            need = new - old
            if need <= fr:
                ns = list(st); ns[i] = (nc, nr)
                yield tuple(ns), i


def gen_multi(st):
    """Multi-cell moves. Yield (new_state, piece_index)."""
    fr = free_cells(st)
    for i, (c, r) in enumerate(st):
        w, h = SHAPES[i]
        old = cells_of((c,r), SHAPES[i])
        for dc, dr in DIRS:
            for k in range(1, max(W, H)):
                nc, nr = c + k*dc, r + k*dr
                if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                    break
                new = cells_of((nc,nr), SHAPES[i])
                need = new - old
                if need <= fr:
                    ns = list(st); ns[i] = (nc, nr)
                    yield tuple(ns), i
                else:
                    break


def bfs_01_turns(start, goal_fn, gen_fn):
    """0/1 BFS: cost 0 = same piece, cost 1 = different piece.

    State = (canonical_positions, last_piece_moved).
    last_piece = -1 for initial state (first move always costs 1).
    """
    k0 = canon(start)
    # state = (canon_key, last_piece)
    init_state = (k0, -1)
    dist = {init_state: 0}
    q = deque([((start, -1), 0)])

    best = None
    best_d = float('inf')

    while q:
        (st, last_p), d = q.popleft()
        if d > best_d:
            continue
        if goal_fn(st):
            if d < best_d:
                best_d = d
                best = (st, d)
            continue

        ck = canon(st)
        for ns, i in gen_fn(st):
            nk = canon(ns)
            cost = 0 if i == last_p else 1
            nd = d + cost
            ns_key = (nk, i)
            if ns_key not in dist or dist[ns_key] > nd:
                dist[ns_key] = nd
                if cost == 0:
                    q.appendleft(((ns, i), nd))  # 0-cost: front
                else:
                    q.append(((ns, i), nd))       # 1-cost: back

    return best_d if best else -1


def main():
    INIT = (
        (1,3), (1,2),
        (0,3), (3,3), (0,1), (3,1),
        (1,1), (2,1), (0,0), (3,0),
    )
    goal = lambda st: st[0] == (1, 0)

    print("=== Minimum PIECE TURNS (0/1 BFS) ===")
    print("(switching to a different piece = 1 turn)")
    print()

    t_s = bfs_01_turns(INIT, goal, gen_single)
    print(f"Single-cell base, min turns: {t_s}")

    t_m = bfs_01_turns(INIT, goal, gen_multi)
    print(f"Multi-cell base, min turns:  {t_m}")

    # Also check: min moves where each "move" is all consecutive
    # actions on the same piece (any direction)
    # This is different from turns: a turn counts the switch,
    # but here we count the number of "engagements" with distinct pieces.
    # First engagement = 1. Each switch = +1.
    # So min_engagements = min_turns (same thing).
    print(f"\nFor reference:")
    print(f"  Standard BFS single-cell: 116 moves, 99 turns")
    print(f"  Standard BFS multi-cell:  90 moves, 84 turns")
    print(f"  0/1 BFS single-cell:      {t_s} turns (minimum)")
    print(f"  0/1 BFS multi-cell:       {t_m} turns (minimum)")


if __name__ == '__main__':
    main()
