#!/usr/bin/env python3
"""华容道 — free-cell mode analysis.

Thinks from the space of the free (水).
Two free cells → three modes (H-pair, V-pair, Separated).
Counts: single-cell moves, multi-cell moves, and PIECE TURNS
(consecutive moves of the same piece = 1 turn).
"""
from collections import deque

W, H = 4, 5

# (name, width, height, col₀, row₀)
PIECES = [
    ('操', 2, 2, 1, 3), ('羽', 2, 1, 1, 2),
    ('飞', 1, 2, 0, 3), ('云', 1, 2, 3, 3),
    ('超', 1, 2, 0, 1), ('忠', 1, 2, 3, 1),
    ('①', 1, 1, 1, 1), ('②', 1, 1, 2, 1),
    ('③', 1, 1, 0, 0), ('④', 1, 1, 3, 0),
]
NM = [p[0] for p in PIECES]
SH = [(p[1], p[2]) for p in PIECES]
INIT = tuple((p[3], p[4]) for p in PIECES)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ARROW = {(1, 0): '→', (-1, 0): '←', (0, 1): '↑', (0, -1): '↓'}


def cells_of(st, i):
    c, r = st[i]
    w, h = SH[i]
    return frozenset((c+dc, r+dr) for dc in range(w) for dr in range(h))


def all_occupied(st):
    s = set()
    for i in range(len(st)):
        s |= cells_of(st, i)
    return s


def free(st):
    occ = all_occupied(st)
    return frozenset((c, r) for c in range(W) for r in range(H)
                     if (c, r) not in occ)


def free_mode(fc):
    fc = sorted(fc)
    if len(fc) != 2:
        return '?'
    (c0, r0), (c1, r1) = fc
    if r0 == r1 and abs(c0 - c1) == 1:
        return 'H'
    if c0 == c1 and abs(r0 - r1) == 1:
        return 'V'
    return 'S'


def canon(st):
    return (st[0], st[1], tuple(sorted(st[2:6])), tuple(sorted(st[6:])))


def gen_single(st):
    """Generate single-cell moves."""
    fr = free(st)
    for i in range(len(st)):
        c, r = st[i]
        w, h = SH[i]
        old = cells_of(st, i)
        for dc, dr in DIRS:
            nc, nr = c + dc, r + dr
            if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                continue
            new = frozenset((nc+ddc, nr+ddr) for ddc in range(w) for ddr in range(h))
            need = new - old
            if need <= fr:
                ns = list(st); ns[i] = (nc, nr)
                yield tuple(ns), i, (dc, dr)


def bfs(start, goal_fn, gen_fn):
    vis = {canon(start): None}
    q = deque([start])
    while q:
        st = q.popleft()
        if goal_fn(st):
            path = []
            while vis[canon(st)] is not None:
                prev, i, d = vis[canon(st)]
                path.append((i, d, st))
                st = prev
            path.reverse()
            return path
        for ns, i, d in gen_fn(st):
            k = canon(ns)
            if k not in vis:
                vis[k] = (st, i, d)
                q.append(ns)
    return None


def count_turns(path):
    """Count piece-turns: consecutive moves of same piece = 1 turn."""
    if not path:
        return 0
    turns = 1
    for k in range(1, len(path)):
        if path[k][0] != path[k-1][0]:
            turns += 1
    return turns


def gen_multi(st):
    """Generate multi-cell moves (slide 1..k cells, 1 direction)."""
    fr = free(st)
    for i in range(len(st)):
        c, r = st[i]
        w, h = SH[i]
        old = cells_of(st, i)
        for dc, dr in DIRS:
            for k in range(1, max(W, H)):
                nc, nr = c + k*dc, r + k*dr
                if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                    break
                new = frozenset((nc+ddc, nr+ddr) for ddc in range(w) for ddr in range(h))
                need = new - old
                if need <= fr:
                    ns = list(st); ns[i] = (nc, nr)
                    yield tuple(ns), i, (dc, dr)
                else:
                    break


def main():
    goal = lambda st: st[0] == (1, 0)

    print("=== Multi-cell BFS ===")
    path_m = bfs(INIT, goal, gen_multi)
    nm = len(path_m)
    turns_m = count_turns(path_m)
    print(f"Moves: {nm}")
    print(f"Piece-turns: {turns_m}")
    # Show grouping
    print(f"\nMulti-cell solution ({nm} moves, {turns_m} turns):")
    prev_piece = -1
    turn_num = 0
    for k, (i, d, st) in enumerate(path_m):
        fc = free(st)
        m = free_mode(fc)
        is_new_turn = (i != prev_piece)
        if is_new_turn:
            turn_num += 1
        marker = f"  T{turn_num}" if is_new_turn else "   |"
        print(f"  {k+1:3d}. {NM[i]}{ARROW[d]}  [{m}]{marker}")
        prev_piece = i

    print(f"\n=== Single-cell BFS ===")
    path = bfs(INIT, goal, gen_single)
    n = len(path)
    turns = count_turns(path)
    print(f"Moves: {n}")
    print(f"Piece-turns (consecutive same piece = 1): {turns}")

    # Mode analysis
    modes_at = []
    prev_piece = -1
    for k, (i, d, st) in enumerate(path):
        fc = free(st)
        m = free_mode(fc)
        modes_at.append(m)
        is_new_turn = (i != prev_piece)
        prev_piece = i

    from collections import Counter
    mc = Counter(modes_at)
    print(f"Mode distribution: H={mc.get('H',0)}, V={mc.get('V',0)}, S={mc.get('S',0)}")

    # Show first 30 and last 10 moves with modes and turn boundaries
    print(f"\nMove list ({n} moves, {turns} turns):")
    prev_piece = -1
    turn_num = 0
    for k, (i, d, st) in enumerate(path):
        fc = free(st)
        m = free_mode(fc)
        is_new_turn = (i != prev_piece)
        if is_new_turn:
            turn_num += 1
        marker = f"  T{turn_num}" if is_new_turn else "   |"
        if k < 40 or k >= n - 10:
            print(f"  {k+1:3d}. {NM[i]}{ARROW[d]}  [{m}]{marker}")
        elif k == 40:
            print(f"  ... ({n - 50} moves omitted) ...")
        prev_piece = i

    # Mode transitions
    transitions = Counter()
    for k in range(1, len(modes_at)):
        transitions[(modes_at[k-1], modes_at[k])] += 1
    print(f"\nMode transitions:")
    for (a, b), c in sorted(transitions.items()):
        print(f"  {a} → {b}: {c}")


if __name__ == '__main__':
    main()
