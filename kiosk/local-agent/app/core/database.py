import sqlite3
from contextlib import contextmanager

from app.core.config import settings


def initialize_database() -> None:
    settings.database_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(settings.database_file) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                extension TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS upload_sessions (
                id TEXT PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                document_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(document_id)
                    REFERENCES documents(id)
            )
            """
        )

        connection.commit()


@contextmanager
def get_connection():
    connection = sqlite3.connect(settings.database_file)

    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()