#!/usr/bin/env python3
"""华容道 (Huarong Pass) — symbolic-level solver.

Direct translation of the mathematical formalization in §10 (huarongdao.tex).
Every Definition → named type/class. Every Theorem/Proposition → verify_*().
Stdlib only. Self-verifying: `python3 hrd_solver.py` checks all results.

Symbol mapping:
    Def 10.1  (B, P, p*, E)         → Board class
    Def 10.6  水-position            → Board.water()
    Def 10.7  H/V/S modes           → water_mode()
    Def 10.8  步 (step)              → 0/1 cost model in solve_bu()
    Def 10.9  d+, d-                → Board.bfs_bu_distances()
    Alg 1     0/1 BFS               → Board.solve_bu()
    Thm 10.4  81 步                  → verify_81bu()
    Prop 10.5 Ergodicity            → verify_ergodicity()
    Prop 10.10 Phase decomposition  → verify_phase_decomposition()
    Prop 10.11 Duality gap          → verify_duality_gap()
    Thm 10.13 Saddle                → verify_saddle()
    Prop 10.14 Mode statistics      → verify_mode_statistics()
"""
from __future__ import annotations

from collections import deque
from typing import NamedTuple

# ── Types (Definition 10.1) ──────────────────────────────────
#
# Cell      = (col, row) ∈ B = [m] × [n]
# Shape     = (width, height) of a rectangular piece
# Direction = unit vector: (±1, 0) or (0, ±1)
# Config    = tuple of k positions, one per piece
# Canon     = canonical form (interchangeable pieces sorted)
# WaterPos  = frozenset of free cells (the unordered pair {f1, f2})

Cell = tuple[int, int]
Shape = tuple[int, int]
Direction = tuple[int, int]
Config = tuple[Cell, ...]
Canon = tuple
WaterPos = frozenset

DIRS: list[Direction] = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ARROW = {(1, 0): '→', (-1, 0): '←', (0, 1): '↑', (0, -1): '↓'}


class Piece(NamedTuple):
    name: str
    shape: Shape
    is_king: bool = False


class Turn(NamedTuple):
    """One 步 (Def 10.8): maximal run of unit moves by one piece."""
    piece: int
    moves: list  # [(Direction, Config), ...]


class SolveResult(NamedTuple):
    bu: int           # minimum 步
    unit_path: list   # [(piece_idx, direction, config, prev_config), ...]
    turns: list       # [Turn, ...]


# ── Definition 10.7: Free-cell modes ─────────────────────────

def water_mode(w: WaterPos) -> str:
    """Definition 10.7: classify free-cell pair.

    H — horizontal pair: enables 2×h pieces (sword, king horizontal).
    V — vertical pair:   enables w×2 pieces (generals, king vertical).
    S — separated:       only 1×1 soldiers can move.
    """
    cells = sorted(w)
    if len(cells) != 2:
        return '?'
    (c0, r0), (c1, r1) = cells
    if r0 == r1 and abs(c0 - c1) == 1:
        return 'H'
    if c0 == c1 and abs(r0 - r1) == 1:
        return 'V'
    return 'S'


# ── Definition 10.1: Board ───────────────────────────────────

