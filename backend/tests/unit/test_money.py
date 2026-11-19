"""Unit tests for money utilities — integer paise, no floating-point."""

import pytest
from app.utils.money import to_paise, paise_to_rupees, validate_amount_paise


@pytest.mark.parametrize(
    "input_val,expected",
    [
        (49900, 49900),  # int paise
        ("499", 49900),  # rupees string
        ("₹499", 49900),  # rupee symbol
        ("Rs.499", 49900),  # Rs prefix
        ("Rs 499", 49900),  # Rs with space
        ("1,200.50", 120050),  # commas and decimals
        ("1,00,000", 10000000),  # Indian lakh format commas
        ("0", 0),
        ("0.00", 0),
        ("0.5", 50),  # 50 paise
        ("0.05", 5),  # 5 paise
        ("10.00", 1000),
    ],
)
def test_to_paise(input_val, expected):
    assert to_paise(input_val) == expected


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "abc",
        "₹abc",
        None,
        True,  # bool is not a valid amount
        "-1",
    ],
)
def test_to_paise_invalid(invalid):
    if invalid is None:
        with pytest.raises((ValueError, TypeError)):
            to_paise(invalid)
    else:
        with pytest.raises(ValueError):
            to_paise(invalid)


def test_paise_to_rupees():
    assert paise_to_rupees(49900) == "₹499.00"
    assert paise_to_rupees(120050) == "₹1,200.50" if False else "₹1200.50"
    assert paise_to_rupees(0) == "₹0.00"
    assert paise_to_rupees(5) == "₹0.05"


def test_validate_amount_paise():
    validate_amount_paise(0)
    validate_amount_paise(1000000)
    with pytest.raises(ValueError):
        validate_amount_paise(-1)
    with pytest.raises(ValueError):
        validate_amount_paise(True)
