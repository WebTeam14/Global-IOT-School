from datetime import datetime
from database.db import get_db, next_id


def _doc(d):
    if d is None:
        return None
    out = dict(d)
    out.pop("_id", None)
    return out


def _docs(cursor):
    return [_doc(x) for x in cursor]


# ======================================
# EVENTS
# ======================================

def get_all_events():
    db = get_db()
    return _docs(db.events.find().sort("event_date", -1))


def get_event_by_id(event_id):
    db = get_db()
    return _doc(db.events.find_one({"id": int(event_id)}))


def create_event(event_name, event_date, organizer, venue, description, template_name, status, template_id=None):
    db = get_db()
    eid = next_id("events")
    db.events.insert_one({
        "id": eid,
        "event_name": event_name,
        "event_date": event_date,
        "organizer": organizer,
        "venue": venue,
        "description": description,
        "template_name": template_name,
        "status": status,
        "template_id": int(template_id) if template_id not in (None, "") else None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return eid


def update_event(event_id, event_name, event_date, organizer, venue, description, template_name, status, template_id=None):
    db = get_db()
    db.events.update_one(
        {"id": int(event_id)},
        {"$set": {
            "event_name": event_name,
            "event_date": event_date,
            "organizer": organizer,
            "venue": venue,
            "description": description,
            "template_name": template_name,
            "status": status,
            "template_id": int(template_id) if template_id not in (None, "") else None,
        }},
    )


def get_events_by_template(template_id):
    db = get_db()
    return _docs(db.events.find(
        {"template_id": int(template_id)},
        {"id": 1, "event_name": 1},
    ))


def delete_event(event_id):
    db = get_db()
    db.events.delete_one({"id": int(event_id)})


def search_events(keyword):
    import re
    db = get_db()
    rx = re.compile(re.escape(keyword), re.IGNORECASE)
    return _docs(db.events.find({
        "$or": [
            {"event_name": rx},
            {"organizer": rx},
            {"venue": rx},
        ]
    }).sort("event_date", -1))


# ======================================
# TEMPLATES
# ======================================

def create_template(template_name, file_name, uploaded_at, status,
                    template_type="image", description=None):
    db = get_db()
    tid = next_id("certificate_templates")
    db.certificate_templates.insert_one({
        "id": tid,
        "template_name": template_name,
        "file_name": file_name,
        "uploaded_at": uploaded_at,
        "status": status,
        "template_type": template_type or "image",
        "description": description,
        "updated_at": uploaded_at,
    })
    return tid


def get_all_templates(search=None, status=None, template_type=None):
    import re
    db = get_db()
    q = {}
    if status:
        q["status"] = status
    if template_type:
        q["template_type"] = template_type
    if search:
        q["template_name"] = re.compile(re.escape(search), re.IGNORECASE)
    return _docs(db.certificate_templates.find(q).sort("id", -1))


def get_template_by_id(template_id):
    db = get_db()
    return _doc(db.certificate_templates.find_one({"id": int(template_id)}))


def get_template_by_name(template_name):
    db = get_db()
    return _doc(db.certificate_templates.find_one({"template_name": template_name}))


def update_template(template_id, template_name, description, status,
                    template_type=None, file_name=None, updated_at=None):
    db = get_db()
    fields = {
        "template_name": template_name,
        "description": description,
        "status": status,
    }
    if template_type is not None:
        fields["template_type"] = template_type
    if file_name is not None:
        fields["file_name"] = file_name
    if updated_at is not None:
        fields["updated_at"] = updated_at
    db.certificate_templates.update_one({"id": int(template_id)}, {"$set": fields})


def delete_template(template_id):
    db = get_db()
    db.certificate_templates.delete_one({"id": int(template_id)})


# ======================================
# PARTICIPANTS
# ======================================

def create_participant(event_id, name, email, college, department, position, created_at):
    db = get_db()
    pid = next_id("participants")
    db.participants.insert_one({
        "id": pid,
        "event_id": int(event_id),
        "name": name,
        "email": email,
        "college": college or "",
        "department": department or "",
        "position": position or "",
        "created_at": created_at,
    })
    return pid


def get_all_participants():
    db = get_db()
    rows = []
    for p in db.participants.find().sort("id", -1):
        p = _doc(p)
        ev = db.events.find_one({"id": p.get("event_id")})
        p["event_name"] = ev.get("event_name") if ev else ""
        rows.append(p)
    return rows


def get_participant_by_id(participant_id):
    db = get_db()
    p = _doc(db.participants.find_one({"id": int(participant_id)}))
    if not p:
        return None
    ev = db.events.find_one({"id": p.get("event_id")})
    p["event_name"] = ev.get("event_name") if ev else ""
    return p


def get_participants_by_event(event_id):
    db = get_db()
    rows = []
    for p in db.participants.find({"event_id": int(event_id)}).sort("id", -1):
        p = _doc(p)
        ev = db.events.find_one({"id": p.get("event_id")})
        p["event_name"] = ev.get("event_name") if ev else ""
        rows.append(p)
    return rows


def delete_participant(participant_id):
    db = get_db()
    db.participants.delete_one({"id": int(participant_id)})


# ======================================
# CERTIFICATES
# ======================================

def create_certificate(participant_id, certificate_id, file_name, issue_date, status, qr_code=None):
    db = get_db()
    cid = next_id("certificates")
    db.certificates.insert_one({
        "id": cid,
        "participant_id": int(participant_id),
        "certificate_id": certificate_id,
        "file_name": file_name,
        "issue_date": issue_date,
        "status": status,
        "qr_code": qr_code,
        "svg_file_name": None,
        "png_file_name": None,
    })
    return cid


def _enrich_certificate(cert):
    if not cert:
        return None
    db = get_db()
    cert = _doc(cert)
    p = db.participants.find_one({"id": cert.get("participant_id")})
    if p:
        cert["name"] = p.get("name")
        cert["email"] = p.get("email")
        ev = db.events.find_one({"id": p.get("event_id")})
        if ev:
            cert["event_name"] = ev.get("event_name")
            cert["organizer"] = ev.get("organizer")
            cert["event_date"] = ev.get("event_date")
    return cert


def get_all_certificates():
    db = get_db()
    return [_enrich_certificate(c) for c in db.certificates.find().sort("id", -1)]


def get_certificate_by_certificate_id(certificate_id):
    db = get_db()
    cert = db.certificates.find_one({"certificate_id": certificate_id})
    return _enrich_certificate(cert)


def update_certificate_status(certificate_id, status):
    db = get_db()
    db.certificates.update_one({"certificate_id": certificate_id}, {"$set": {"status": status}})


def update_certificate_export_files(certificate_id, svg_file_name=None, png_file_name=None):
    db = get_db()
    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": {"svg_file_name": svg_file_name, "png_file_name": png_file_name}},
    )


def get_certificate_by_id(cert_id):
    db = get_db()
    return _doc(db.certificates.find_one({"id": int(cert_id)}))


def get_certificates_by_participant(participant_id):
    db = get_db()
    return _docs(db.certificates.find({"participant_id": int(participant_id)}))


def delete_certificate_row(cert_id):
    db = get_db()
    db.certificates.delete_one({"id": int(cert_id)})


def delete_certificates_by_participant(participant_id):
    db = get_db()
    db.certificates.delete_many({"participant_id": int(participant_id)})


def delete_all_certificate_rows():
    db = get_db()
    db.certificates.delete_many({})


# ======================================
# EMAIL LOGS
# ======================================

def create_email_log(participant_id, email_status, error_message, sent_at):
    db = get_db()
    lid = next_id("email_logs")
    db.email_logs.insert_one({
        "id": lid,
        "participant_id": int(participant_id),
        "email_status": email_status,
        "error_message": error_message,
        "sent_at": sent_at,
    })
    return lid


# ======================================
# DASHBOARD
# ======================================

def get_dashboard_stats():
    db = get_db()
    sent = db.email_logs.count_documents({"email_status": "Sent"})
    failed = db.email_logs.count_documents({"email_status": "Failed"})
    return {
        "total_participants": db.participants.count_documents({}),
        "total_events": db.events.count_documents({}),
        "total_certificates": db.certificates.count_documents({}),
        "emails_sent": sent,
        "emails_failed": failed,
    }


def get_event_reports():
    db = get_db()
    reports = []
    for event in db.events.find().sort("id", -1):
        eid = event["id"]
        pcount = db.participants.count_documents({"event_id": eid})
        pids = [p["id"] for p in db.participants.find({"event_id": eid}, {"id": 1})]
        ccount = db.certificates.count_documents({"participant_id": {"$in": pids}}) if pids else 0
        reports.append({
            "id": eid,
            "event_name": event.get("event_name"),
            "event_date": event.get("event_date"),
            "participant_count": pcount,
            "certificate_count": ccount,
        })
    return reports


def get_recent_certificates(limit=5):
    db = get_db()
    return [_enrich_certificate(c) for c in db.certificates.find().sort("id", -1).limit(limit)]


# ======================================
# ADMINS
# ======================================

def get_admin_by_username(username):
    db = get_db()
    return _doc(db.admins.find_one({"username": username}))


def get_admin_by_id(admin_id):
    db = get_db()
    return _doc(db.admins.find_one({"id": int(admin_id)}))


def create_admin(username, email, password_hash, created_at):
    db = get_db()
    aid = next_id("admins")
    db.admins.insert_one({
        "id": aid,
        "username": username,
        "email": email,
        "password": password_hash,
        "profile_pic": None,
        "created_at": created_at,
    })
    return aid


def update_admin_password(admin_id, new_password_hash):
    db = get_db()
    db.admins.update_one({"id": int(admin_id)}, {"$set": {"password": new_password_hash}})


def update_admin_profile(admin_id, username=None, email=None, profile_pic=None):
    data = {}
    if username is not None:
        data["username"] = str(username).strip()
    if email is not None:
        data["email"] = str(email).strip()
    if profile_pic is not None:
        data["profile_pic"] = profile_pic
    if not data:
        return
    db = get_db()
    db.admins.update_one({"id": int(admin_id)}, {"$set": data})