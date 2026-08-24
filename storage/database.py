import hashlib
import json
import sqlite3

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


class DatabaseManager:
    def __init__(
        self,
        db_path="data/smartdata.db"
    ):
        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._initialize_database()

    # --------------------------------------------------
    # Connection
    # --------------------------------------------------

    def _connect(self):
        connection = sqlite3.connect(
            self.db_path
        )

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    # --------------------------------------------------
    # Database initialization
    # --------------------------------------------------

    def _initialize_database(self):
        with self._connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    product_count INTEGER NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    run_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    availability INTEGER NOT NULL,

                    PRIMARY KEY (
                        run_id,
                        url
                    ),

                    FOREIGN KEY (run_id)
                        REFERENCES runs(id)
                        ON DELETE CASCADE
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS monitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    fingerprint TEXT
                        NOT NULL
                        UNIQUE,

                    source_url TEXT NOT NULL,

                    product_selector TEXT NOT NULL,
                    name_selector TEXT NOT NULL,
                    price_selector TEXT NOT NULL,

                    availability_selector TEXT,

                    link_selector TEXT NOT NULL,

                    next_page_selector TEXT,

                    name_attribute TEXT,

                    link_attribute TEXT NOT NULL,

                    mode TEXT NOT NULL,

                    max_pages INTEGER NOT NULL,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS monitor_runs (
                    monitor_id INTEGER NOT NULL,
                    run_id INTEGER NOT NULL UNIQUE,

                    PRIMARY KEY (
                        monitor_id,
                        run_id
                    ),

                    FOREIGN KEY (monitor_id)
                        REFERENCES monitors(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (run_id)
                        REFERENCES runs(id)
                        ON DELETE CASCADE
                )
            """)

    # --------------------------------------------------
    # Monitor fingerprint
    # --------------------------------------------------

    def _build_monitor_fingerprint(
        self,
        source_url,
        config,
        mode,
        max_pages
    ):
        payload = {
            "source_url": source_url,

            "product_selector":
                config.product_selector,

            "name_selector":
                config.name_selector,

            "price_selector":
                config.price_selector,

            "availability_selector":
                config.availability_selector,

            "link_selector":
                config.link_selector,

            "next_page_selector":
                config.next_page_selector,

            "name_attribute":
                config.name_attribute,

            "link_attribute":
                config.link_attribute,

            "mode":
                mode,

            "max_pages":
                int(max_pages)
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":")
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    # --------------------------------------------------
    # Save / update monitor
    # --------------------------------------------------

    def save_monitor(
        self,
        name,
        source_url,
        config,
        mode,
        max_pages
    ):
        fingerprint = (
            self._build_monitor_fingerprint(
                source_url,
                config,
                mode,
                max_pages
            )
        )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM monitors
                WHERE fingerprint = ?
                """,
                (fingerprint,)
            )

            existing = cursor.fetchone()

            if existing is not None:
                monitor_id = existing[0]

                cursor.execute(
                    """
                    UPDATE monitors
                    SET
                        name = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        now,
                        monitor_id
                    )
                )

                return monitor_id

            cursor.execute(
                """
                INSERT INTO monitors (
                    name,
                    fingerprint,
                    source_url,

                    product_selector,
                    name_selector,
                    price_selector,
                    availability_selector,
                    link_selector,
                    next_page_selector,
                    name_attribute,
                    link_attribute,

                    mode,
                    max_pages,

                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    name,
                    fingerprint,
                    source_url,

                    config.product_selector,
                    config.name_selector,
                    config.price_selector,
                    config.availability_selector,
                    config.link_selector,
                    config.next_page_selector,
                    config.name_attribute,
                    config.link_attribute,

                    mode,
                    int(max_pages),

                    now,
                    now
                )
            )

            return cursor.lastrowid

    # --------------------------------------------------
    # Load one monitor
    # --------------------------------------------------

    def load_monitor(
        self,
        monitor_id
    ):
        with self._connect() as connection:
            df = pd.read_sql_query(
                """
                SELECT *
                FROM monitors
                WHERE id = ?
                """,
                connection,
                params=(monitor_id,)
            )

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    # --------------------------------------------------
    # List monitors
    # --------------------------------------------------

    def list_monitors(self):
        with self._connect() as connection:
            return pd.read_sql_query(
                """
                SELECT
                    id,
                    name,
                    source_url,
                    mode,
                    max_pages,
                    updated_at
                FROM monitors
                ORDER BY updated_at DESC
                """,
                connection
            )

    # --------------------------------------------------
    # Save snapshot
    # --------------------------------------------------

    def save_snapshot(
        self,
        df,
        source_url,
        monitor_id=None
    ):
        scraped_at = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO runs (
                    source_url,
                    scraped_at,
                    product_count
                )
                VALUES (?, ?, ?)
                """,
                (
                    source_url,
                    scraped_at,
                    len(df)
                )
            )

            run_id = cursor.lastrowid

            product_rows = [
                (
                    run_id,
                    row.url,
                    row.name,
                    float(row.price),
                    int(row.availability)
                )
                for row in df.itertuples(
                    index=False
                )
            ]

            cursor.executemany(
                """
                INSERT INTO products (
                    run_id,
                    url,
                    name,
                    price,
                    availability
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                product_rows
            )

            if monitor_id is not None:
                cursor.execute(
                    """
                    INSERT INTO monitor_runs (
                        monitor_id,
                        run_id
                    )
                    VALUES (?, ?)
                    """,
                    (
                        monitor_id,
                        run_id
                    )
                )

            return run_id

    # --------------------------------------------------
    # Load latest snapshot
    # --------------------------------------------------

    def load_latest_snapshot(
        self,
        source_url=None,
        monitor_id=None
    ):
        empty_df = pd.DataFrame(
            columns=[
                "name",
                "price",
                "availability",
                "url"
            ]
        )

        with self._connect() as connection:

            if monitor_id is not None:
                run = connection.execute(
                    """
                    SELECT r.id
                    FROM runs AS r

                    JOIN monitor_runs AS mr
                        ON mr.run_id = r.id

                    WHERE mr.monitor_id = ?

                    ORDER BY r.id DESC

                    LIMIT 1
                    """,
                    (monitor_id,)
                ).fetchone()

            else:
                run = connection.execute(
                    """
                    SELECT id
                    FROM runs
                    WHERE source_url = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (source_url,)
                ).fetchone()

            if run is None:
                return empty_df

            run_id = run[0]

            df = pd.read_sql_query(
                """
                SELECT
                    name,
                    price,
                    availability,
                    url
                FROM products
                WHERE run_id = ?
                """,
                connection,
                params=(run_id,)
            )

        if not df.empty:
            df["availability"] = (
                df["availability"].astype(bool)
            )

        return df

    # --------------------------------------------------
    # Run history
    # --------------------------------------------------

    def get_run_history(
        self,
        source_url=None,
        limit=10,
        monitor_id=None
    ):
        with self._connect() as connection:

            if monitor_id is not None:
                return pd.read_sql_query(
                    """
                    SELECT
                        r.id,
                        r.source_url,
                        r.scraped_at,
                        r.product_count

                    FROM runs AS r

                    JOIN monitor_runs AS mr
                        ON mr.run_id = r.id

                    WHERE mr.monitor_id = ?

                    ORDER BY r.id DESC

                    LIMIT ?
                    """,
                    connection,
                    params=(
                        monitor_id,
                        limit
                    )
                )

            return pd.read_sql_query(
                """
                SELECT
                    id,
                    source_url,
                    scraped_at,
                    product_count
                FROM runs
                WHERE source_url = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                connection,
                params=(
                    source_url,
                    limit
                )
            )