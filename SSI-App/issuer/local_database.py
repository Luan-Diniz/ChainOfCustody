import sqlite3
import asyncio

DB_FILE = "shared_data.db"

def _init_db_sync():
    """
    Internal synchronous function to create the connections table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        connection_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        subject_did TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def _add_connection_sync(connection_id: str, name: str, subject_did: str):
    """
    Internal synchronous function to add or replace a connection in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Use REPLACE INTO to either insert a new row or update an existing one.
    cursor.execute("REPLACE INTO connections (connection_id, name, subject_did) VALUES (?, ?, ?)",
                   (connection_id, name, subject_did))
    conn.commit()
    conn.close()

def _get_connection_sync(connection_id: str) -> tuple | None:
    """
    Internal synchronous function to fetch a connection's data by its ID.
    Returns a tuple (name, subject_did) or None if not found.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, subject_did FROM connections WHERE connection_id = ?", (connection_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- Asynchronous wrappers for use in the application ---

async def init_db():
    """
    Asynchronously initializes the database by running the sync function in a separate thread.
    """
    await asyncio.to_thread(_init_db_sync)

async def add_connection(connection_id: str, name: str, subject_did: str):
    """
    Asynchronously adds a connection to the database by running the sync function in a separate thread.
    """
    await asyncio.to_thread(_add_connection_sync, connection_id, name, subject_did)

async def get_connection(connection_id: str) -> tuple | None:
    """
    Asynchronously gets a connection from the database by running the sync function in a separate thread.
    """
    return await asyncio.to_thread(_get_connection_sync, connection_id)