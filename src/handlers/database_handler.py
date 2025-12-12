"""Database handler for persistent book storage."""

import sqlite3
import os
from pathlib import Path


class DatabaseHandler:
    """Handles SQLite database operations for book persistence."""

    def __init__(self, db_path: str = None):
        """
        Initialize database handler.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Store database in user's home directory
            home_dir = Path.home()
            app_dir = home_dir / ".book_library"
            app_dir.mkdir(exist_ok=True)
            db_path = app_dir / "library.db"

        self.db_path = str(db_path)
        print(f"[DEBUG] Database path: {self.db_path}")
        print(f"[DEBUG] Database exists: {os.path.exists(self.db_path)}")
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists and has correct schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
        table_exists = cursor.fetchone()

        if table_exists:
            # Check if the table has the correct columns
            cursor.execute("PRAGMA table_info(books)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"[DEBUG] Existing table columns: {columns}")

            # If schema is wrong, drop and recreate
            required_columns = {'id', 'name', 'path', 'ext', 'added_date'}
            if not required_columns.issubset(set(columns)):
                print(f"[DEBUG] Schema mismatch! Dropping and recreating table...")
                cursor.execute('DROP TABLE IF EXISTS books')
                conn.commit()

        # Create table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                ext TEXT NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print(f"[DEBUG] Database initialized")

    def add_book(self, name: str, path: str, ext: str) -> bool:
        """
        Add a book to the database.

        Args:
            name: Book name/title
            path: Full file path
            ext: File extension (pdf, txt, etc.)

        Returns:
            True if added successfully, False if already exists or error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'INSERT INTO books (name, path, ext) VALUES (?, ?, ?)',
                (name, path, ext)
            )

            conn.commit()
            rows_added = cursor.rowcount
            conn.close()

            print(f"[DEBUG] Book added to database: {name}")
            print(f"[DEBUG] Rows affected: {rows_added}")

            # Verify the book was actually saved
            self._verify_book_saved(path)

            return True
        except sqlite3.IntegrityError:
            # Book already exists
            print(f"[DEBUG] Book already exists in database: {name}")
            return False
        except Exception as e:
            print(f"[ERROR] Error adding book to database: {e}")
            return False

    def _verify_book_saved(self, path: str):
        """Verify a book was actually saved to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books WHERE path = ?', (path,))
            result = cursor.fetchone()
            conn.close()

            if result:
                print(f"[DEBUG] ✓ Verified book is in database: {result}")
            else:
                print(f"[ERROR] ✗ Book NOT found in database after adding!")
        except Exception as e:
            print(f"[ERROR] Error verifying book: {e}")

    def remove_book(self, path: str) -> bool:
        """
        Remove a book from the database.

        Args:
            path: Full file path of the book to remove

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM books WHERE path = ?', (path,))

            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()

            print(f"[DEBUG] Book removed from database. Rows affected: {rows_affected}")
            return rows_affected > 0
        except Exception as e:
            print(f"[ERROR] Error removing book from database: {e}")
            return False

    def get_all_books(self) -> list[dict]:
        """
        Retrieve all books from the database.

        Returns:
            List of dictionaries containing book data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT name, path, ext FROM books ORDER BY added_date DESC')
            rows = cursor.fetchall()

            conn.close()

            print(f"[DEBUG] Retrieved {len(rows)} books from database")

            books = []
            for row in rows:
                print(f"[DEBUG] Checking book: {row[0]} at {row[1]}")
                # Check if file still exists
                if os.path.exists(row[1]):
                    books.append({
                        'name': row[0],
                        'path': row[1],
                        'ext': row[2]
                    })
                    print(f"[DEBUG] ✓ File exists, added to list")
                else:
                    # Remove from database if file no longer exists
                    print(f"[DEBUG] ✗ File no longer exists, removing from database")
                    self.remove_book(row[1])

            print(f"[DEBUG] Returning {len(books)} valid books")
            return books
        except Exception as e:
            print(f"[ERROR] Error retrieving books from database: {e}")
            import traceback
            traceback.print_exc()
            return []

    def book_exists(self, path: str) -> bool:
        """
        Check if a book already exists in the database.

        Args:
            path: Full file path to check

        Returns:
            True if book exists, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM books WHERE path = ?', (path,))
            count = cursor.fetchone()[0]

            conn.close()

            print(f"[DEBUG] Book exists check for {path}: {count > 0}")
            return count > 0
        except Exception as e:
            print(f"[ERROR] Error checking book existence: {e}")
            return False

    def clear_all_books(self):
        """Remove all books from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM books')

            conn.commit()
            conn.close()
            print(f"[DEBUG] All books cleared from database")
        except Exception as e:
            print(f"[ERROR] Error clearing database: {e}")

    def print_all_books_raw(self):
        """Debug method to print all books in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books')
            rows = cursor.fetchall()
            conn.close()

            print(f"\n[DEBUG] === RAW DATABASE CONTENTS ===")
            print(f"[DEBUG] Total books in database: {len(rows)}")
            for row in rows:
                print(f"[DEBUG] {row}")
            print(f"[DEBUG] ================================\n")
        except Exception as e:
            print(f"[ERROR] Error printing database contents: {e}")