class Board:
    """Definition 10.1: 华容道 instance (B, P, p*, E).

    B = [m] × [n]:  rectangular grid (方).
    P = pieces:     rectangular blocks (圆).
    p* = king:      pieces[king_index].
    E = exit_pos:   boundary region congruent to p*.
    equiv_groups:   index ranges of interchangeable pieces.
    """

    def __init__(self, m: int, n: int, pieces: list[Piece],
                 king_index: int, exit_pos: Cell,
                 equiv_groups: list[range]):
        self.m = m
        self.n = n
        self.pieces = pieces
        self.shapes: list[Shape] = [p.shape for p in pieces]
        self.king_index = king_index
        self.exit_pos = exit_pos
        self.equiv_groups = equiv_groups
        self.all_cells = frozenset(
            (c, r) for c in range(m) for r in range(n))

    @staticmethod
    def cells_of(pos: Cell, shape: Shape) -> frozenset:
        """Cells occupied by a piece at pos with given shape."""
        c, r = pos
        w, h = shape
        return frozenset(
            (c + dc, r + dr) for dc in range(w) for dr in range(h))

    def occupied(self, sigma: Config) -> frozenset:
        """∪ p_i: union of all piece cells."""
        occ: set = set()
        for i, pos in enumerate(sigma):
            occ |= self.cells_of(pos, self.shapes[i])
        return frozenset(occ)

    def free(self, sigma: Config) -> WaterPos:
        """F = B \\ ∪ p_i  (Def 10.1): the free cells."""
        return self.all_cells - self.occupied(sigma)

    def water(self, sigma: Config) -> WaterPos:
        """Definition 10.6: W(σ) = unordered pair of free cells."""
        return self.free(sigma)

    def canon(self, sigma: Config) -> Canon:
        """Canonical form: sort interchangeable piece groups."""
        lst = list(sigma)
        parts: list = []
        prev = 0
        for grp in self.equiv_groups:
            if grp.start > prev:
                parts.extend(lst[prev:grp.start])
            parts.append(tuple(sorted(lst[grp.start:grp.stop])))
            prev = grp.stop
        if prev < len(lst):
            parts.extend(lst[prev:])
        return tuple(parts)

    def is_goal(self, sigma: Config) -> bool:
        """σ(p*) = E: king reached exit."""
        return sigma[self.king_index] == self.exit_pos

    # ── Edges of G (Def 10.1) ────────────────────────────────

    def neighbours(self, sigma: Config):
        """Unit moves: slide one piece one cell in one direction.

        Yields (σ', piece_index, direction).
        """
        fr = self.free(sigma)
        for i, pos in enumerate(sigma):
            w, h = self.shapes[i]
            old = self.cells_of(pos, self.shapes[i])
            for d in DIRS:
                dc, dr = d
                nc, nr = pos[0] + dc, pos[1] + dr
                if nc < 0 or nc + w > self.m or nr < 0 or nr + h > self.n:
                    continue
                need = self.cells_of((nc, nr), self.shapes[i]) - old
                if need <= fr:
                    ns = list(sigma)
                    ns[i] = (nc, nr)
                    yield tuple(ns), i, d

    def neighbours_multi(self, sigma: Config):
        """Multi-cell slides: one piece, one direction, any distance.

        Yields (σ', piece_index, direction).
        """
        fr = self.free(sigma)
        for i, pos in enumerate(sigma):
            w, h = self.shapes[i]
            c, r = pos
            for d in DIRS:
                dc, dr = d
                for k in range(1, max(self.m, self.n)):
                    nc, nr = c + k * dc, r + k * dr
                    if nc < 0 or nc + w > self.m or nr < 0 or nr + h > self.n:
                        break
                    if dc != 0:
                        col = c + ((w + k - 1) if dc == 1 else -k)
                        blocked = any((col, r + j) not in fr
                                      for j in range(h))
                    else:
                        row = r + ((h + k - 1) if dr == 1 else -k)
                        blocked = any((c + j, row) not in fr
                                      for j in range(w))
                    if blocked:
                        break
                    ns = list(sigma)
                    ns[i] = (nc, nr)
                    yield tuple(ns), i, d

    # ── Algorithm 1: Minimum-步 solver (0/1 BFS) ─────────────

    def solve_bu(self, sigma0: Config) -> SolveResult:
        """Algorithm 1: Minimum-步 solver via 0/1 BFS.

        Augmented state: (σ, ℓ) where ℓ = last piece moved (⊥ = -1).
        dist[(σ0, ⊥)] = 0.
        Cost: 0 if i = ℓ (same piece), 1 if i ≠ ℓ (new piece).
        Deque: pushfront for cost-0, pushback for cost-1.
        """
        k0 = self.canon(sigma0)
        dist: dict = {(k0, -1): 0}
        parent: dict = {(k0, -1): None}
        q: deque = deque([((sigma0, -1), 0)])

        goal_key = None
        goal_dist = float('inf')

        while q:
            (st, last_p), d = q.popleft()
            ck = self.canon(st)
            bfs_key = (ck, last_p)

            if d > dist.get(bfs_key, float('inf')):
                continue
            if d > goal_dist:
                continue
            if self.is_goal(st):
                if d < goal_dist:
                    goal_dist = d
                    goal_key = bfs_key
                continue

            for ns, i, direction in self.neighbours(st):
                nk = self.canon(ns)
                cost = 0 if i == last_p else 1
                nd = d + cost
                ns_key = (nk, i)
                if nd < dist.get(ns_key, float('inf')):
                    dist[ns_key] = nd
                    parent[ns_key] = (bfs_key, (i, direction, ns, st))
                    if cost == 0:
                        q.appendleft(((ns, i), nd))
                    else:
                        q.append(((ns, i), nd))

        assert goal_key is not None, "No solution"

        # Reconstruct unit-move path
        path: list = []
        key = goal_key
        while parent[key] is not None:
            prev_key, move_info = parent[key]
            path.append(move_info)
            key = prev_key
        path.reverse()

        # Group into turns (Def 10.8: 步 = maximal same-piece run)
        turns: list[Turn] = []
        current: list = []
        for i, d, ns, prev in path:
            if current and i != current[0][0]:
                turns.append(Turn(
                    piece=current[0][0],
                    moves=[(dd, ss) for _, dd, ss, _ in current]))
                current = []
            current.append((i, d, ns, prev))
        if current:
            turns.append(Turn(
                piece=current[0][0],
                moves=[(dd, ss) for _, dd, ss, _ in current]))

        return SolveResult(bu=len(turns), unit_path=path, turns=turns)

    # ── Definition 10.9: Primal-dual distances ────────────────

    def bfs_bu_distances(self, sigma0: Config):
        """Full 0/1 BFS (no early termination).

        Returns (dist_map, water_positions, n_canonical):
            dist_map:        Canon → min 步 distance
            water_positions: set of all WaterPos encountered
            n_canonical:     number of distinct canonical states
        """
        k0 = self.canon(sigma0)
        aug_dist: dict = {(k0, -1): 0}
        q: deque = deque([((sigma0, -1), 0)])

        water_positions: set = {self.water(sigma0)}
        canonical_states: set = {k0}

        while q:
            (st, last_p), d = q.popleft()
            ck = self.canon(st)
            if d > aug_dist.get((ck, last_p), float('inf')):
                continue
            for ns, i, direction in self.neighbours(st):
                nk = self.canon(ns)
                cost = 0 if i == last_p else 1
                nd = d + cost
                ns_key = (nk, i)
                if nd < aug_dist.get(ns_key, float('inf')):
                    aug_dist[ns_key] = nd
                    if cost == 0:
                        q.appendleft(((ns, i), nd))
                    else:
                        q.append(((ns, i), nd))
                    canonical_states.add(nk)
                    water_positions.add(self.water(ns))

        # Collapse: min over all last-piece values per canonical state
        dist_map: dict = {}
        for (ck, _), d in aug_dist.items():
            if ck not in dist_map or d < dist_map[ck]:
                dist_map[ck] = d

        return dist_map, water_positions, len(canonical_states)

    # ── Standard BFS (Remark 10.12: three conventions) ────────

    def bfs_unit_count(self, sigma0: Config) -> int:
        """Standard BFS, single-cell moves. Returns min unit moves (116)."""
        k0 = self.canon(sigma0)
        dist: dict = {k0: 0}
        q: deque = deque([(sigma0, 0)])
        while q:
            st, d = q.popleft()
            if self.is_goal(st):
                return d
            for ns, _, _ in self.neighbours(st):
                nk = self.canon(ns)
                if nk not in dist:
                    dist[nk] = d + 1
                    q.append((ns, d + 1))
        return -1

    def bfs_multi_count(self, sigma0: Config) -> int:
        """Standard BFS, multi-cell slides. Returns min multi moves (90)."""
        k0 = self.canon(sigma0)
        dist: dict = {k0: 0}
        q: deque = deque([(sigma0, 0)])
        while q:
            st, d = q.popleft()
            if self.is_goal(st):
                return d
            for ns, _, _ in self.neighbours_multi(st):
                nk = self.canon(ns)
                if nk not in dist:
                    dist[nk] = d + 1
                    q.append((ns, d + 1))
        return -1


