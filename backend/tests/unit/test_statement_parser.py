"""Unit tests for CSV statement parsing."""

import pytest
from app.services.statement_parser import parse_csv


def test_parse_csv_basic():
    content = b"""date,merchant,amount,type,payment_method,reference
2026-11-18,NETFLIX INDIA,499.00,debit,upi,REF123
2026-11-19,AMAZON IN,1200.00,debit,card,REF456
2026-11-20,SALARY CREDIT,50000.00,credit,net_banking,REF789
"""
    result = parse_csv(content)
    assert len(result["rows"]) == 3
    assert result["errors"] == []
    assert result["rows"][0].amount_paise == 49900
    assert result["rows"][0].transaction_type == "debit"
    assert result["rows"][0].merchant == "NETFLIX INDIA"
    assert result["rows"][2].amount_paise == 5000000
    assert result["rows"][2].transaction_type == "credit"


def test_parse_csv_column_aliases():
    content = b"""Date,Description,Amt,Cr/Dr
18-11-2026,SWIGGY ORDER,299.00,dr
"""
    result = parse_csv(content)
    assert len(result["rows"]) == 1
    assert result["rows"][0].amount_paise == 29900


def test_parse_csv_missing_columns():
    content = b"name,age\nJohn,30\n"
    result = parse_csv(content)
    assert len(result["rows"]) == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_COLUMNS"


def test_parse_csv_invalid_row():
    content = b"""date,merchant,amount,type
2026-11-18,NETFLIX,notanumber,debit
"""
    result = parse_csv(content)
    assert len(result["rows"]) == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row"] == 2


def test_parse_csv_empty():
    result = parse_csv(b"")
    assert len(result["rows"]) == 0
    assert len(result["errors"]) == 1
