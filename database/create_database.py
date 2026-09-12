import os
import sys

# Add the project root folder to Python's search path,
# so "database.db" can always be found, regardless of
# how this script is run.
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.db import get_connection

connection = get_connection()

cursor = connection.cursor()

# Admins Table
# Delete old admins table (safe - no admin rows exist yet anyway)
cursor.execute("DROP TABLE IF EXISTS admins")

cursor.execute("""
CREATE TABLE admins(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    email TEXT NOT NULL,

    password TEXT NOT NULL,

    profile_pic TEXT,

    created_at TEXT

)
""")

# Events Table
# Delete old events table
cursor.execute("DROP TABLE IF EXISTS events")

# Create new events table
cursor.execute("""
CREATE TABLE events(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_name TEXT NOT NULL,

    event_date TEXT,

    organizer TEXT,

    venue TEXT,

    description TEXT,

    template_name TEXT,

    status TEXT,

    created_at TEXT

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participants(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_id INTEGER NOT NULL,

    name TEXT NOT NULL,

    email TEXT NOT NULL,

    college TEXT,

    department TEXT,

    position TEXT,

    created_at TEXT,

    FOREIGN KEY(event_id) REFERENCES events(id)

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS certificates(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    participant_id INTEGER NOT NULL,

    certificate_id TEXT UNIQUE,

    file_name TEXT,

    issue_date TEXT,

    qr_code TEXT,

    status TEXT,

    FOREIGN KEY(participant_id) REFERENCES participants(id)

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS template_fields(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_id INTEGER NOT NULL,

    field_name TEXT NOT NULL,

    x REAL NOT NULL,

    y REAL NOT NULL,

    font_size INTEGER DEFAULT 32,

    font_family TEXT DEFAULT 'Poppins',

    font_color TEXT DEFAULT '#000000',

    font_weight TEXT DEFAULT 'bold',

    text_align TEXT DEFAULT 'center',

    rotation REAL DEFAULT 0,

    FOREIGN KEY(event_id)
        REFERENCES events(id)

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS email_logs(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    participant_id INTEGER NOT NULL,

    email_status TEXT,

    error_message TEXT,

    sent_at TEXT,

    FOREIGN KEY(participant_id) REFERENCES participants(id)

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS certificate_templates(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    template_name TEXT,

    file_name TEXT,

    uploaded_at TEXT,

    status TEXT

)
""")

connection.commit()

connection.close()

print("Database Created Successfully")