#!/usr/bin/env python3
"""华容道 — grid-based BFS, NO canonicalization. Paranoid verification.

State = flat tuple of 20 ints (board[row*4 + col]).
Each cell stores piece ID (0-9) or -1 for free.
All pieces are DISTINGUISHABLE. No symmetry exploitation.
This is the slowest but most correct possible solver.
"""
from collections import deque
import time

W, H = 4, 5

# Piece shapes: (id, width, height)
SHAPES = {
    0: (2, 2),  # 曹操
    1: (2, 1),  # 関羽
    2: (1, 2),  # 张飞
    3: (1, 2),  # 赵云
    4: (1, 2),  # 马超
    5: (1, 2),  # 黄忠
    6: (1, 1),  # ①
    7: (1, 1),  # ②
    8: (1, 1),  # ③
    9: (1, 1),  # ④
}

# Initial board
# Row 0 (bottom): ③ . . ④
# Row 1: 超 ① ② 忠
# Row 2: 超 羽 羽 忠
# Row 3: 飞 操 操 云
# Row 4 (top): 飞 操 操 云
def make_init():
    b = [-1] * (W * H)
    def put(pid, c, r, w, h):
        for dc in range(w):
            for dr in range(h):
                b[(r + dr) * W + (c + dc)] = pid
    put(0, 1, 3, 2, 2)  # 曹操
    put(1, 1, 2, 2, 1)  # 関羽
    put(2, 0, 3, 1, 2)  # 张飞
    put(3, 3, 3, 1, 2)  # 赵云
    put(4, 0, 1, 1, 2)  # 马超
    put(5, 3, 1, 1, 2)  # 黄忠
    put(6, 1, 1, 1, 1)  # ①
    put(7, 2, 1, 1, 1)  # ②
    put(8, 0, 0, 1, 1)  # ③
    put(9, 3, 0, 1, 1)  # ④
    return tuple(b)


def print_board(st):
    names = {0:'操', 1:'羽', 2:'飞', 3:'云', 4:'超', 5:'忠',
             6:'①', 7:'②', 8:'③', 9:'④', -1:'..'}
    for r in range(H - 1, -1, -1):
        print('  ' + ' '.join(f'{names[st[r*W+c]]:>2s}' for c in range(W)))


def find_pieces(st):
    """Return dict: pid -> (col, row) of bottom-left corner."""
    seen = {}
    for r in range(H):
        for c in range(W):
            pid = st[r * W + c]
            if pid >= 0 and pid not in seen:
                seen[pid] = (c, r)
    return seen


def gen_moves(st):
    """Generate all single-cell moves. Yield (new_state, pid, direction)."""
    pieces = find_pieces(st)
    for pid, (c, r) in pieces.items():
        w, h = SHAPES[pid]
        for dc, dr in [(1,0), (-1,0), (0,1), (0,-1)]:
            nc, nr = c + dc, r + dr
            # Bounds check
            if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                continue
            # Find cells that need to be free
            old = set()
            for ddc in range(w):
                for ddr in range(h):
                    old.add((c + ddc, r + ddr))
            new = set()
            for ddc in range(w):
                for ddr in range(h):
                    new.add((nc + ddc, nr + ddr))
            need = new - old
            # Check all needed cells are free
            if all(st[rr * W + cc] == -1 for cc, rr in need):
                # Build new state
                freed = old - new
                ns = list(st)
                for cc, rr in freed:
                    ns[rr * W + cc] = -1
                for cc, rr in need:
                    ns[rr * W + cc] = pid
                yield tuple(ns), pid, (dc, dr)


def is_goal(st):
    """曹操 at (1,0): cells (1,0),(2,0),(1,1),(2,1) all = 0."""
    return (st[0*W+1] == 0 and st[0*W+2] == 0 and
            st[1*W+1] == 0 and st[1*W+2] == 0)


def bfs_single(start):
    vis = {start: 0}
    q = deque([(start, 0)])
    while q:
        st, d = q.popleft()
        if is_goal(st):
            return d
        for ns, _, _ in gen_moves(st):
            if ns not in vis:
                vis[ns] = d + 1
                q.append((ns, d + 1))
    return -1


def bfs_multi(start):
    """Multi-cell: BFS where each edge = one piece, one direction, any distance."""
    vis = {start: 0}
    q = deque([(start, 0)])
    while q:
        st, d = q.popleft()
        if is_goal(st):
            return d
        pieces = find_pieces(st)
        for pid, (c, r) in pieces.items():
            w, h = SHAPES[pid]
            old = set()
            for ddc in range(w):
                for ddr in range(h):
                    old.add((c + ddc, r + ddr))
            for dc, dr in [(1,0), (-1,0), (0,1), (0,-1)]:
                for k in range(1, max(W, H)):
                    nc, nr = c + k*dc, r + k*dr
                    if nc < 0 or nc + w > W or nr < 0 or nr + h > H:
                        break
                    new = set()
                    for ddc in range(w):
                        for ddr in range(h):
                            new.add((nc + ddc, nr + ddr))
                    need = new - old
                    if all(st[rr * W + cc] == -1 for cc, rr in need):
                        freed = old - new
                        ns = list(st)
                        for cc, rr in freed:
                            ns[rr * W + cc] = -1
                        for cc, rr in need:
                            ns[rr * W + cc] = pid
                        nst = tuple(ns)
                        if nst not in vis:
                            vis[nst] = d + 1
                            q.append((nst, d + 1))
                    else:
                        break
    return -1


def main():
    start = make_init()
    print("Initial board:")
    print_board(start)
    free = [i for i in range(W*H) if start[i] == -1]
    print(f"Free cells (indices): {free}")
    print(f"Free cells (col,row): {[(i%W, i//W) for i in free]}")

    t0 = time.time()
    d_single = bfs_single(start)
    t1 = time.time()
    print(f"\nSingle-cell BFS (no canonicalization): {d_single} moves")
    print(f"  Time: {t1-t0:.1f}s")

    t0 = time.time()
    d_multi = bfs_multi(start)
    t1 = time.time()
    print(f"\nMulti-cell BFS (no canonicalization): {d_multi} moves")
    print(f"  Time: {t1-t0:.1f}s")


if __name__ == '__main__':
    main()
