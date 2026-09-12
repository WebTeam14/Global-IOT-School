from flask import Flask, render_template, request, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from routes.events import events_bp
from routes.templates import templates_bp
from routes.participants import participants_bp
from routes.certificates_gen import certificates_gen_bp
from routes.verify import verify_bp
from routes.auth import auth_bp

from database.models import (
    get_dashboard_stats,
    get_event_reports,
    get_admin_by_id,
    update_admin_password,
    update_admin_profile,
    get_recent_certificates
)
from modules.auth_decorators import login_required
from database.db import run_schema_migrations

app = Flask(__name__)
app.config.from_pyfile("config.py")

# Safe, additive schema upgrade for the SVG Template Manager.
# Only adds new columns if missing — never touches existing data.
run_schema_migrations()

app.register_blueprint(events_bp)
app.register_blueprint(templates_bp)
app.register_blueprint(participants_bp)
app.register_blueprint(certificates_gen_bp)
app.register_blueprint(verify_bp)
app.register_blueprint(auth_bp)


@app.before_request
def load_logged_in_admin():
    admin_id = session.get("admin_id")
    g.admin = get_admin_by_id(admin_id) if admin_id else None


@app.route("/")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    recent_certs = get_recent_certificates(5)
    return render_template("dashboard.html", stats=stats, recent_certs=recent_certs)


@app.route("/reports")
@login_required
def reports():
    reports_data = get_event_reports()
    overall_stats = get_dashboard_stats()
    return render_template("reports.html", reports=reports_data, overall_stats=overall_stats)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    message = None
    error = None

    if request.method == "POST":

        form_type = request.form.get("form_type")

        if form_type == "profile":

            username = request.form.get("username")
            email = request.form.get("email")
            profile_pic_filename = None

            file = request.files.get("profile_pic")
            if file and file.filename != "":
                upload_folder = os.path.join(app.static_folder, "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                profile_pic_filename = secure_filename(f"{session['admin_id']}_{file.filename}")
                file.save(os.path.join(upload_folder, profile_pic_filename))

            update_admin_profile(
                session["admin_id"],
                username=username,
                email=email,
                profile_pic=profile_pic_filename
            )
            message = "Profile updated successfully!"

        elif form_type == "password":

            current_password = request.form["current_password"]
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]

            admin = get_admin_by_id(session["admin_id"])

            if not check_password_hash(admin["password"], current_password):
                error = "Current password is incorrect."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            elif len(new_password) < 6:
                error = "New password must be at least 6 characters long."
            else:
                update_admin_password(admin["id"], generate_password_hash(new_password))
                message = "Password updated successfully!"

    admin = get_admin_by_id(session["admin_id"])

    return render_template("settings.html", admin=admin, message=message, error=error)


if __name__ == "__main__":
    app.run(debug=True)