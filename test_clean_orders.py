from clean_orders import clean_rows


def test_clean_rows_removes_duplicates_and_filters_bad_amounts():
    sample = [
        {
            "order_id": "101",
            "customer_email": " alice@example.com ",
            "order_date": "2026-10-01",
            "amount_inr": "1250.50",
            "status": "COMPLETED",
        },
        {
            "order_id": "101",
            "customer_email": " alice@example.com ",
            "order_date": "2026-10-01",
            "amount_inr": "1250.50",
            "status": "COMPLETED",
        },
        {
            "order_id": "102",
            "customer_email": "bob@example.com",
            "order_date": "01/10/2026",
            "amount_inr": "",
            "status": "COMPLETED",
        },
    ]

    cleaned, stats = clean_rows(sample)

    assert len(cleaned) == 1
    assert cleaned[0] == (101, "alice@example.com", "2026-10-01", 1250.5, "COMPLETED")
    assert stats["duplicates_skipped"] == 1
    assert stats["invalid_amount_skipped"] == 1