"""Initialize database with users table and sample data."""

import sqlite3
from pathlib import Path

DB_PATH = "carnatic_guru.db"


def init_database():
    """Initialize the database with users table."""
    db_file = Path(DB_PATH)
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Drop existing table if it exists (for fresh start)
    cursor.execute("DROP TABLE IF EXISTS users")

    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            avatar TEXT NOT NULL,
            color TEXT NOT NULL
        )
    """)

    # Insert sample user data
    users_data = [
        ("learner_1", "Sankar", "👨‍🎓", "#FF6B6B"),
        ("learner_2", "Vishnu", "👩‍🎓", "#4ECDC4"),
        ("learner_3", "Priya", "👨‍🎓", "#45B7D1"),
        ("admin", "Admin", "👨‍💼", "#95E1D3"),
    ]

    cursor.executemany(
        "INSERT INTO users (id, name, avatar, color) VALUES (?, ?, ?, ?)",
        users_data
    )

    conn.commit()
    print("✓ Database initialized successfully")
    print(f"✓ Created users table with {len(users_data)} users")

    # Verify data
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    print(f"✓ Users in database:")
    for row in rows:
        print(f"  - {row[1]} ({row[0]})")

    conn.close()


if __name__ == "__main__":
    init_database()
