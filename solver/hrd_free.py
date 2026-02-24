#!/usr/bin/env python3
"""华容道 solver: free-cell (水) perspective.

Two free cells = 2 degrees of freedom.
Three modes: H-pair, V-pair, Separated.
A 'move' = slide one piece ONE cell in one direction (unit translation).
The free cell moves OPPOSITE (水 flows opposite to piece).

This solver verifies the minimum from first principles.
"""
from collections import deque

W, H = 4, 5  # 4 columns × 5 rows

# (name, width, height, col₀, row₀)
PIECES = [
    ('操', 2, 2, 1, 3),  # king
    ('羽', 2, 1, 1, 2),  # knife (horizontal)
    ('飞', 1, 2, 0, 3),  # general
    ('云', 1, 2, 3, 3),  # general
    ('超', 1, 2, 0, 1),  # general
    ('忠', 1, 2, 3, 1),  # general
    ('①', 1, 1, 1, 1),  # soldier
    ('②', 1, 1, 2, 1),  # soldier
    ('③', 1, 1, 0, 0),  # soldier
    ('④', 1, 1, 3, 0),  # soldier
]

NM = [p[0] for p in PIECES]
SH = [(p[1], p[2]) for p in PIECES]
INIT = tuple((p[3], p[4]) for p in PIECES)

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ARROW = {(1, 0): '→', (-1, 0): '←', (0, 1): '↑', (0, -1): '↓'}


def occupied_cells(st):
    """Return set of (col, row) occupied by pieces."""
    cells = set()
    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for dc in range(w):
            for dr in range(h):
                cells.add((c + dc, r + dr))
    return cells


def free_cells(st):
    """Return the 2 free cells."""
    occ = occupied_cells(st)
    return [(c, r) for c in range(W) for r in range(H) if (c, r) not in occ]


def free_mode(fc):
    """Classify free-cell mode: 'H', 'V', 'S' (separated)."""
    if len(fc) != 2:
        return '?'
    (c0, r0), (c1, r1) = fc
    if r0 == r1 and abs(c0 - c1) == 1:
        return 'H'
    if c0 == c1 and abs(r0 - r1) == 1:
        return 'V'
    return 'S'


def canonical(st):
    """Canonical state: sort interchangeable pieces."""
    return (st[0], st[1], tuple(sorted(st[2:6])), tuple(sorted(st[6:])))


def neighbours_single(st):
    """Single-cell moves only. Each move = one piece, one cell, one direction."""
    occ = occupied_cells(st)
    free = set((c, r) for c in range(W) for r in range(H)) - occ

    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for dc, dr in DIRS:
            nc, nr = c + dc, r + dr
            # Check bounds
            if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                continue
            # Check: all cells that piece would newly occupy must be free
            # New cells = cells at (nc, nr) with shape (w, h) MINUS cells at (c, r) with shape (w, h)
            old_cells = set()
            for ddc in range(w):
                for ddr in range(h):
                    old_cells.add((c + ddc, r + ddr))
            new_cells = set()
            for ddc in range(w):
                for ddr in range(h):
                    new_cells.add((nc + ddc, nr + ddr))
            # Cells that need to be free = new_cells - old_cells
            need_free = new_cells - old_cells
            if need_free.issubset(free):
                ns = list(st)
                ns[i] = (nc, nr)
                yield tuple(ns), i, (dc, dr)


def bfs_single(start, goal_fn):
    """BFS with single-cell moves."""
    vis = {canonical(start): None}
    q = deque([start])
    while q:
        st = q.popleft()
        if goal_fn(st):
            # Reconstruct path
            path = []
            while vis[canonical(st)] is not None:
                prev, i, d = vis[canonical(st)]
                path.append((i, d, st))
                st = prev
            path.reverse()
            return path
        for ns, i, d in neighbours_single(st):
            k = canonical(ns)
            if k not in vis:
                vis[k] = (st, i, d)
                q.append(ns)
    return None