# ── Standard instance ─────────────────────────────────────────

def 横刀立马() -> tuple[Board, Config]:
    """The standard 横刀立马 ('horizontal sword, standing horse') instance.

    B = [4] × [5], 10 pieces, king = 曹操 (2×2), exit at (1, 0).
    Free cells: {(1,0), (2,0)} — water mode H.
    """
    pieces = [
        Piece('曹操', (2, 2), is_king=True),   # 0: king  (王)
        Piece('关羽', (2, 1)),                  # 1: sword (刀)
        Piece('张飞', (1, 2)),                  # 2: general
        Piece('赵云', (1, 2)),                  # 3: general
        Piece('马超', (1, 2)),                  # 4: general
        Piece('黄忠', (1, 2)),                  # 5: general
        Piece('兵①', (1, 1)),                   # 6: soldier (卒)
        Piece('兵②', (1, 1)),                   # 7: soldier
        Piece('兵③', (1, 1)),                   # 8: soldier
        Piece('兵④', (1, 1)),                   # 9: soldier
    ]
    board = Board(
        m=4, n=5, pieces=pieces,
        king_index=0, exit_pos=(1, 0),
        equiv_groups=[range(2, 6), range(6, 10)],
    )
    sigma0: Config = (
        (1, 3),  # 曹操  2×2
        (1, 2),  # 关羽  2×1
        (0, 3),  # 张飞  1×2
        (3, 3),  # 赵云  1×2
        (0, 1),  # 马超  1×2
        (3, 1),  # 黄忠  1×2
        (1, 1),  # 兵①  1×1
        (2, 1),  # 兵②  1×1
        (0, 0),  # 兵③  1×1
        (3, 0),  # 兵④  1×1
    )
    return board, sigma0


