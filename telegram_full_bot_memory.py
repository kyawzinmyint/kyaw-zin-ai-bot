#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tg_memory.db"


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(chat_id, memory_key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id_id
            ON chat_messages(chat_id, id)
            """
        )


def save_memory(chat_id, key, value):
    key = key.strip().lower()
    value = value.strip()

    if not key or not value:
        return

    timestamp = now_utc()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_memory
                (chat_id, memory_key, memory_value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, memory_key) DO UPDATE SET
                memory_value = excluded.memory_value,
                updated_at = excluded.updated_at
            """,
            (chat_id, key, value, timestamp, timestamp),
        )


def get_memories(chat_id, limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT memory_key, memory_value
            FROM user_memory
            WHERE chat_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (chat_id, limit),
        ).fetchall()

    return [(row["memory_key"], row["memory_value"]) for row in rows]


def delete_memory(chat_id, key):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM user_memory
            WHERE chat_id = ? AND memory_key = ?
            """,
            (chat_id, key.strip().lower()),
        )

    return cursor.rowcount > 0


def log_message(chat_id, role, content):
    content = content.strip()

    if not content:
        return

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, role, content, now_utc()),
        )


def get_recent_messages(chat_id, limit=12):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, limit),
        ).fetchall()

    return [(row["role"], row["content"]) for row in reversed(rows)]
def build_memory_context(chat_id):
    memories = get_memories(chat_id)

    if not memories:
        return "No saved user memories yet."

    lines = ["Saved user memories:"]
    for key, value in memories:
        lines.append("- " + key + ": " + value)

    return chr(10).join(lines)


if __name__ == "__main__":
    initialize_database()
    print("Memory database ready: " + str(DB_PATH))
