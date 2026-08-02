from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql

from hive_sight_advisor_api.settings import load_settings

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def _database_name(database_url: str) -> str:
    return urlparse(database_url).path.lstrip("/")


def _maintenance_database_url(database_url: str) -> str:
    return urlunparse(urlparse(database_url)._replace(path="/postgres"))


def test_database_url(database_url: str) -> str:
    database_name = _database_name(database_url)
    test_database_name = database_name.removesuffix("_dev") + "_test"
    return urlunparse(urlparse(database_url)._replace(path=f"/{test_database_name}"))


def ensure_database_exists(database_url: str) -> None:
    database_name = _database_name(database_url)
    if not database_name:
        return
    with (
        psycopg.connect(_maintenance_database_url(database_url), autocommit=True) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        if cursor.fetchone() is None:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))


def apply_migrations(database_url: str) -> None:
    ensure_database_exists(database_url)
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.name
            cursor.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
            if cursor.fetchone() is not None:
                continue
            cursor.execute(path.read_text(encoding="utf-8"))
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))


def reset_database(database_url: str) -> None:
    ensure_database_exists(database_url)
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE")
        cursor.execute("CREATE SCHEMA public")
    apply_migrations(database_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="HiveSight Advisor API database commands.")
    parser.add_argument("command", choices=("migrate", "migrate-test", "reset-test"))
    args = parser.parse_args()
    database_url = load_settings().database_url
    if args.command == "migrate":
        apply_migrations(database_url)
    elif args.command == "migrate-test":
        apply_migrations(test_database_url(database_url))
    elif args.command == "reset-test":
        reset_database(test_database_url(database_url))


if __name__ == "__main__":
    main()
