from django.db import connection
from django.test import TestCase


class DatabaseConnectionTestCase(TestCase):
    """Integration test for Django database connection health."""

    def test_database_connection_is_usable(self) -> None:
        """Verify default database connection is responsive."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)
