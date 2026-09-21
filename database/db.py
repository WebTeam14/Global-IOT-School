import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is not None:
        return _db

    uri = os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not set in .env or environment.")

    _client = MongoClient(uri, serverSelectionTimeoutMS=10000)

    try:
        _db = _client.get_default_database()
    except Exception:
        _db = None

    if _db is None or not getattr(_db, "name", None) or _db.name == "test":
        _db = _client["iot_certificates"]

    _ensure_indexes(_db)
    return _db

def _ensure_indexes(db):
    db.admins.create_index("username", unique=True)
    db.admins.create_index("id", unique=True)
    db.events.create_index("id", unique=True)
    db.participants.create_index("id", unique=True)
    db.participants.create_index("event_id")
    db.certificates.create_index("id", unique=True)
    db.certificates.create_index("certificate_id", unique=True)
    db.certificates.create_index("participant_id")
    db.certificate_templates.create_index("id", unique=True)
    db.email_logs.create_index("id", unique=True)


def next_id(collection_name: str) -> int:
    db = get_db()
    doc = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return int(doc["seq"])


def run_schema_migrations():
    get_db()
    print("MongoDB connected and indexes ensured.")


def get_connection():
    """Back-compat alias."""
    return get_db()