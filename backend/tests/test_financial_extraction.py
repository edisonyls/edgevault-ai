"""Regression tests for the rules-based financial extractor.

The text fixtures mirror what PyMuPDF's ``page.get_text()`` returns for real
documents: values from a table are emitted one per line (top-to-bottom,
left-to-right), not as visually-aligned rows. All data below is synthetic, but
the layout reproduces two failure modes seen on real trust-account receipts:

  * a "Total" label whose value is stacked as a tax column above the gross
    amount, which used to extract the tax ($0.00) instead of the total; and
  * a vendor whose spaced name lives only in a logo image, so the text layer
    carries the name solely in a condensed domain/email ("baysiderealty.com.au").
"""

from decimal import Decimal

from app.services.financial_extraction import (
    _detect_total,
    _match_rules,
    _pick_stacked_amount,
    extract_financials,
)

# Synthetic text layer in the shape PyMuPDF produces for a trust-account
# receipt. The company logo is an image, so the first real text line is the
# address, and the amount table is stacked: "Total" then the tax column then
# the gross amount.
RECEIPT_TEXT = """Unit 7 120 Harbour Esplanade
Docklands VIC 3008
(m) 0400000000 (w) 0390000000
baysiderealty.com.au
accounts@baysiderealty.com.au
ABN: 11 111 111 111
Trust Account Receipt
For property:
101/1 Example Street, Melbourne VIC 3000
Receipt number:
10001
Date received:
17/10/2025
Eff. paid to:
17 November 2025
On behalf of:
Sample Tenant - (TEN00001)
Owner:
Example Holdings Pty Ltd - (OWN00001)
Rent - Paid to 17/11/2025 (from 17/10/2025)
$0.00
$2,608.00
Total
$0.00
$2,608.00
Description
Included Tax
Amount
Payment method: EFT
Principal: BAYSIDE REALTY GROUP PTY LTD
Company: BAYSIDE REALTY GROUP PTY LTD
Receipted by: Account - Bayside Realty
Date processed: 19/10/2025"""

# Same vendor, but a layout where the spaced legal name never reaches the text
# layer (e.g. it is only drawn in the logo image). The name survives only in the
# condensed domain and email.
INVOICE_TEXT = RECEIPT_TEXT.replace("BAYSIDE REALTY GROUP PTY LTD", "").replace(
    "Account - Bayside Realty", "Account"
)

VENDOR_RULES = [("bayside realty", "Bayside Realty", "other")]


def _total(text: str) -> Decimal | None:
    return _detect_total(text, text.splitlines())


# --- total amount -----------------------------------------------------------


def test_stacked_tax_first_total_picks_gross_amount():
    """The receipt bug: tax stacked above the gross under a 'Total' label."""
    text = "Total\n$0.00\n$2,608.00\nDescription"
    assert _total(text) == Decimal("2608.00")


def test_stacked_total_picks_gross_regardless_of_order():
    text = "Total\n$2,608.00\n$0.00\nDescription"
    assert _total(text) == Decimal("2608.00")


def test_label_with_single_stacked_value():
    assert _total("Amount Due\n$42.50") == Decimal("42.50")


def test_inline_total_with_subtotal_and_tax():
    text = "Subtotal $100.00\nGST $10.00\nTotal $110.00"
    assert _total(text) == Decimal("110.00")


def test_subtotal_line_is_ignored_for_total():
    text = "Subtotal $100.00\nTotal $110.00"
    assert _total(text) == Decimal("110.00")


def test_no_keyword_falls_back_to_largest_amount():
    text = "Random line $5.00\nOther $9.00"
    assert _total(text) == Decimal("9.00")


def test_pick_stacked_amount_prefers_symboled_max():
    amounts = [(True, Decimal("0.00")), (True, Decimal("2608.00"))]
    assert _pick_stacked_amount(amounts) == (True, Decimal("2608.00"))


# --- vendor matching --------------------------------------------------------


def test_vendor_matches_spaced_name_in_body():
    assert _match_rules("principal: bayside realty group pty ltd", VENDOR_RULES) == (
        "Bayside Realty",
        "other",
    )


def test_vendor_matches_condensed_domain_when_spaced_name_absent():
    """The invoice bug: name survives only in 'baysiderealty.com.au'."""
    assert _match_rules("see accounts@baysiderealty.com.au", VENDOR_RULES) == (
        "Bayside Realty",
        "other",
    )


def test_single_word_keyword_does_not_collapse_match_substring():
    """A one-word keyword must not spuriously match a longer word."""
    rules = [("amazon", "Amazon", "shopping")]
    assert _match_rules("paid via amazonbasics cable", rules) is None


def test_no_rule_match_returns_none():
    assert _match_rules("totally unrelated text", VENDOR_RULES) is None


# --- end-to-end on a full receipt-shaped document ---------------------------


def test_extract_financials_on_receipt():
    result = extract_financials(RECEIPT_TEXT, VENDOR_RULES)
    assert result.vendor == "Bayside Realty"
    assert result.total_amount == Decimal("2608.00")
    assert result.document_type == "receipt"
    assert result.currency == "AUD"


def test_extract_financials_on_logo_only_invoice():
    result = extract_financials(INVOICE_TEXT, VENDOR_RULES)
    # Vendor is recovered from the condensed domain/email, not the header.
    assert result.vendor == "Bayside Realty"
    assert result.total_amount == Decimal("2608.00")