def neighbours_multi(st):
    """Multi-cell moves. Each move = one piece, one direction, any distance."""
    occ = occupied_cells(st)
    free = set((c, r) for c in range(W) for r in range(H)) - occ

    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for dc, dr in DIRS:
            for k in range(1, max(W, H)):
                nc, nr = c + k * dc, r + k * dr
                if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                    break
                # For step k, check the frontier strip
                # Piece at (c,r) with shape (w,h) moving by k*(dc,dr)
                # The cells that need to be free are the "frontier" at distance k
                old_cells = set()
                for ddc in range(w):
                    for ddr in range(h):
                        old_cells.add((c + ddc, r + ddr))
                new_cells = set()
                for ddc in range(w):
                    for ddr in range(h):
                        new_cells.add((nc + ddc, nr + ddr))
                need_free = new_cells - old_cells
                if need_free.issubset(free):
                    ns = list(st)
                    ns[i] = (nc, nr)
                    yield tuple(ns), i, (dc, dr)
                else:
                    break  # Can't slide further


def bfs_multi(start, goal_fn):
    """BFS with multi-cell moves."""
    vis = {canonical(start): None}
    q = deque([start])
    while q:
        st = q.popleft()
        if goal_fn(st):
            path = []
            while vis[canonical(st)] is not None:
                prev, i, d = vis[canonical(st)]
                path.append((i, d, st))
                st = prev
            path.reverse()
            return path
        for ns, i, d in neighbours_multi(st):
            k = canonical(ns)
            if k not in vis:
                vis[k] = (st, i, d)
                q.append(ns)
    return None


def print_board(st):
    """Print board state."""
    board = [['..'] * W for _ in range(H)]
    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for ddc in range(w):
            for ddr in range(h):
                board[r + ddr][c + ddc] = NM[i]
    for row in reversed(range(H)):
        print('  ' + ' '.join(f'{board[row][c]:>2s}' for c in range(W)))


def main():
    print("Initial configuration:")
    print_board(INIT)
    fc = free_cells(INIT)
    print(f"\nFree cells: {fc}")
    print(f"Free-cell mode: {free_mode(fc)}")
    print(f"\nTotal occupied: {len(occupied_cells(INIT))}")
    print(f"Total free: {len(fc)}")

    goal = lambda st: st[0] == (1, 0)

    print("\n--- Single-cell BFS ---")
    path_s = bfs_single(INIT, goal)
    if path_s:
        print(f"Minimum (single-cell): {len(path_s)} moves")
        # Show free-cell mode transitions
        modes = []
        prev_st = INIT
        for i, d, st in path_s:
            fc = free_cells(st)
            m = free_mode(fc)
            modes.append(m)
        from collections import Counter
        mc = Counter(modes)
        print(f"Mode distribution: H={mc.get('H',0)}, V={mc.get('V',0)}, S={mc.get('S',0)}")

    print("\n--- Multi-cell BFS ---")
    path_m = bfs_multi(INIT, goal)
    if path_m:
        print(f"Minimum (multi-cell): {len(path_m)} moves")
        modes = []
        for i, d, st in path_m:
            fc = free_cells(st)
            m = free_mode(fc)
            modes.append(m)
        from collections import Counter
        mc = Counter(modes)
        print(f"Mode distribution: H={mc.get('H',0)}, V={mc.get('V',0)}, S={mc.get('S',0)}")

    # Count total states
    print("\n--- State space ---")
    dist = {}
    q = deque([(INIT, 0)])
    dist[canonical(INIT)] = 0
    while q:
        st, dd = q.popleft()
        for ns, _, _ in neighbours_single(st):
            k = canonical(ns)
            if k not in dist:
                dist[k] = dd + 1
                q.append((ns, dd + 1))
    print(f"Total reachable canonical states: {len(dist)}")
    print(f"Diameter (max distance from σ₀): {max(dist.values())}")


if __name__ == '__main__':
    main()
