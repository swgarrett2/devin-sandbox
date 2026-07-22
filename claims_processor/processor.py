"""Core logic for parsing and aggregating insurance claim data.

The refactored processor reads claim rows in a single streaming pass and
aggregates approved amounts per policy in O(n) time using a dictionary,
replacing the legacy O(n^2) nested-loop lookups. Invalid policy numbers and
malformed rows are validated and reported instead of being silently accepted.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_FIELDS = (
    "claim_id",
    "policy_number",
    "claimant_name",
    "claim_amount",
    "claim_date",
    "status",
)

# Policy numbers are three uppercase letters, a hyphen, then seven digits,
# e.g. "POL-1002003".
POLICY_NUMBER_RE = re.compile(r"^[A-Z]{3}-\d{7}$")

APPROVED_STATUS = "approved"


class ClaimError(Exception):
    """Base error for problems encountered while processing a claim row."""


class InvalidPolicyError(ClaimError):
    """Raised when a claim's policy number does not match the expected format."""

    def __init__(self, policy_number: str) -> None:
        self.policy_number = policy_number
        super().__init__(f"Invalid policy number: {policy_number!r}")


@dataclass(frozen=True)
class Claim:
    claim_id: str
    policy_number: str
    claimant_name: str
    claim_amount: Decimal
    claim_date: str
    status: str


@dataclass(frozen=True)
class PolicySummary:
    policy_number: str
    approved_total: Decimal
    approved_count: int
    claim_count: int


@dataclass
class ProcessingResult:
    summaries: dict[str, PolicySummary] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def total_approved(self) -> Decimal:
        return sum((s.approved_total for s in self.summaries.values()), Decimal("0"))


def is_valid_policy_number(policy_number: str) -> bool:
    """Return True if ``policy_number`` matches the expected format."""
    return bool(POLICY_NUMBER_RE.match(policy_number))


def parse_row(row: dict[str, str], line_number: int) -> Claim:
    """Validate and convert a raw CSV row into a :class:`Claim`.

    Raises :class:`ClaimError` (or :class:`InvalidPolicyError`) with a
    line-numbered message when the row cannot be parsed.
    """
    missing = [f for f in REQUIRED_FIELDS if row.get(f) is None]
    if missing:
        raise ClaimError(
            f"line {line_number}: missing field(s): {', '.join(missing)}"
        )

    policy_number = (row["policy_number"] or "").strip()
    if not is_valid_policy_number(policy_number):
        raise InvalidPolicyError(policy_number)

    raw_amount = (row["claim_amount"] or "").strip()
    try:
        claim_amount = Decimal(raw_amount)
    except InvalidOperation as exc:
        raise ClaimError(
            f"line {line_number}: invalid claim_amount {raw_amount!r}"
        ) from exc
    if claim_amount < 0:
        raise ClaimError(
            f"line {line_number}: negative claim_amount {raw_amount!r}"
        )

    return Claim(
        claim_id=(row["claim_id"] or "").strip(),
        policy_number=policy_number,
        claimant_name=(row["claimant_name"] or "").strip(),
        claim_amount=claim_amount,
        claim_date=(row["claim_date"] or "").strip(),
        status=(row["status"] or "").strip().lower(),
    )


def iter_claims(rows: Iterable[dict[str, str]]) -> Iterator[tuple[int, Claim | str]]:
    """Yield ``(line_number, Claim)`` or ``(line_number, error_message)`` per row."""
    # Row 1 is the header, so data rows start at line 2.
    for line_number, row in enumerate(rows, start=2):
        try:
            yield line_number, parse_row(row, line_number)
        except ClaimError as exc:
            yield line_number, str(exc)


def summarize(claims: Iterable[Claim]) -> dict[str, PolicySummary]:
    """Aggregate approved totals per policy in a single O(n) pass."""
    approved_total: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    approved_count: dict[str, int] = defaultdict(int)
    claim_count: dict[str, int] = defaultdict(int)

    for claim in claims:
        claim_count[claim.policy_number] += 1
        if claim.status == APPROVED_STATUS:
            approved_total[claim.policy_number] += claim.claim_amount
            approved_count[claim.policy_number] += 1

    return {
        policy: PolicySummary(
            policy_number=policy,
            approved_total=approved_total[policy],
            approved_count=approved_count[policy],
            claim_count=claim_count[policy],
        )
        for policy in claim_count
    }


def process_claims(path: str | Path) -> ProcessingResult:
    """Read a claims CSV and return per-policy summaries plus any row errors."""
    result = ProcessingResult()
    valid_claims: list[Claim] = []

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for _, item in iter_claims(reader):
            if isinstance(item, Claim):
                valid_claims.append(item)
            else:
                result.errors.append(item)

    result.summaries = summarize(valid_claims)
    return result
