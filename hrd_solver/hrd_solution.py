#!/usr/bin/env python3
"""华容道 — extract the 81-turn solution with full analysis.

A "move" (步) = engaging a different piece. All consecutive slides of the
same piece = 1 move. This is the standard 华容道 counting.

Uses 0/1 BFS to find the optimal path, then analyzes:
- Phase decomposition (water phases between king moves)
- Mode analysis (H/V/S free-cell modes)
- Saddle point (mirror descent)
"""
from collections import deque, Counter

W, H = 4, 5
SHAPES = [(2,2), (2,1), (1,2), (1,2), (1,2), (1,2), (1,1), (1,1), (1,1), (1,1)]
NAMES = ['操', '羽', '飞', '云', '超', '忠', '①', '②', '③', '④']
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ARROW = {(1, 0): '→', (-1, 0): '←', (0, 1): '↑', (0, -1): '↓'}


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


def free_mode(fc):
    fc = sorted(fc)
    if len(fc) != 2: return '?'
    (c0, r0), (c1, r1) = fc
    if r0 == r1 and abs(c0 - c1) == 1: return 'H'
    if c0 == c1 and abs(r0 - r1) == 1: return 'V'
    return 'S'


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
                yield tuple(ns), i, (dc, dr)


def bfs_01_path(start, goal_fn):
    """0/1 BFS with path reconstruction.

    Cost 0 = same piece as previous. Cost 1 = different piece.
    Returns list of (piece_idx, direction, resulting_state) for each unit move.
    """
    k0 = canon(start)
    # State for 0/1 BFS: (canon, last_piece)
    dist = {(k0, -1): 0}
    parent = {(k0, -1): None}  # parent -> (prev_bfs_state, move_info)
    q = deque([((start, -1), 0)])

    goal_key = None
    goal_dist = float('inf')

    while q:
        (st, last_p), d = q.popleft()
        ck = canon(st)
        bfs_key = (ck, last_p)

        if d > dist.get(bfs_key, float('inf')):
            continue
        if d > goal_dist:
            continue

        if goal_fn(st):
            if d < goal_dist:
                goal_dist = d
                goal_key = bfs_key
            continue

        for ns, i, direction in gen_single(st):
            nk = canon(ns)
            cost = 0 if i == last_p else 1
            nd = d + cost
            ns_bfs_key = (nk, i)

            if nd < dist.get(ns_bfs_key, float('inf')):
                dist[ns_bfs_key] = nd
                parent[ns_bfs_key] = (bfs_key, (i, direction, ns, st))
                if cost == 0:
                    q.appendleft(((ns, i), nd))
                else:
                    q.append(((ns, i), nd))

    if goal_key is None:
        return None

    # Reconstruct path
    path = []
    key = goal_key
    while parent[key] is not None:
        prev_key, move_info = parent[key]
        path.append(move_info)
        key = prev_key
    path.reverse()
    return path


