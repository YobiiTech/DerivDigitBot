import csv
import hashlib
import os
import sqlite3
from contextlib import contextmanager


def _database_url():
    url = os.environ.get("DATABASE_URL", "").strip()

    # Support older PostgreSQL URL prefixes.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    return url or None


def _is_postgres():
    return _database_url() is not None


@contextmanager
def get_connection():
    database_url = _database_url()

    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=10
        )
    else:
        database_path = os.environ.get(
            "DATABASE_PATH", "tick_history.db"
        )

        connection = sqlite3.connect(
            database_path,
            timeout=30
        )
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


def _execute(connection, query, parameters=()):
    if _is_postgres():
        query = query.replace("?", "%s")

    return connection.execute(query, parameters)


def init_db():
    if _is_postgres():
        ticks_schema = """
            CREATE TABLE IF NOT EXISTS ticks (
                id BIGSERIAL PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                digit SMALLINT NOT NULL CHECK (digit BETWEEN 0 AND 9)
            )
        """
    else:
        ticks_schema = """
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                digit INTEGER NOT NULL CHECK (digit BETWEEN 0 AND 9)
            )
        """

    with get_connection() as connection:
        _execute(connection, ticks_schema)

        _execute(connection, """
            CREATE INDEX IF NOT EXISTS idx_ticks_symbol_id
            ON ticks(symbol, id)
        """)

        _execute(connection, """
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
        _execute(connection, """
            INSERT INTO ticks (timestamp, symbol, price, digit)
            VALUES (?, ?, ?, ?)
        """, (timestamp, symbol, float(price), digit))


def load_ticks(symbol=None):
    with get_connection() as connection:
        if symbol:
            rows = _execute(connection, """
                SELECT timestamp, symbol, price, digit
                FROM ticks
                WHERE symbol = ?
                ORDER BY id
            """, (symbol,)).fetchall()
        else:
            rows = _execute(connection, """
                SELECT timestamp, symbol, price, digit
                FROM ticks
                ORDER BY id
            """).fetchall()

    return [dict(row) for row in rows]


def import_csv(csv_path):
    with open(csv_path, "rb") as source:
        checksum = hashlib.sha256(source.read()).hexdigest()

    with get_connection() as connection:
        existing = _execute(
            connection,
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

            def validated_rows():
                for row in reader:
                    digit = int(row["digit"])
                    price = float(row["price"])

                    if not row["timestamp"] or not row["symbol"]:
                        raise ValueError("Missing timestamp or symbol")

                    if not 0 <= digit <= 9:
                        raise ValueError("Invalid digit in CSV")

                    yield (
                        row["timestamp"],
                        row["symbol"],
                        price,
                        digit
                    )

            if _is_postgres():
                with connection.cursor().copy(
                    "COPY ticks (timestamp, symbol, price, digit) FROM STDIN"
                ) as copy:
                    for values in validated_rows():
                        copy.write_row(values)
                        imported += 1
            else:
                for values in validated_rows():
                    _execute(connection, """
                        INSERT INTO ticks (timestamp, symbol, price, digit)
                        VALUES (?, ?, ?, ?)
                    """, values)
                    imported += 1

        _execute(connection, """
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
            row = _execute(
                connection,
                "SELECT COUNT(*) AS total FROM ticks WHERE symbol = ?",
                (symbol,)
            ).fetchone()
        else:
            row = _execute(
                connection,
                "SELECT COUNT(*) AS total FROM ticks"
            ).fetchone()

    return row["total"]
