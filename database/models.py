from database.db import get_connection
from datetime import datetime

# ======================================
# EVENT FUNCTIONS
# ======================================

def get_all_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    events = cursor.fetchall()
    conn.close()
    return events


def get_event_by_id(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return event


def create_event(event_name, event_date, organizer, venue, description, template_name, status, template_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events(event_name, event_date, organizer, venue, description, template_name, status, template_id)
        VALUES(?,?,?,?,?,?,?,?)
    """, (event_name, event_date, organizer, venue, description, template_name, status, template_id))
    conn.commit()
    conn.close()


def update_event(event_id, event_name, event_date, organizer, venue, description, template_name, status, template_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events SET event_name=?, event_date=?, organizer=?, venue=?,
        description=?, template_name=?, status=?, template_id=? WHERE id=?
    """, (event_name, event_date, organizer, venue, description, template_name, status, template_id, event_id))
    conn.commit()
    conn.close()


def get_events_by_template(template_id):
    """All events currently assigned to a given template (for the template card list)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, event_name FROM events WHERE template_id=?", (template_id,))
    events = cursor.fetchall()
    conn.close()
    return events


def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()


def search_events(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM events
        WHERE event_name LIKE ? OR organizer LIKE ? OR venue LIKE ?
        ORDER BY event_date DESC
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    events = cursor.fetchall()
    conn.close()
    return events


# ======================================
# CERTIFICATE TEMPLATE FUNCTIONS
# ======================================

def create_template(template_name, file_name, uploaded_at, status,
                     template_type="svg", description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO certificate_templates
            (template_name, file_name, uploaded_at, status, template_type, description, updated_at)
        VALUES(?,?,?,?,?,?,?)
    """, (template_name, file_name, uploaded_at, status, template_type, description, uploaded_at))
    conn.commit()
    template_id = cursor.lastrowid
    conn.close()
    return template_id


