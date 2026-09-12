import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from modules.auth_decorators import login_required
from modules.file_cleanup import delete_certificate_files

from database.models import (
    get_all_participants,
    get_all_events,
    create_participant,
    delete_participant,
    get_participant_by_id,
    get_certificates_by_participant,
    delete_certificates_by_participant
)

participants_bp = Blueprint("participants", __name__)


def _cascade_delete_participant(participant_id):
    """Removes one participant's certificates (files + DB rows), then the
    participant itself. Shared by the individual delete route and the
    bulk-delete API used by the Participants page's 'select all' feature."""
    certs = get_certificates_by_participant(participant_id)

    for cert in certs:
        delete_certificate_files(
            current_app.config,
            cert["file_name"],
            cert["qr_code"],
            cert["svg_file_name"],
            cert["png_file_name"]
        )

    delete_certificates_by_participant(participant_id)
    delete_participant(participant_id)


@participants_bp.route("/participants")
@login_required
def participants_list():
    participants = get_all_participants()
    events = get_all_events()
    return render_template(
        "participants.html",
        participants=participants,
        total_participants=len(participants),
        total_events=len(events)
    )


@participants_bp.route("/participants/add", methods=["GET", "POST"])
@login_required
def add_participant():

    if request.method == "POST":

        create_participant(
            request.form["event_id"],
            request.form["name"],
            request.form["email"],
            request.form.get("college", ""),
            request.form.get("department", ""),
            request.form.get("position", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return redirect(url_for("participants.participants_list"))

    events = get_all_events()
    return render_template("add_participant.html", events=events)


@participants_bp.route("/participants/delete/<int:participant_id>")
@login_required
def delete_participant_route(participant_id):

    _cascade_delete_participant(participant_id)

    return redirect(url_for("participants.participants_list", deleted="1"))


# ======================================
# BULK DELETE API (used by Participants page "select all" JS)
# ======================================

@participants_bp.route("/api/participants/bulk_delete", methods=["POST"])
@login_required
def api_bulk_delete_participants():

    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if not isinstance(ids, list) or not ids:
        return jsonify({"success": False, "message": "No participants selected."}), 400

    try:
        deleted_count = 0
        for participant_id in ids:
            participant = get_participant_by_id(int(participant_id))
            if participant is None:
                continue
            _cascade_delete_participant(int(participant_id))
            deleted_count += 1

        return jsonify({
            "success": True,
            "message": f"Deleted {deleted_count} participant(s) successfully.",
            "deleted_count": deleted_count
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to delete selected participants. Please try again."}), 500


@participants_bp.route("/participants/upload_excel", methods=["GET", "POST"])
@login_required
def upload_excel():

    if request.method == "POST":

        event_id = request.form["event_id"]
        file = request.files["excel_file"]

        if file.filename == "":
            return "No file selected", 400

        df = pd.read_excel(file)

        required_columns = ["Name", "Email"]
        for col in required_columns:
            if col not in df.columns:
                return f"Missing required column: '{col}'. Found columns: {list(df.columns)}", 400

        added_count = 0

        for index, row in df.iterrows():

            if pd.isna(row["Name"]) or pd.isna(row["Email"]):
                continue

            create_participant(
                event_id,
                str(row["Name"]),
                str(row["Email"]),
                str(row.get("College", "")) if not pd.isna(row.get("College", "")) else "",
                str(row.get("Department", "")) if not pd.isna(row.get("Department", "")) else "",
                str(row.get("Position", "")) if not pd.isna(row.get("Position", "")) else "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            added_count += 1

        return redirect(url_for("participants.participants_list", imported=added_count))

    events = get_all_events()
    return render_template("upload_excel.html", events=events)