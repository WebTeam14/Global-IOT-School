from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from modules.auth_decorators import login_required
from modules.file_cleanup import delete_certificate_files

from database.models import (
    get_all_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
    get_all_templates,
    get_template_by_id,
    get_participants_by_event,
    get_certificates_by_participant,
    delete_certificates_by_participant,
    delete_participant
)

events_bp = Blueprint("events", __name__)


def _cascade_delete_event(event_id):
    """
    Deletes one event and everything under it: for every participant of
    this event, removes their certificates (files + DB rows), then the
    participant itself, then finally the event. Shared by the legacy
    link-based delete route and the JSON API used by the Reports page.
    """
    participants = get_participants_by_event(event_id)

    for participant in participants:
        certs = get_certificates_by_participant(participant["id"])

        for cert in certs:
            delete_certificate_files(
                current_app.config,
                cert["file_name"],
                cert["qr_code"],
                cert["svg_file_name"],
                cert["png_file_name"]
            )

        delete_certificates_by_participant(participant["id"])
        delete_participant(participant["id"])

    delete_event(event_id)


@events_bp.route("/events")
@login_required
def events():

    event_list = get_all_events()

    today_str = datetime.now().strftime("%Y-%m-%d")
    upcoming_count = sum(1 for e in event_list if e["event_date"] >= today_str)

    return render_template(
        "events.html",
        events=event_list,
        total_events=len(event_list),
        upcoming_count=upcoming_count
    )


@events_bp.route("/events/add", methods=["GET", "POST"])
@login_required
def add_event():

    if request.method == "POST":

        event_name = request.form["event_name"]
        event_date = request.form["event_date"]
        organizer = request.form["organizer"]
        venue = request.form.get("venue", "")
        description = request.form.get("description", "")
        template_id = request.form.get("template_id") or None
        status = "Active"

        template = get_template_by_id(int(template_id)) if template_id else None
        template_name = template["template_name"] if template else None

        create_event(
            event_name, event_date, organizer,
            venue, description, template_name, status,
            template_id=template_id
        )

        return redirect(url_for("events.events"))

    templates = get_all_templates(status="Active")
    return render_template("add_event.html", templates=templates)


@events_bp.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
def edit_event(event_id):

    event = get_event_by_id(event_id)

    if request.method == "POST":
        template_id = request.form.get("template_id") or None
        template = get_template_by_id(int(template_id)) if template_id else None
        template_name = template["template_name"] if template else None

        update_event(
            event_id,
            request.form["event_name"],
            request.form["event_date"],
            request.form["organizer"],
            request.form.get("venue", ""),
            request.form.get("description", ""),
            template_name,
            event["status"],
            template_id=template_id
        )
        return redirect(url_for("events.events"))

    templates = get_all_templates(status="Active")
    return render_template("edit_event.html", event=event, templates=templates)


@events_bp.route("/events/delete/<int:event_id>")
@login_required
def delete_event_route(event_id):

    _cascade_delete_event(event_id)

    return redirect(url_for("events.events", deleted="1"))


# ======================================
# DELETE API (used by Reports page JS)
# ======================================

@events_bp.route("/api/events/<int:event_id>", methods=["DELETE"])
@login_required
def api_delete_event(event_id):

    event = get_event_by_id(event_id)

    if event is None:
        return jsonify({"success": False, "message": "Event not found."}), 404

    try:
        _cascade_delete_event(event_id)
        return jsonify({"success": True, "message": "Event and all its data deleted successfully."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to delete event. Please try again."}), 500


@events_bp.route("/api/events", methods=["DELETE"])
@login_required
def api_delete_all_events():

    try:
        events = get_all_events()

        for event in events:
            _cascade_delete_event(event["id"])

        return jsonify({"success": True, "message": "All events and their data deleted successfully."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to delete events. Please try again."}), 500