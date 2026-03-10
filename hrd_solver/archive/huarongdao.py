#!/usr/bin/env python3
"""BFS solver for 华容道 (Huarong Pass), 横刀立马 configuration.

Certifies the 81-move minimum.  Bidirectional BFS locates the
saddle point for the mirror-descent interpretation.

A 'move' = slide one piece any number of cells in one direction.

Usage:
    python3 huarongdao.py            # numbered move list
    python3 huarongdao.py --latex    # LaTeX table for paper
"""
import sys
from collections import deque

W, H = 4, 5  # board: 4 columns × 5 rows

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
ARROW = {(1, 0): '→', (-1, 0): '←', (0, 1): '↑', (0, -1): '↓'}
DIRS = list(ARROW)

def key(st):
    """Canonical state: sort interchangeable pieces."""
    return (st[0], st[1], tuple(sorted(st[2:6])), tuple(sorted(st[6:])))

def grid(st):
    """Occupancy grid (flat bytearray, index = col*H + row)."""
    g = bytearray(W * H)
    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for dc in range(w):
            for dr in range(h):
                g[(c + dc) * H + (r + dr)] = 1
    return g

def neighbours(st, g):
    """Yield (new_state, piece_index, direction) for valid moves.

    A move slides one piece 1..k cells in one direction (standard counting).
    """
    for i, (c, r) in enumerate(st):
        w, h = SH[i]
        for d in DIRS:
            dc, dr = d
            for k in range(1, max(W, H)):
                nc, nr = c + k * dc, r + k * dr
                if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                    break
                # Check the k-th frontier strip
                if dc != 0:
                    col_off = (w + k - 1) if dc == 1 else -k
                    blocked = any(g[(c + col_off) * H + (r + j)]
                                  for j in range(h))
                else:
                    row_off = (h + k - 1) if dr == 1 else -k
                    blocked = any(g[(c + j) * H + (r + row_off)]
                                  for j in range(w))
                if blocked:
                    break
                ns = list(st); ns[i] = (nc, nr)
                yield tuple(ns), i, d

# ── Forward BFS ───────────────────────────────────────────
def bfs(start, goal_fn):
    vis = {key(start): None}
    q = deque([start])
    while q:
        st = q.popleft()
        if goal_fn(st):
            path = []
            while vis[key(st)] is not None:
                prev, i, d = vis[key(st)]
                path.append((i, d, st))
                st = prev
            path.reverse()
            return path
        g = grid(st)
        for ns, i, d in neighbours(st, g):
            k = key(ns)
            if k not in vis:
                vis[k] = (st, i, d)
                q.append(ns)
    return None

# ── Full BFS (distance map) ──────────────────────────────
def bfs_dist(start):
    dist = {key(start): 0}
    q = deque([(start, 0)])
    while q:
        st, dd = q.popleft()
        g = grid(st)
        for ns, _, _ in neighbours(st, g):
            k = key(ns)
            if k not in dist:
                dist[k] = dd + 1
                q.append((ns, dd + 1))
    return dist

# ── Phase detection ───────────────────────────────────────
def detect_phases(path):
    """Detect phase boundaries from the move list."""
    guan_first = None   # first move of 关羽
    guan_clear = None   # 关羽 no longer blocks corridor (cols 1-2)
    cao_descent = None  # 曹操 first moves down
    for k, (i, d, st) in enumerate(path):
        if i == 1 and guan_first is None:
            guan_first = k
        c1 = st[1][0]  # 关羽's column after this move
        w1 = SH[1][0]  # 关羽's width (2)
        # Corridor blocked if 关羽 covers both cols 1 and 2
        covers_corridor = (c1 <= 1 and c1 + w1 > 2)
        if guan_clear is None and not covers_corridor:
            guan_clear = k
        if i == 0 and d == (0, -1) and cao_descent is None:
            cao_descent = k
    return guan_first, guan_clear, cao_descent

# ── LaTeX output ──────────────────────────────────────────
def print_latex(path, saddle_idx, phases):
    guan_first, guan_clear, cao_descent = phases
    n = len(path)
    cols = 4
    rows_per_col = (n + cols - 1) // cols

    print(r'\begin{table}[H]')
    print(r'\centering\small')
    print(r'\caption{Optimal ' + str(n) + r'-move solution to 横刀立马.}')
    print(r'\label{tab:solution}')
    print(r'\begin{tabular}{@{}rl' + 'rl' * (cols - 1) + r'@{}}')
    print(r'\toprule')
    hdr = ' & '.join([r'\#', r'Move'] * cols)
    print(hdr + r' \\')
    print(r'\midrule')

    for row in range(rows_per_col):
        parts = []
        for col in range(cols):
            idx = col * rows_per_col + row
            if idx < n:
                i, d, st = path[idx]
                marker = r'\,$\star$' if idx == saddle_idx else ''
                parts.append(f'{idx+1} & {NM[i]}{ARROW[d]}{marker}')
            else:
                parts.append(' & ')
        print(' & '.join(parts) + r' \\')

    print(r'\bottomrule')
    print(r'\end{tabular}')
    print(r'\end{table}')

# ── Main ──────────────────────────────────────────────────
def main():
    path = bfs(INIT, lambda st: st[0] == (1, 0))
    assert path is not None, "No solution found"
    n = len(path)

    # Bidirectional distance analysis
    goal_state = path[-1][2]
    df = bfs_dist(INIT)
    db = bfs_dist(goal_state)

    # Saddle point on optimal path: d+ ≈ d-
    saddle_idx = n // 2
    best_gap = n
    for k in range(n):
        kk = key(path[k][2])
        dp = df.get(kk, n)
        dm = db.get(kk, n)
        if dp + dm == n and abs(dp - dm) < best_gap:
            best_gap = abs(dp - dm)
            saddle_idx = k

    phases = detect_phases(path)

    if '--latex' in sys.argv:
        print_latex(path, saddle_idx, phases)
    else:
        print(f"Minimum solution: {n} moves\n")
        gf, gc, cd = phases
        for k, (i, d, st) in enumerate(path):
            tag = ''
            if k == saddle_idx:
                tag = '  <- sigma* (saddle)'
            if k == gf:
                tag += '  [I->II: knife moves]'
            if k == gc:
                tag += '  [II->III: corridor opens]'
            if k == cd:
                tag += '  [III->IV: king descends]'
            print(f"  {k+1:3d}. {NM[i]}{ARROW[d]}{tag}")

        sk = key(path[saddle_idx][2])
        dp = df.get(sk, '?')
        dm = db.get(sk, '?')
        print(f"\nSaddle point sigma*: after move {saddle_idx+1}")
        print(f"  d+(sigma*) = {dp},  d-(sigma*) = {dm}")
        print(f"\nPhase boundaries:")
        print(f"  I->II   (knife first moves):  move {gf+1 if gf is not None else '?'}")
        print(f"  II->III (corridor opens):     move {gc+1 if gc is not None else '?'}")
        print(f"  III->IV (king descends):      move {cd+1 if cd is not None else '?'}")

        # Saddle configuration
        st = path[saddle_idx][2]
        print(f"\nSaddle configuration (sigma*):")
        board = [['.' ] * W for _ in range(H)]
        for pi, (c, r) in enumerate(st):
            w, h = SH[pi]
            for ddc in range(w):
                for ddr in range(h):
                    board[r + ddr][c + ddc] = NM[pi]
        for row in reversed(range(H)):
            print('  ' + ' '.join(f'{board[row][c]:>2s}' for c in range(W)))

if __name__ == '__main__':
    main()
