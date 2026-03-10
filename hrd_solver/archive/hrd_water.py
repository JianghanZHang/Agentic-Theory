#!/usr/bin/env python3
"""华容道 — from the water's perspective.

The pieces ARE the board. The water (2 free cells) ARE the pieces.
The knife = the water configuration that blocks the king's freedom.
The cut = a legitimate combination of water positions.

What does the state space look like from water's eyes?
"""
from collections import deque

W, H = 4, 5

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


def free_cells(st):
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
    fr = free_cells(st)
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


def bfs_full(start, goal_fn):
    """BFS returning path."""
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
        for ns, i, d in gen_single(st):
            k = canon(ns)
            if k not in vis:
                vis[k] = (st, i, d)
                q.append(ns)
    return None


def main():
    goal = lambda st: st[0] == (1, 0)
    path = bfs_full(INIT, goal)
    n = len(path)
    print(f"Single-cell moves: {n}")

    # === WATER PERSPECTIVE ===
    print(f"\n=== THE WATER'S VIEW ===")
    print(f"Water = 2 free cells. Pieces = the board.\n")

    # Track water state through solution
    water_states = []
    # Initial water state
    fc0 = free_cells(INIT)
    water_states.append(fc0)

    king_free_count = 0  # How many moves does the king have freedom?

    for k, (i, d, st) in enumerate(path):
        fc = free_cells(st)
        water_states.append(fc)

    # How many DISTINCT water positions visited?
    unique_water = set(water_states)
    print(f"Total moves: {n}")
    print(f"Distinct water positions visited: {len(unique_water)}")

    # Water transitions: how often does the water position CHANGE?
    water_changes = 0
    for k in range(1, len(water_states)):
        if water_states[k] != water_states[k-1]:
            water_changes += 1
    print(f"Water position changes: {water_changes} (should = {n}, every move changes water)")

    # THE KEY QUESTION: King's freedom at each step
    print(f"\n=== KING'S FREEDOM (刀 = free of king) ===")
    prev_st = INIT
    king_moves_available = []
    knife_blocks = []
    for k, (i, d, st) in enumerate(path):
        # How many moves does 曹操 have at this configuration?
        king_options = 0
        fc = free_cells(st)
        c0, r0 = st[0]  # king position
        w0, h0 = SH[0]  # (2, 2)
        old_king = cells_of(st, 0)
        for dc, dr in DIRS:
            nc, nr = c0 + dc, r0 + dr
            if nc < 0 or nc + w0 > W or nr < 0 or nr + h0 > H:
                continue
            new_king = frozenset((nc+ddc, nr+ddr) for ddc in range(w0) for ddr in range(h0))
            need = new_king - old_king
            if need <= fc:
                king_options += 1
        king_moves_available.append(king_options)

        # Does 関羽 block the corridor?
        c1, r1 = st[1]  # 関羽 position
        w1 = SH[1][0]
        covers_corridor = (c1 <= 1 and c1 + w1 > 2)
        knife_blocks.append(covers_corridor)

    # Print summary
    free_king = sum(1 for x in king_moves_available if x > 0)
    blocked_king = sum(1 for x in king_moves_available if x == 0)
    knife_active = sum(knife_blocks)
    knife_clear = sum(1 for x in knife_blocks if not x)
    print(f"King has ≥1 move available: {free_king}/{n} steps")
    print(f"King has 0 moves (stuck): {blocked_king}/{n} steps")
    print(f"Knife (関羽) blocks corridor: {knife_active}/{n} steps")
    print(f"Knife cleared: {knife_clear}/{n} steps")

    # When does king freedom first appear?
    first_free = None
    for k, x in enumerate(king_moves_available):
        if x > 0:
            first_free = k
            break
    if first_free is not None:
        print(f"\nKing first has freedom at move {first_free+1}")

    # When does knife clear?
    first_clear = None
    for k, x in enumerate(knife_blocks):
        if not x:
            first_clear = k
            break
    if first_clear is not None:
        print(f"Knife first clears at move {first_clear+1}")

    # Water mode analysis
    print(f"\n=== WATER MODES ===")
    mode_counts = {'H': 0, 'V': 0, 'S': 0}
    for ws in water_states:
        m = free_mode(ws)
        if m in mode_counts:
            mode_counts[m] += 1
    total = sum(mode_counts.values())
    print(f"H-pair: {mode_counts['H']}/{total} ({100*mode_counts['H']/total:.0f}%)")
    print(f"V-pair: {mode_counts['V']}/{total} ({100*mode_counts['V']/total:.0f}%)")
    print(f"Separated: {mode_counts['S']}/{total} ({100*mode_counts['S']/total:.0f}%)")

    # The dual: can water REACH any position?
    # BFS on water space (but water doesn't move independently — it's coupled to pieces)
    # Instead: count how many of the C(20,2)=190 possible water positions are ever reachable
    print(f"\n=== WATER REACHABILITY ===")
    dist = {}
    q = deque([(INIT, 0)])
    dist[canon(INIT)] = 0
    all_water_positions = set()
    all_water_positions.add(free_cells(INIT))
    while q:
        st, dd = q.popleft()
        for ns, _, _ in gen_single(st):
            k = canon(ns)
            if k not in dist:
                dist[k] = dd + 1
                q.append((ns, dd + 1))
                all_water_positions.add(free_cells(ns))
    print(f"Total canonical states: {len(dist)}")
    print(f"Total distinct water positions ever occupied: {len(all_water_positions)}")
    print(f"Out of C(20,2) = {20*19//2} possible pairs")

    # CRITICAL: what is the water state when king moves?
    print(f"\n=== WHEN DOES THE KING MOVE? ===")
    king_move_modes = []
    for k, (i, d, st) in enumerate(path):
        if i == 0:  # king moves
            fc = free_cells(st)
            m = free_mode(fc)
            king_move_modes.append((k+1, ARROW[d], m))
            print(f"  Move {k+1}: 操{ARROW[d]}  water mode={m}  water={sorted(fc)}")

    from collections import Counter
    kmc = Counter(m for _, _, m in king_move_modes)
    print(f"King moves by water mode: {dict(kmc)}")
    print(f"Total king moves: {len(king_move_modes)}")


if __name__ == '__main__':
    main()