# ── Verification: Theorems & Propositions ─────────────────────

def verify_81bu(board: Board, sigma0: Config, result: SolveResult):
    """Theorem 10.4: minimum 81 步, three counting conventions."""
    # (i) 81 步
    assert result.bu == 81, f"Expected 81 步, got {result.bu}"

    # (iii) 9 king + 72 水
    king = sum(1 for t in result.turns if t.piece == board.king_index)
    assert king == 9, f"King steps: {king} ≠ 9"
    assert result.bu - king == 72, f"水-steps: {result.bu - king} ≠ 72"

    # (ii) 118 unit moves, 37 multi-slide turns
    assert len(result.unit_path) == 118, \
        f"Unit moves on 步-path: {len(result.unit_path)} ≠ 118"
    multi = sum(1 for t in result.turns if len(t.moves) > 1)
    assert multi == 37, f"Multi-slide turns: {multi} ≠ 37"

    # Remark 10.12: three conventions
    u = board.bfs_unit_count(sigma0)
    m = board.bfs_multi_count(sigma0)
    assert u == 116, f"Unit-move optimal: {u} ≠ 116"
    assert m == 90, f"Multi-cell optimal: {m} ≠ 90"

    print(f"  Thm 10.4  ✓  {result.bu} 步 = {king} king + "
          f"{result.bu - king} 水; {len(result.unit_path)} unit moves; "
          f"conventions: {u}/{m}/{result.bu}")


def verify_ergodicity(board: Board, water_positions, n_canonical):
    """Proposition 10.5: all C(20,2) = 190 水-positions reachable."""
    assert len(water_positions) == 190, \
        f"水-positions: {len(water_positions)} ≠ 190"
    assert n_canonical == 25955, \
        f"|V|: {n_canonical} ≠ 25,955"
    print(f"  Prop 10.5 ✓  {len(water_positions)}/190 水-positions; "
          f"|V| = {n_canonical}")


def verify_phase_decomposition(board: Board, result: SolveResult):
    """Proposition 10.10: 9 phases separated by king steps."""
    expected_water = [25, 5, 8, 6, 3, 7, 6, 8, 4]
    expected_step  = [26, 32, 41, 48, 52, 60, 67, 76, 81]
    expected_dir   = [(1, 0), (-1, 0), (0, -1), (0, -1), (1, 0),
                      (-1, 0), (-1, 0), (0, -1), (1, 0)]
    expected_pos   = [(2, 3), (1, 3), (1, 2), (1, 1), (2, 1),
                      (1, 1), (0, 1), (0, 0), (1, 0)]

    phases: list = []
    wcount = 0
    for j, turn in enumerate(result.turns):
        if turn.piece == board.king_index:
            d0 = turn.moves[0][0]                    # direction
            king_pos = turn.moves[-1][1][board.king_index]  # final pos
            phases.append((wcount, j + 1, d0, king_pos))
            wcount = 0
        else:
            wcount += 1

    assert len(phases) == 9, f"Phases: {len(phases)} ≠ 9"
    assert [p[0] for p in phases] == expected_water, \
        f"Water: {[p[0] for p in phases]}"
    assert [p[1] for p in phases] == expected_step, \
        f"Steps: {[p[1] for p in phases]}"
    assert [p[2] for p in phases] == expected_dir, \
        f"Dirs: {[p[2] for p in phases]}"
    assert [p[3] for p in phases] == expected_pos, \
        f"Pos: {[p[3] for p in phases]}"

    print(f"  Prop 10.10 ✓  9 phases: water = {expected_water}")


