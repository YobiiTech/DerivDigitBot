import csv
import hashlib
import os
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = os.environ.get("DATABASE_PATH", "tick_history.db")


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 30000")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                digit INTEGER NOT NULL CHECK (digit BETWEEN 0 AND 9)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticks_symbol_id
            ON ticks(symbol, id)
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS import_batches (
                checksum TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                imported_records INTEGER NOT NULL
            )
        """)


def save_tick(timestamp, symbol, price, digit):
    digit = int(digit)

    if not 0 <= digit <= 9:
        raise ValueError("Digit must be between 0 and 9")

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO ticks (timestamp, symbol, price, digit)
            VALUES (?, ?, ?, ?)
        """, (timestamp, symbol, float(price), digit))


def load_ticks(symbol=None):
    with get_connection() as connection:
        if symbol:
            rows = connection.execute("""
                SELECT timestamp, symbol, price, digit
                FROM ticks
                WHERE symbol = ?
                ORDER BY id
            """, (symbol,)).fetchall()
        else:
            rows = connection.execute("""
                SELECT timestamp, symbol, price, digit
                FROM ticks
                ORDER BY id
            """).fetchall()

    return [dict(row) for row in rows]


def import_csv(csv_path):
    with open(csv_path, "rb") as source:
        checksum = hashlib.sha256(source.read()).hexdigest()

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT imported_records FROM import_batches WHERE checksum = ?",
            (checksum,)
        ).fetchone()

        if existing:
            return {
                "status": "already_imported",
                "imported": existing["imported_records"]
            }

        imported = 0

        with open(csv_path, newline="") as source:
            reader = csv.DictReader(source)

            required = {"timestamp", "symbol", "price", "digit"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError("CSV is missing required columns")

            for row in reader:
                digit = int(row["digit"])
                price = float(row["price"])

                if not row["timestamp"] or not row["symbol"]:
                    raise ValueError("Missing timestamp or symbol")

                if not 0 <= digit <= 9:
                    raise ValueError("Invalid digit in CSV")

                connection.execute("""
                    INSERT INTO ticks (timestamp, symbol, price, digit)
                    VALUES (?, ?, ?, ?)
                """, (row["timestamp"], row["symbol"], price, digit))

                imported += 1

        connection.execute("""
            INSERT INTO import_batches
            (checksum, source_file, imported_records)
            VALUES (?, ?, ?)
        """, (checksum, os.path.basename(csv_path), imported))

    return {
        "status": "imported",
        "imported": imported
    }


def get_tick_count(symbol=None):
    with get_connection() as connection:
        if symbol:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM ticks WHERE symbol = ?",
                (symbol,)
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM ticks"
            ).fetchone()

    return row["total"]
