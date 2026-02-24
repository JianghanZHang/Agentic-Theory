#!/usr/bin/env python3
"""Test multiple 华容道 configurations to find which gives 81."""
from collections import deque

W, H = 4, 5
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Standard piece shapes (always same)
# 0: 曹操 2×2, 1: 関羽 2×1h, 2-5: generals 1×2v, 6-9: soldiers 1×1
SHAPES = [(2,2), (2,1), (1,2), (1,2), (1,2), (1,2), (1,1), (1,1), (1,1), (1,1)]


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


def bfs_count(start, goal_fn, gen_fn):
    vis = {canon(start): 0}
    q = deque([(start, 0)])
    while q:
        st, d = q.popleft()
        if goal_fn(st):
            return d
        for ns, _ in gen_fn(st):
            k = canon(ns)
            if k not in vis:
                vis[k] = d + 1
                q.append((ns, d + 1))
    return -1


def valid_config(st):
    """Check no overlaps and all cells within bounds."""
    occupied = set()
    for i, (c, r) in enumerate(st):
        w, h = SHAPES[i]
        for dc in range(w):
            for dr in range(h):
                cell = (c+dc, r+dr)
                if c+dc >= W or r+dr >= H or c+dc < 0 or r+dr < 0:
                    return False
                if cell in occupied:
                    return False
                occupied.add(cell)
    return len(occupied) == 18  # 20 - 2 free


# Named configurations to test
CONFIGS = {
    # Our standard 横刀立马
    '横刀立马 (standard)': (
        (1,3), (1,2),  # 曹操, 関羽
        (0,3), (3,3), (0,1), (3,1),  # generals
        (1,1), (2,1), (0,0), (3,0),  # soldiers
    ),
    # Variant: soldiers at corners of row 0, free at center of row 1
    '横刀立马 (variant A)': (
        (1,3), (1,2),
        (0,3), (3,3), (0,1), (3,1),
        (0,0), (3,0), (1,1), (2,1),  # same soldiers, different order
    ),
    # Different: free cells at (1,1) and (2,1) instead of (1,0) and (2,0)
    '近咫尺 (free at row 1)': (
        (1,3), (1,2),
        (0,3), (3,3), (0,0), (3,0),  # generals at row 0-1
        (1,0), (2,0), (0,2), (3,2),  # soldiers
    ),
    # 兵分三路: soldiers on top
    '兵临城下': (
        (1,3), (1,0),  # 曹操 top, 関羽 bottom
        (0,3), (3,3), (0,1), (3,1),
        (1,1), (2,1), (0,0), (3,0),
    ),
    # 水泄不通: dense packing at top
    '水泄不通': (
        (1,3), (1,2),
        (0,3), (3,3), (0,1), (3,1),
        (1,0), (2,0), (0,0), (3,0),  # all soldiers in row 0
    ),
}


def main():
    goal = lambda st: st[0] == (1, 0)

    print("Testing named configurations:")
    print("=" * 60)
    for name, config in CONFIGS.items():
        st = tuple(config)
        if not valid_config(st):
            # Try different soldier placement
            print(f"\n{name}: INVALID CONFIG")
            continue

        fc = free_cells(st)
        d_s = bfs_count(st, goal, gen_single)
        d_m = bfs_count(st, goal, gen_multi)
        print(f"\n{name}:")
        print(f"  Free cells: {sorted(fc)}")
        print(f"  Single-cell: {d_s}")
        print(f"  Multi-cell:  {d_m}")
        if d_m == 81 or d_s == 81:
            print(f"  *** FOUND 81! ***")


if __name__ == '__main__':
    main()
