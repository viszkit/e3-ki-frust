"""Small SQLite persistence layer for the local experiment."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    condition TEXT NOT NULL CHECK(condition IN
                        ('keine_hilfe', 'statische_hilfe', 'ki_chat')),
                    provider TEXT NOT NULL DEFAULT 'openai' CHECK(provider IN
                        ('openai', 'gemini', 'deepseek')),
                    model TEXT NOT NULL DEFAULT 'nicht dokumentiert',
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    current_riddle INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS attempts (
                    session_id TEXT NOT NULL,
                    riddle_number INTEGER NOT NULL CHECK(riddle_number BETWEEN 1 AND 8),
                    aid_available INTEGER NOT NULL,
                    shown_at TEXT NOT NULL,
                    submitted_at TEXT,
                    selected_option INTEGER,
                    is_correct INTEGER,
                    frustration INTEGER CHECK(frustration BETWEEN 1 AND 5),
                    hint_clicks INTEGER NOT NULL DEFAULT 0,
                    ai_message_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (session_id, riddle_number),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(sessions)")}
            if "provider" not in columns:
                connection.execute(
                    "ALTER TABLE sessions ADD COLUMN provider TEXT NOT NULL DEFAULT 'openai'"
                )
            if "model" not in columns:
                connection.execute(
                    "ALTER TABLE sessions ADD COLUMN model TEXT NOT NULL DEFAULT 'nicht dokumentiert'"
                )

    def create_session(
        self,
        session_id: str,
        condition: str,
        provider: str = "openai",
        model: str = "nicht dokumentiert",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO sessions (id, condition, provider, model, started_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, condition, provider, model, now_iso()),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_or_create_attempt(
        self, session_id: str, riddle_number: int, aid_available: bool
    ) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO attempts
                    (session_id, riddle_number, aid_available, shown_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, riddle_number, int(aid_available), now_iso()),
            )
            row = connection.execute(
                """
                SELECT * FROM attempts
                WHERE session_id = ? AND riddle_number = ?
                """,
                (session_id, riddle_number),
            ).fetchone()
        return dict(row)

    def increment_hint(self, session_id: str, riddle_number: int) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE attempts SET hint_clicks = MIN(hint_clicks + 1, 3)
                WHERE session_id = ? AND riddle_number = ? AND submitted_at IS NULL
                """,
                (session_id, riddle_number),
            )

    def increment_ai_message(self, session_id: str, riddle_number: int) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE attempts SET ai_message_count = ai_message_count + 1
                WHERE session_id = ? AND riddle_number = ? AND submitted_at IS NULL
                """,
                (session_id, riddle_number),
            )

    def submit_attempt(
        self,
        session_id: str,
        riddle_number: int,
        selected_option: int,
        correct: bool,
        frustration: int,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE attempts
                SET submitted_at = ?, selected_option = ?, is_correct = ?, frustration = ?
                WHERE session_id = ? AND riddle_number = ? AND submitted_at IS NULL
                """,
                (
                    now_iso(),
                    selected_option,
                    int(correct),
                    frustration,
                    session_id,
                    riddle_number,
                ),
            )
            if riddle_number == 8:
                connection.execute(
                    "UPDATE sessions SET completed_at = ?, current_riddle = 9 WHERE id = ?",
                    (now_iso(), session_id),
                )
            else:
                connection.execute(
                    "UPDATE sessions SET current_riddle = ? WHERE id = ?",
                    (riddle_number + 1, session_id),
                )

    def dashboard_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.id AS session_id,
                    s.condition,
                    s.provider,
                    s.model,
                    a.riddle_number,
                    a.aid_available,
                    a.shown_at,
                    a.submitted_at,
                    a.is_correct,
                    a.frustration,
                    a.hint_clicks,
                    a.ai_message_count,
                    (julianday(a.submitted_at) - julianday(a.shown_at)) * 86400.0 AS duration_seconds
                FROM sessions AS s
                JOIN attempts AS a ON a.session_id = s.id
                WHERE s.completed_at IS NOT NULL AND a.submitted_at IS NOT NULL
                ORDER BY s.started_at, a.riddle_number
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def completed_session_counts(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT condition, COUNT(*) AS sessions
                FROM sessions
                WHERE completed_at IS NOT NULL
                GROUP BY condition
                """
            ).fetchall()
        return [dict(row) for row in rows]
