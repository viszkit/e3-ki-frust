from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.db")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_completed_attempt_is_available_in_dashboard(self) -> None:
        self.database.create_session("session-1", "statische_hilfe")
        attempt = self.database.get_or_create_attempt("session-1", 1, True)
        self.assertEqual(attempt["hint_clicks"], 0)
        self.database.increment_hint("session-1", 1)
        self.database.increment_hint("session-1", 1)
        self.database.submit_attempt("session-1", 1, 0, True, 3)

        session = self.database.get_session("session-1")
        self.assertEqual(session["current_riddle"], 2)
        self.assertEqual(self.database.dashboard_rows(), [])

    def test_final_riddle_completes_session(self) -> None:
        self.database.create_session("session-2", "keine_hilfe", "gemini", "gemini-2.5-flash-lite")
        for number in range(1, 9):
            self.database.get_or_create_attempt("session-2", number, False)
            self.database.submit_attempt("session-2", number, 0, number % 2 == 0, 2)

        session = self.database.get_session("session-2")
        self.assertIsNotNone(session["completed_at"])
        self.assertEqual(session["provider"], "gemini")
        self.assertEqual(session["model"], "gemini-2.5-flash-lite")
        self.assertEqual(session["current_riddle"], 9)
        self.assertEqual(len(self.database.dashboard_rows()), 8)
        self.assertEqual(self.database.completed_session_counts()[0]["sessions"], 1)


if __name__ == "__main__":
    unittest.main()
