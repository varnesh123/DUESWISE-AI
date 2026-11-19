"""Unit tests for SMS transaction parsing — UPI, card, IMPS, NEFT, ATM, transfer."""

import pytest
from app.services.transaction_parser import (
    ParsedTransaction,
    SmsParseError,
    parse_sms,
)


def _assert_parsed(txn: ParsedTransaction, amount: int, ttype: str, method: str, merchant_contains: str):
    assert txn.amount_paise == amount
    assert txn.transaction_type == ttype
    assert txn.payment_method == method
    assert merchant_contains.lower() in txn.merchant_raw.lower()
    assert txn.transaction_date is not None
    assert 0 <= txn.confidence <= 1


# ---------- UPI ----------

def test_parse_upi_debit():
    msg = "Rs.499 debited from A/c XX1234 for UPI payment to NETFLIX INDIA on 18-11-2026. UPI Ref 123456789012."
    txn = parse_sms(msg)
    _assert_parsed(txn, 49900, "debit", "upi", "NETFLIX")
    assert txn.source_reference == "123456789012"


def test_parse_upi_debit_gpay():
    msg = "Rs.1,200 debited from A/c XX1234 via GPay UPI to AMAZON IN on 20/11/2026. UPI Ref TXN123456"
    txn = parse_sms(msg)
    _assert_parsed(txn, 120000, "debit", "upi", "AMAZON")
    assert txn.payment_gateway == "gpay"


def test_parse_upi_credit():
    msg = "Rs.5000 credited to A/c XX1234 via UPI from RAVI SHARMA on 20-11-2026. UPI Ref 987654321012."
    txn = parse_sms(msg)
    _assert_parsed(txn, 500000, "credit", "upi", "RAVI SHARMA")


# ---------- Card ----------

def test_parse_card_debit():
    msg = "₹1,200 spent on your HDFC Card ending 1234 at AMAZON IN on 20/11/2026. Ref: TXN123456"
    txn = parse_sms(msg)
    _assert_parsed(txn, 120000, "debit", "card", "AMAZON")


# ---------- IMPS ----------

def test_parse_imps_credit():
    msg = "IMPS credit of Rs 50000 from SALARY ACC on 01-12-2026. Ref 9876543210."
    txn = parse_sms(msg)
    _assert_parsed(txn, 5000000, "credit", "imps", "SALARY")


# ---------- NEFT ----------

def test_parse_neft_credit():
    msg = "NEFT Credit Rs.25000 from ABC COMPANY on 15-11-2026."
    txn = parse_sms(msg)
    _assert_parsed(txn, 2500000, "credit", "neft", "ABC COMPANY")


# ---------- ATM ----------

def test_parse_atm_debit():
    msg = "ATM withdrawal of Rs.2000 at HDFC ATM on 10-11-2026. Balance: Rs.15000."
    txn = parse_sms(msg)
    _assert_parsed(txn, 200000, "debit", "atm", "HDFC ATM")


# ---------- Bank transfer ----------

def test_parse_bank_transfer_debit():
    msg = "Bank transfer of ₹5000 to FRIEND NAME on 12-11-2026. UTR: 123456789."
    txn = parse_sms(msg)
    _assert_parsed(txn, 500000, "debit", "net_banking", "FRIEND NAME")


# ---------- Errors ----------

def test_parse_empty_message():
    with pytest.raises(SmsParseError):
        parse_sms("")


def test_parse_non_transaction_message():
    msg = "Hello, this is a promotional message from your bank."
    with pytest.raises(SmsParseError):
        parse_sms(msg)
