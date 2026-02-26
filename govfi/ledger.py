"""Core data model: Project, Transaction, Ledger.

Implements the immutable append-only ledger with full observability (Obs = F).
Stdlib only — no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Transaction:
    """A single fiscal event on the ledger."""

    time: float             # t
    amount: float           # positive = disbursement, negative = return
    from_layer: int         # 0 = Gov, 1 = Company, 2 = Builder
    to_layer: int
    description: str
    verified: bool = False  # has corresponding physical verification


@dataclass
class Project:
    """A construction project with budget and layer structure."""

    name: str
    budget: float           # total budget B (亿元)
    interest_rate: float    # r (cost of capital / bond rate)
    layers: list[str] = field(default_factory=lambda: ["Gov", "Company", "Builder"])


class Ledger:
    """Immutable append-only ledger.  Obs = F (full observability).

    Every disbursement and verification is recorded with a timestamp.
    The ledger is the single source of truth for computing the loss field.
    """

    def __init__(self, project: Project) -> None:
        self.project = project
        self._txns: list[Transaction] = []

    # ── Append operations ──

    def disburse(
        self,
        t: float,
        amount: float,
        from_layer: int,
        to_layer: int,
        desc: str,
    ) -> Transaction:
        """Record a disbursement (money flows down the layers)."""
        txn = Transaction(
            time=t,
            amount=amount,
            from_layer=from_layer,
            to_layer=to_layer,
            description=desc,
        )
        self._txns.append(txn)
        return txn

    def verify(self, t: float, amount: float, desc: str) -> Transaction:
        """Record a physical verification (construction work confirmed)."""
        txn = Transaction(
            time=t,
            amount=amount,
            from_layer=2,
            to_layer=2,
            description=desc,
            verified=True,
        )
        self._txns.append(txn)
        return txn

    # ── Queries ──

    def total_disbursed(self, t: float | None = None) -> float:
        """B_disbursed(t): total money disbursed up to time t."""
        return sum(
            txn.amount
            for txn in self._txns
            if not txn.verified and (t is None or txn.time <= t)
        )

    def total_verified(self, t: float | None = None) -> float:
        """C_verified(t): total construction value verified up to time t."""
        return sum(
            txn.amount
            for txn in self._txns
            if txn.verified and (t is None or txn.time <= t)
        )

    def transactions(self) -> list[Transaction]:
        """Return all transactions (immutable view)."""
        return list(self._txns)

    def __repr__(self) -> str:
        return (
            f"Ledger({self.project.name!r}, "
            f"disbursed={self.total_disbursed():.2f}, "
            f"verified={self.total_verified():.2f}, "
            f"txns={len(self._txns)})"
        )
