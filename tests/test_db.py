"""
Unit tests for DatabaseManager.
"""

import unittest
import tempfile
from pathlib import Path
from database.db_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test SQLite Database operations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_app.db"
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass


    def test_session_crud(self):
        # Create session
        session_id = self.db.create_session(title="Test Session")
        self.assertIsNotNone(session_id)

        # Get sessions
        sessions = self.db.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "Test Session")

        # Rename session
        self.db.rename_session(session_id, "Renamed Session")
        sessions = self.db.get_sessions()
        self.assertEqual(sessions[0]["title"], "Renamed Session")

        # Add message
        msg_id = self.db.add_message(session_id, "user", "Hello AI!")
        self.assertIsNotNone(msg_id)

        messages = self.db.get_messages(session_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Hello AI!")

        # Delete session
        self.db.delete_session(session_id)
        sessions = self.db.get_sessions()
        self.assertEqual(len(sessions), 0)


if __name__ == "__main__":
    unittest.main()
