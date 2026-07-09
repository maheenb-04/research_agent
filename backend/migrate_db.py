"""
One-time migration script to add new columns to the existing reports table.
Safe to run multiple times - it checks for existing columns first and skips
them if already present. Does NOT delete or modify any existing data.

Run this once from the backend/ folder:
    python3 migrate_db.py
"""
import sqlite3

conn = sqlite3.connect("data.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(reports)")
existing_columns = {row[1] for row in cur.fetchall()}

if "raw_sources" not in existing_columns:
    cur.execute("ALTER TABLE reports ADD COLUMN raw_sources TEXT DEFAULT '[]'")
    print("Added 'raw_sources' column to reports table.")
else:
    print("'raw_sources' column already exists - skipping.")

if "tags" not in existing_columns:
    cur.execute("ALTER TABLE reports ADD COLUMN tags TEXT DEFAULT ''")
    print("Added 'tags' column to reports table.")
else:
    print("'tags' column already exists - skipping.")

# digest_subscriptions table may not exist yet on very old databases -
# only migrate its columns if the table is already there (a fresh table
# with all columns gets created automatically on next backend startup)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='digest_subscriptions'")
if cur.fetchone():
    cur.execute("PRAGMA table_info(digest_subscriptions)")
    digest_columns = {row[1] for row in cur.fetchall()}

    digest_column_defs = {
        "day_of_week": "TEXT DEFAULT 'mon'",
        "hour": "INTEGER DEFAULT 8",
        "timezone": "TEXT DEFAULT 'America/New_York'",
        "frequency": "TEXT DEFAULT 'weekly'",
        "confirmed": "BOOLEAN DEFAULT 0",
    }
    for col_name, col_def in digest_column_defs.items():
        if col_name not in digest_columns:
            cur.execute(f"ALTER TABLE digest_subscriptions ADD COLUMN {col_name} {col_def}")
            print(f"Added '{col_name}' column to digest_subscriptions table.")
        else:
            print(f"'{col_name}' column already exists on digest_subscriptions - skipping.")

    if "confirmed" not in digest_columns:
        print(
            "\nIMPORTANT: any digest subscriptions you already had are now marked "
            "unconfirmed and will PAUSE sending until re-confirmed. This is intentional - "
            "it closes a security gap where subscriptions could be created without the "
            "email owner's consent. You'll need to re-subscribe to get a fresh "
            "confirmation email for each topic you want to keep receiving.\n"
        )
else:
    print("digest_subscriptions table doesn't exist yet - it will be created automatically on next backend startup.")

conn.commit()
conn.close()

print("Migration complete. Your existing search history was not modified.")
