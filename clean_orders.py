import csv
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_date(raw_date: str) -> str | None:
    """Convert common date formats to ISO YYYY-MM-DD, or return None if invalid."""
    cleaned = raw_date.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_amount(raw_amount: str) -> float | None:
    """Parse a positive amount as float, or return None if blank/invalid/non-positive."""
    cleaned = raw_amount.strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value <= 0:
        return None
    return round(value, 2)


def clean_rows(rows: list[dict[str, str]]) -> tuple[list[tuple], dict[str, int]]:
    """Clean raw CSV rows and return valid tuples plus a summary of skipped rows."""
    seen_rows: set[tuple] = set()
    cleaned_records: list[tuple] = []
    stats = {
        "total_read": len(rows),
        "duplicates_skipped": 0,
        "invalid_date_skipped": 0,
        "invalid_amount_skipped": 0,
        "loaded": 0,
    }

    for row in rows:
        order_id = row["order_id"].strip()
        email = row["customer_email"].strip().lower()
        iso_date = parse_date(row["order_date"])
        amount = parse_amount(row["amount_inr"])
        status = row["status"].strip().upper()

        record = (int(order_id), email, iso_date, amount, status)

        if record in seen_rows:
            stats["duplicates_skipped"] += 1
            continue
        seen_rows.add(record)

        if iso_date is None:
            stats["invalid_date_skipped"] += 1
            continue

        if amount is None:
            stats["invalid_amount_skipped"] += 1
            continue

        cleaned_records.append(record)

    stats["loaded"] = len(cleaned_records)
    return cleaned_records, stats


def load_to_sqlite(db_path: Path, records: list[tuple]) -> None:
    """Create the orders table if needed and insert cleaned records."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_email TEXT,
                order_date TEXT NOT NULL,
                amount_inr REAL NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO orders (
                order_id, customer_email, order_date, amount_inr, status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            records,
        )
        conn.commit()


def main() -> None:
    base_dir = Path(__file__).parent
    csv_path = base_dir / "Sample_orders.csv"
    db_path = base_dir / "orders.db"

    with csv_path.open(mode="r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    records, stats = clean_rows(rows)
    load_to_sqlite(db_path, records)

    print("Summary:", stats)
    with sqlite3.connect(db_path) as conn:
        for row in conn.execute("SELECT * FROM orders ORDER BY order_id"):
            print("DB row:", row)


if __name__ == "__main__":
    main()