def verify_duality_gap(board: Board, sigma0: Config,
                       result: SolveResult, d_plus, d_minus):
    """Proposition 10.11: d+(sj) + d-(sj) = 81 on optimal path."""
    configs = [sigma0]
    for turn in result.turns:
        configs.append(turn.moves[-1][1])

    for j, sigma in enumerate(configs):
        ck = board.canon(sigma)
        dp = d_plus.get(ck)
        dm = d_minus.get(ck)
        assert dp is not None and dm is not None, f"Step {j}: missing"
        assert dp + dm == 81, f"Step {j}: {dp} + {dm} = {dp + dm} ≠ 81"

    print(f"  Prop 10.11 ✓  d⁺ + d⁻ = 81 for all {len(configs)} "
          f"path states")


def verify_saddle(board: Board, sigma0: Config,
                  result: SolveResult, d_plus, d_minus):
    """Theorem 10.13: saddle at step 40."""
    configs = [sigma0]
    for turn in result.turns:
        configs.append(turn.moves[-1][1])

    best_j, best_gap = 0, float('inf')
    for j, sigma in enumerate(configs):
        ck = board.canon(sigma)
        dp = d_plus.get(ck, 999)
        dm = d_minus.get(ck, 999)
        gap = abs(dp - dm)
        if gap < best_gap:
            best_gap = gap
            best_j = j

    assert best_j == 40, f"Saddle at step {best_j} ≠ 40"

    sigma_star = configs[40]
    guan = sigma_star[1]
    king = sigma_star[board.king_index]
    w = board.water(sigma_star)
    mode = water_mode(w)

    assert guan == (2, 0), f"关羽 @ {guan} ≠ (2,0)"
    assert king == (1, 3), f"King @ {king} ≠ (1,3)"
    assert mode == 'H', f"Mode {mode} ≠ H"
    assert w == frozenset({(1, 2), (2, 2)}), f"水 = {sorted(w)}"

    print(f"  Thm 10.13 ✓  Saddle at step {best_j}: "
          f"关羽@{guan}, king@{king}, mode={mode}")


def verify_mode_statistics(board: Board, result: SolveResult):
    """Proposition 10.14: 27 H + 42 V + 12 S = 81."""
    counts: dict = {'H': 0, 'V': 0, 'S': 0}
    for turn in result.turns:
        sigma = turn.moves[-1][1]
        m = water_mode(board.water(sigma))
        counts[m] = counts.get(m, 0) + 1

    assert counts['H'] == 27, f"H = {counts['H']} ≠ 27"
    assert counts['V'] == 42, f"V = {counts['V']} ≠ 42"
    assert counts['S'] == 12, f"S = {counts['S']} ≠ 12"

    print(f"  Prop 10.14 ✓  H={counts['H']}, V={counts['V']}, "
          f"S={counts['S']}")


# ── Main ──────────────────────────────────────────────────────

def main():
    board, sigma0 = 横刀立马()
    print("华容道 symbolic solver — verifying §10\n")

    # Algorithm 1
    print("Alg 1: 0/1 BFS …")
    result = board.solve_bu(sigma0)
    print(f"  → {result.bu} 步, {len(result.unit_path)} unit moves\n")

    # d+ (Def 10.9)
    print("Def 10.9: d⁺ (forward) …")
    d_plus, water_pos, n_states = board.bfs_bu_distances(sigma0)

    # d- (Def 10.9)
    sigma_f = result.turns[-1].moves[-1][1]
    print("Def 10.9: d⁻ (backward) …")
    d_minus, _, _ = board.bfs_bu_distances(sigma_f)
    print()

    # Verify
    print("── Verification ──")
    verify_81bu(board, sigma0, result)
    verify_ergodicity(board, water_pos, n_states)
    verify_phase_decomposition(board, result)
    verify_duality_gap(board, sigma0, result, d_plus, d_minus)
    verify_saddle(board, sigma0, result, d_plus, d_minus)
    verify_mode_statistics(board, result)
    print("\nALL VERIFIED ✓")


if __name__ == '__main__':
    main()
