#!/usr/bin/env python3
"""华容道 — water finds king, play backwards.

The water IS the agent. The king IS the goal.
Between king moves, the water rearranges.
Each "phase" = water navigates to king, king moves once.

Also: backward BFS from goal. The dual path.
Verify: forward + backward meet at saddle.
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


def free_cells(st):
    occ = set()
    for i in range(len(st)):
        occ |= cells_of(st, i)
    return frozenset((c, r) for c in range(W) for r in range(H) if (c, r) not in occ)


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


def bfs_path(start, goal_fn):
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


def bfs_dist(start):
    dist = {canon(start): 0}
    q = deque([(start, 0)])
    states = {canon(start): start}
    while q:
        st, dd = q.popleft()
        for ns, _, _ in gen_single(st):
            k = canon(ns)
            if k not in dist:
                dist[k] = dd + 1
                states[k] = ns
                q.append((ns, dd + 1))
    return dist, states


def main():
    goal = lambda st: st[0] == (1, 0)

    print("=== FORWARD: water finds king ===")
    path = bfs_path(INIT, goal)
    n = len(path)
    print(f"Total moves: {n}")

    # Phase decomposition: segment by king moves
    print(f"\n=== PHASE DECOMPOSITION ===")
    print(f"(water rearrangement moves between each king move)\n")
    phases = []
    current_phase_start = 0
    current_phase_water_moves = 0
    phase_num = 0
    for k, (i, d, st) in enumerate(path):
        if i == 0:  # king move
            phases.append({
                'water_moves': current_phase_water_moves,
                'king_move': k + 1,
                'king_dir': ARROW[d],
                'king_pos': st[0],
                'water_at_king_move': sorted(free_cells(st)),
            })
            current_phase_water_moves = 0
            phase_num += 1
        else:
            current_phase_water_moves += 1

    # Remaining water moves after last king move (shouldn't happen if last move is king)
    if current_phase_water_moves > 0:
        phases.append({
            'water_moves': current_phase_water_moves,
            'king_move': None,
            'king_dir': None,
            'king_pos': None,
            'water_at_king_move': None,
        })

    total_water = sum(p['water_moves'] for p in phases)
    total_king = sum(1 for p in phases if p['king_move'] is not None)

    for j, p in enumerate(phases):
        if p['king_move'] is not None:
            print(f"  Phase {j+1}: {p['water_moves']} water moves → 操{p['king_dir']} "
                  f"(move #{p['king_move']}, king now at {p['king_pos']}, "
                  f"water={p['water_at_king_move']})")
        else:
            print(f"  Phase {j+1}: {p['water_moves']} water moves (no king move)")

    print(f"\n  Total: {total_water} water + {total_king} king = {total_water + total_king}")
    print(f"  Phases (king moves): {total_king}")
    print(f"  Water moves per phase: {[p['water_moves'] for p in phases]}")

    # === BACKWARD BFS ===
    print(f"\n=== BACKWARD: from goal ===")
    goal_state = path[-1][2]
    print(f"Goal state: king at {goal_state[0]}")
    df, _ = bfs_dist(INIT)
    db, _ = bfs_dist(goal_state)

    # Find saddle on optimal path
    print(f"\n=== SADDLE POINT (mirror descent) ===")
    best_gap = n
    saddle_k = n // 2
    for k, (i, d, st) in enumerate(path):
        ck = canon(st)
        dp = df.get(ck, n)
        dm = db.get(ck, n)
        gap = abs(dp - dm)
        if dp + dm == n and gap < best_gap:
            best_gap = gap
            saddle_k = k
            saddle_dp = dp
            saddle_dm = dm

    print(f"Saddle at move {saddle_k + 1}")
    print(f"  d+(σ*) = {saddle_dp} (forward)")
    print(f"  d-(σ*) = {saddle_dm} (backward)")
    print(f"  d+ + d- = {saddle_dp + saddle_dm} = {n}")

    # What phase is the saddle in?
    cum = 0
    saddle_phase = 0
    for j, p in enumerate(phases):
        cum += p['water_moves'] + (1 if p['king_move'] else 0)
        if cum >= saddle_k + 1:
            saddle_phase = j + 1
            break
    print(f"  Saddle in phase {saddle_phase}")

    # Check: does knife block at saddle?
    saddle_st = path[saddle_k][2]
    c1, r1 = saddle_st[1]
    w1 = SH[1][0]
    covers = (c1 <= 1 and c1 + w1 > 2)
    print(f"  Knife blocks corridor at saddle: {covers}")
    print(f"  関羽 position at saddle: ({c1}, {r1})")

    # Print saddle board
    print(f"\n  Saddle configuration (σ*):")
    fc = free_cells(saddle_st)
    board = [['..'] * W for _ in range(H)]
    for pi in range(len(saddle_st)):
        c, r = saddle_st[pi]
        w, h = SH[pi]
        for ddc in range(w):
            for ddr in range(h):
                board[r + ddr][c + ddc] = NM[pi]
    for row in reversed(range(H)):
        print('    ' + ' '.join(f'{board[row][c]:>2s}' for c in range(W)))


if __name__ == '__main__':
    main()
