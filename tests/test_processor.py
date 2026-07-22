from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from claims_processor import (
    Claim,
    ClaimError,
    InvalidPolicyError,
    is_valid_policy_number,
    process_claims,
    summarize,
)
from claims_processor.processor import parse_row


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("POL-1002003", True),
        ("ABC-0000000", True),
        ("BADPOLICY", False),
        ("POL-500600", False),  # only six digits
        ("pol-1002003", False),  # lowercase letters
        ("", False),
    ],
)
def test_is_valid_policy_number(policy: str, expected: bool) -> None:
    assert is_valid_policy_number(policy) is expected


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "claim_id": "C1",
        "policy_number": "POL-1002003",
        "claimant_name": "Alice",
        "claim_amount": "100.50",
        "claim_date": "2024-01-01",
        "status": "approved",
    }
    row.update(overrides)
    return row


def test_parse_row_valid() -> None:
    claim = parse_row(_row(), line_number=2)
    assert claim.policy_number == "POL-1002003"
    assert claim.claim_amount == Decimal("100.50")
    assert claim.status == "approved"


def test_parse_row_invalid_policy_raises() -> None:
    with pytest.raises(InvalidPolicyError):
        parse_row(_row(policy_number="BADPOLICY"), line_number=2)


def test_parse_row_invalid_amount_raises() -> None:
    with pytest.raises(ClaimError):
        parse_row(_row(claim_amount="not-a-number"), line_number=2)


def test_parse_row_negative_amount_raises() -> None:
    with pytest.raises(ClaimError):
        parse_row(_row(claim_amount="-5"), line_number=2)


def test_summarize_only_counts_approved() -> None:
    claims = [
        Claim("C1", "POL-1002003", "A", Decimal("100"), "2024-01-01", "approved"),
        Claim("C2", "POL-1002003", "A", Decimal("50"), "2024-01-02", "pending"),
        Claim("C3", "POL-1002003", "A", Decimal("25"), "2024-01-03", "approved"),
    ]
    summaries = summarize(claims)
    summary = summaries["POL-1002003"]
    assert summary.approved_total == Decimal("125")
    assert summary.approved_count == 2
    assert summary.claim_count == 3


def test_process_claims_sample(tmp_path: Path) -> None:
    csv_text = (
        "claim_id,policy_number,claimant_name,claim_amount,claim_date,status\n"
        "C1,POL-1002003,Alice,100.00,2024-01-01,approved\n"
        "C2,POL-1002003,Alice,50.00,2024-01-02,approved\n"
        "C3,BADPOLICY,Dan,900.00,2024-01-03,approved\n"
        "C4,POL-2003004,Bob,10.00,2024-01-04,denied\n"
    )
    csv_path = tmp_path / "claims.csv"
    csv_path.write_text(csv_text, encoding="utf-8")

    result = process_claims(csv_path)

    assert result.summaries["POL-1002003"].approved_total == Decimal("150.00")
    assert "POL-2003004" in result.summaries
    assert "BADPOLICY" not in result.summaries
    assert len(result.errors) == 1
    assert result.total_approved == Decimal("150.00")


def test_process_claims_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        process_claims(tmp_path / "nope.csv")