def get_all_templates(search=None, status=None, template_type=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM certificate_templates WHERE 1=1"
    params = []

    if search:
        query += " AND (template_name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status:
        query += " AND status = ?"
        params.append(status)

    if template_type:
        query += " AND template_type = ?"
        params.append(template_type)

    query += " ORDER BY uploaded_at DESC"

    cursor.execute(query, params)
    templates = cursor.fetchall()
    conn.close()
    return templates


def get_template_by_id(template_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificate_templates WHERE id=?", (template_id,))
    template = cursor.fetchone()
    conn.close()
    return template


def get_template_by_name(template_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificate_templates WHERE template_name=?", (template_name,))
    template = cursor.fetchone()
    conn.close()
    return template


def update_template(template_id, template_name, description, status,
                     updated_at, file_name=None):
    conn = get_connection()
    cursor = conn.cursor()

    if file_name:
        cursor.execute("""
            UPDATE certificate_templates
            SET template_name=?, description=?, status=?, file_name=?, updated_at=?
            WHERE id=?
        """, (template_name, description, status, file_name, updated_at, template_id))
    else:
        cursor.execute("""
            UPDATE certificate_templates
            SET template_name=?, description=?, status=?, updated_at=?
            WHERE id=?
        """, (template_name, description, status, updated_at, template_id))

    conn.commit()
    conn.close()


def delete_template(template_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificate_templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()


# ======================================
# PARTICIPANT FUNCTIONS
# ======================================

def create_participant(event_id, name, email, college, department, position, created_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO participants(event_id, name, email, college, department, position, created_at)
        VALUES(?,?,?,?,?,?,?)
    """, (event_id, name, email, college, department, position, created_at))
    conn.commit()
    conn.close()


def get_all_participants():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT participants.*, events.event_name, events.template_name
        FROM participants
        JOIN events ON participants.event_id = events.id
        ORDER BY participants.id DESC
    """)
    participants = cursor.fetchall()
    conn.close()
    return participants


def get_participant_by_id(participant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT participants.*, events.event_name, events.template_name
        FROM participants
        JOIN events ON participants.event_id = events.id
        WHERE participants.id=?
    """, (participant_id,))
    participant = cursor.fetchone()
    conn.close()
    return participant


def get_participants_by_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT participants.*, events.event_name, events.template_name
        FROM participants
        JOIN events ON participants.event_id = events.id
        WHERE participants.event_id = ?
    """, (event_id,))
    participants = cursor.fetchall()
    conn.close()
    return participants


def delete_participant(participant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participants WHERE id=?", (participant_id,))
    conn.commit()
    conn.close()


# ======================================
# CERTIFICATE FUNCTIONS
# ======================================

def create_certificate(participant_id, certificate_id, file_name, issue_date, status, qr_code=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO certificates(participant_id, certificate_id, file_name, issue_date, status, qr_code)
        VALUES(?,?,?,?,?,?)
    """, (participant_id, certificate_id, file_name, issue_date, status, qr_code))
    conn.commit()
    conn.close()


def get_all_certificates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT certificates.*, participants.name, participants.email
        FROM certificates
        JOIN participants ON certificates.participant_id = participants.id
        ORDER BY certificates.id DESC
    """)
    certs = cursor.fetchall()
    conn.close()
    return certs


def get_certificate_by_certificate_id(certificate_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            certificates.*,
            participants.name,
            participants.email,
            participants.college,
            participants.department,
            participants.position,
            events.event_name,
            events.organizer,
            events.event_date
        FROM certificates
        JOIN participants ON certificates.participant_id = participants.id
        JOIN events ON participants.event_id = events.id
        WHERE certificates.certificate_id = ?
    """, (certificate_id,))
    certificate = cursor.fetchone()
    conn.close()
    return certificate


def update_certificate_status(certificate_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE certificates SET status=? WHERE certificate_id=?", (status, certificate_id))
    conn.commit()
    conn.close()


def update_certificate_export_files(certificate_id, svg_file_name=None, png_file_name=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE certificates SET svg_file_name=?, png_file_name=? WHERE certificate_id=?",
        (svg_file_name, png_file_name, certificate_id)
    )
    conn.commit()
    conn.close()

def get_certificate_by_id(cert_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificates WHERE id=?", (cert_id,))
    cert = cursor.fetchone()
    conn.close()
    return cert


def get_certificates_by_participant(participant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificates WHERE participant_id=?", (participant_id,))
    certs = cursor.fetchall()
    conn.close()
    return certs


def delete_certificate_row(cert_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificates WHERE id=?", (cert_id,))
    conn.commit()
    conn.close()


def delete_certificates_by_participant(participant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificates WHERE participant_id=?", (participant_id,))
    conn.commit()
    conn.close()


def delete_all_certificate_rows():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificates")
    conn.commit()
    conn.close()

# ======================================
# EMAIL LOG FUNCTIONS
# ======================================

def create_email_log(participant_id, email_status, error_message, sent_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO email_logs(participant_id, email_status, error_message, sent_at)
        VALUES(?,?,?,?)
    """, (participant_id, email_status, error_message, sent_at))
    conn.commit()
    conn.close()


# ======================================
# DASHBOARD / REPORTING FUNCTIONS
# ======================================

def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM participants")
    total_participants = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM certificates")
    total_certificates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM email_logs WHERE email_status = 'Sent'")
    emails_sent = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM email_logs WHERE email_status = 'Failed'")
    emails_failed = cursor.fetchone()[0]

    conn.close()

    return {
        "total_participants": total_participants,
        "total_certificates": total_certificates,
        "emails_sent": emails_sent,
        "emails_failed": emails_failed
    }


def get_event_reports():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    events = cursor.fetchall()

    reports = []
    for event in events:
        cursor.execute("SELECT COUNT(*) FROM participants WHERE event_id=?", (event["id"],))
        participant_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM certificates
            JOIN participants ON certificates.participant_id = participants.id
            WHERE participants.event_id=?
        """, (event["id"],))
        certificate_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM email_logs
            JOIN participants ON email_logs.participant_id = participants.id
            WHERE participants.event_id=? AND email_logs.email_status='Sent'
        """, (event["id"],))
        emails_sent = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM email_logs
            JOIN participants ON email_logs.participant_id = participants.id
            WHERE participants.event_id=? AND email_logs.email_status='Failed'
        """, (event["id"],))
        emails_failed = cursor.fetchone()[0]

        reports.append({
            "event_name": event["event_name"],
            "event_date": event["event_date"],
            "participant_count": participant_count,
            "certificate_count": certificate_count,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed
        })

    conn.close()
    return reports


def get_recent_certificates(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT certificates.*, participants.name, participants.email
        FROM certificates
        JOIN participants ON certificates.participant_id = participants.id
        ORDER BY certificates.id DESC
        LIMIT ?
    """, (limit,))
    certs = cursor.fetchall()
    conn.close()
    return certs


# ======================================
# ADMIN FUNCTIONS
# ======================================

def get_admin_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()
    return admin


def get_admin_by_id(admin_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE id=?", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin


def create_admin(username, email, password_hash, created_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO admins(username, email, password, created_at)
        VALUES(?,?,?,?)
    """, (username, email, password_hash, created_at))
    conn.commit()
    conn.close()


def update_admin_password(admin_id, new_password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admins SET password=? WHERE id=?", (new_password_hash, admin_id))
    conn.commit()
    conn.close()


def update_admin_profile(admin_id, username=None, email=None, profile_pic=None):
    """Update admin profile (username, email, or profile picture)"""
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if username:
        updates.append("username = ?")
        params.append(username)
    if email:
        updates.append("email = ?")
        params.append(email)
    if profile_pic:
        updates.append("profile_pic = ?")
        params.append(profile_pic)

    if updates:
        query = f"UPDATE admins SET {', '.join(updates)} WHERE id = ?"
        params.append(admin_id)
        cursor.execute(query, params)
        conn.commit()

    conn.close()