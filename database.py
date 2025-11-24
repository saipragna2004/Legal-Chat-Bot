import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "legal_assistant.db"

def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Chat History table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_query TEXT,
            assistant_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(username):
    """Add a new user if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
    except Exception as e:
        print(f"Error adding user: {e}")
    finally:
        conn.close()

def save_interaction(username, query, response):
    """Save a chat interaction."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO chat_history (username, user_query, assistant_response)
            VALUES (?, ?, ?)
        ''', (username, query, response))
        conn.commit()
    except Exception as e:
        print(f"Error saving interaction: {e}")
    finally:
        conn.close()

def get_user_history(username):
    """Retrieve chat history for a user as a DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query(
            "SELECT user_query, assistant_response, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp ASC",
            conn,
            params=(username,)
        )
        return df
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return pd.DataFrame(columns=["user_query", "assistant_response", "timestamp"])
    finally:
        conn.close()

def clear_history(username):
    """Clear chat history for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM chat_history WHERE username = ?", (username,))
        conn.commit()
    except Exception as e:
        print(f"Error clearing history: {e}")
    finally:
        conn.close()