def main():
    INIT = (
        (1,3), (1,2),
        (0,3), (3,3), (0,1), (3,1),
        (1,1), (2,1), (0,0), (3,0),
    )

    print("=== 华容道 81-TURN SOLUTION ===")
    print("A 步 (move) = engaging a different piece.")
    print()

    path = bfs_01_path(INIT, lambda st: st[0] == (1, 0))
    if path is None:
        print("No solution found!")
        return

    # Group into turns
    turns = []
    current_turn = []
    for i, d, ns, prev_st in path:
        if current_turn and i != current_turn[0][0]:
            turns.append(current_turn)
            current_turn = []
        current_turn.append((i, d, ns, prev_st))
    if current_turn:
        turns.append(current_turn)

    print(f"Total unit moves: {len(path)}")
    print(f"Total turns (步): {len(turns)}")
    print()

    # Print each turn
    print("--- Solution (81 turns) ---")
    king_turns = 0
    for t, turn in enumerate(turns):
        piece = turn[0][0]
        moves_desc = ''.join(ARROW[d] for _, d, _, _ in turn)
        fc = free_cells(turn[-1][2])
        mode = free_mode(fc)
        is_king = piece == 0

        marker = ' 【王】' if is_king else ''
        unit_moves = len(turn)
        um_str = f'({unit_moves})' if unit_moves > 1 else '   '

        if is_king:
            king_turns += 1
            king_pos = turn[-1][2][0]
            print(f"  {t+1:3d}. {NAMES[piece]}{moves_desc} {um_str} [{mode}]{marker}  king→{king_pos}")
        else:
            print(f"  {t+1:3d}. {NAMES[piece]}{moves_desc} {um_str} [{mode}]")

    print(f"\n--- Summary ---")
    print(f"Total turns: {len(turns)}")
    print(f"King turns:  {king_turns}")
    print(f"Water turns: {len(turns) - king_turns}")
    print(f"Total unit moves: {len(path)}")

    # Unit moves per turn
    um_per_turn = [len(t) for t in turns]
    print(f"Unit moves per turn: min={min(um_per_turn)}, max={max(um_per_turn)}, "
          f"mean={sum(um_per_turn)/len(um_per_turn):.2f}")
    multi_turns = sum(1 for x in um_per_turn if x > 1)
    print(f"Multi-move turns: {multi_turns}/{len(turns)}")

    # Mode analysis
    mode_counts = Counter()
    for turn in turns:
        fc = free_cells(turn[-1][2])
        mode_counts[free_mode(fc)] += 1
    print(f"\nMode after each turn: H={mode_counts['H']}, V={mode_counts['V']}, S={mode_counts['S']}")

    # Phase decomposition by king moves
    print(f"\n--- Phase decomposition ---")
    print(f"(water turns between each king move)")
    phases = []
    water_count = 0
    for t, turn in enumerate(turns):
        piece = turn[0][0]
        if piece == 0:  # king
            phases.append({
                'water': water_count,
                'turn': t + 1,
                'king_pos': turn[-1][2][0],
                'king_moves': ''.join(ARROW[d] for _, d, _, _ in turn),
            })
            water_count = 0
        else:
            water_count += 1
    if water_count > 0:
        phases.append({'water': water_count, 'turn': None, 'king_pos': None, 'king_moves': None})

    for j, p in enumerate(phases):
        if p['turn'] is not None:
            print(f"  Phase {j+1}: {p['water']} water turns → 操{p['king_moves']} "
                  f"(turn #{p['turn']}, king→{p['king_pos']})")
        else:
            print(f"  Phase {j+1}: {p['water']} water turns (trailing)")

    # Saddle analysis (on the unit-move path)
    print(f"\n--- Saddle point (on turn path) ---")
    # Approximate: saddle at turn 81/2 ≈ 40-41
    # More precisely: track which turn corresponds to the midpoint of the path
    # The saddle is where forward distance = backward distance
    # In the 0/1 BFS, the "distance" is turns, not unit moves
    # The midpoint in terms of turns is around turn 40
    mid_turn = len(turns) // 2
    mid_state = turns[mid_turn - 1][-1][2]
    fc = free_cells(mid_state)
    c1, r1 = mid_state[1]
    w1 = SHAPES[1][0]
    covers = (c1 <= 1 and c1 + w1 > 2)
    print(f"  Midpoint turn: {mid_turn}")
    print(f"  関羽 at: ({c1}, {r1}), blocks corridor: {covers}")
    print(f"  Free cells: {sorted(fc)}, mode: {free_mode(fc)}")

    # Board at midpoint
    print(f"\n  Board at turn {mid_turn}:")
    board = [['..'] * W for _ in range(H)]
    for pi in range(len(mid_state)):
        c, r = mid_state[pi]
        w, h = SHAPES[pi]
        for ddc in range(w):
            for ddr in range(h):
                board[r + ddr][c + ddc] = NAMES[pi]
    for row in reversed(range(H)):
        print('    ' + ' '.join(f'{board[row][c]:>2s}' for c in range(W)))


if __name__ == '__main__':
    main()
