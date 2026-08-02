import psycopg
import pytest
from pgvector.psycopg import register_vector

from hive_sight_advisor_api.db import apply_migrations, ensure_database_exists, test_database_url
from hive_sight_advisor_api.settings import load_settings


@pytest.fixture
def postgres_connection():
    database_url = test_database_url(load_settings().database_url)
    ensure_database_exists(database_url)
    with psycopg.connect(database_url) as reset_connection:
        with reset_connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")
        reset_connection.commit()
    apply_migrations(database_url)

    with psycopg.connect(database_url) as connection:
        register_vector(connection)
        yield connection
