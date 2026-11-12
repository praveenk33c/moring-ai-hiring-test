from datetime import date

from ledgerline.parsing import parse_amount, parse_date


def test_parse_amount_indian_grouping():
    assert parse_amount("1,23,456.00") == 123456.0


def test_parse_amount_rupee_symbol():
    assert parse_amount("₹ 2,480.00") == 2480.0


def test_parse_amount_passes_numbers_through():
    assert parse_amount(1789.2) == 1789.2


def test_parse_amount_empty_is_none():
    assert parse_amount("") is None


def test_parse_amount_rs_prefix_slash_suffix_and_foreign_currency():
    assert parse_amount("Rs. 1,23,456/-") == 123456.0
    assert parse_amount("Rs 45,000.50") == 45000.5
    assert parse_amount("₹ 21,600/-") == 21600.0
    assert parse_amount("$ 4,850.00") == 4850.0
    assert parse_amount("USD 2,643.20") == 2643.2


def test_parse_amount_lakh_and_crore_multipliers():
    assert parse_amount("₹1.2 lakh") == 120000.0
    assert parse_amount("Rs. 2.5 lakhs") == 250000.0
    assert parse_amount("1.5 crore") == 15000000.0
    assert parse_amount("(-0.32)") == -0.32



def test_parse_date_iso():
    assert parse_date("2026-04-25") == date(2026, 4, 25)
    assert parse_date("2026-04-03") == date(2026, 4, 3)


def test_parse_date_with_slashes():
    # Per AP Policy Section 1: Indian vendors print dates day-first (DD/MM/YYYY)
    assert parse_date("03/04/2026") == date(2026, 4, 3)
    assert parse_date("03-04-2026") == date(2026, 4, 3)
    assert parse_date("03.04.2026") == date(2026, 4, 3)


def test_parse_date_us_vendor_month_first():
    # Per AP Policy Section 1: Vendors whose country is US print dates month-first (MM/DD/YYYY)
    assert parse_date("04/10/2026", country="US") == date(2026, 4, 10)
    assert parse_date("03/04/2026", country="US") == date(2026, 3, 4)


def test_parse_date_day_first_when_unambiguous():
    assert parse_date("25/04/2026") == date(2026, 4, 25)
