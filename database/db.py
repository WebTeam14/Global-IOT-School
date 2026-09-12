import sqlite3

DATABASE = "database/certificate.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_missing(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if column not in existing_columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def run_schema_migrations():
    """
    Additive, idempotent schema upgrades that support the SVG Template Manager.
    Safe to run on every app startup: only ADDS columns that don't exist yet,
    never drops or rewrites any existing table or data. Older PNG/JPG
    templates and events keep working exactly as before.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # certificate_templates: distinguish SVG vs legacy image templates,
    # and support an optional description shown on the template cards.
    _add_column_if_missing(cursor, "certificate_templates", "template_type", "TEXT DEFAULT 'image'")
    _add_column_if_missing(cursor, "certificate_templates", "description", "TEXT")
    _add_column_if_missing(cursor, "certificate_templates", "updated_at", "TEXT")

    # events: template_id is the new source of truth used by the SVG
    # Template Manager dropdown. template_name (legacy) is kept in sync
    # for any existing code/display that still reads it.
    _add_column_if_missing(cursor, "events", "template_id", "INTEGER")

    # certificates: extra export formats generated alongside the existing
    # PDF (file_name), for templates that are SVG-based.
    _add_column_if_missing(cursor, "certificates", "svg_file_name", "TEXT")
    _add_column_if_missing(cursor, "certificates", "png_file_name", "TEXT")

    conn.commit()
    conn.close()