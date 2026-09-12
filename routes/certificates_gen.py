import os
import uuid
from datetime import datetime
from flask import (
    Blueprint,
    redirect,
    url_for,
    current_app,
    send_from_directory,
    render_template,
    jsonify,
    request
)
from modules.auth_decorators import login_required

from database.models import (
    get_participant_by_id,
    get_participants_by_event,
    create_certificate,
    get_all_certificates,
    get_certificate_by_id,
    delete_certificate_row,
    delete_all_certificate_rows,
    create_email_log,
    update_certificate_status,
    update_certificate_export_files,
    get_event_by_id,
    get_template_by_id,
    get_all_events
)
from modules.certificate_generator import generate_certificate
from modules.svg_certificate_gen import render_svg_certificate, svg_to_pdf, pdf_to_png
from modules.email_sender import send_certificate_email
from modules.qr_generator import generate_qr_code
from modules.file_cleanup import delete_certificate_files

certificates_gen_bp = Blueprint("certificates_gen", __name__)


def _get_svg_template_for_participant(participant):
    """Returns the SVG certificate_templates row assigned to this participant's
    event, or None if the event has no template / a legacy image template."""
    event = get_event_by_id(participant["event_id"])
    if not event or not event["template_id"]:
        return None

    template = get_template_by_id(event["template_id"])
    if not template or template["template_type"] != "svg":
        return None

    return template, event


def generate_certificate_for_participant(participant, send_email=None):

    certificate_id = "CERT-" + uuid.uuid4().hex[:8].upper()

    qr_folder = current_app.config["QR_FOLDER"]
    os.makedirs(qr_folder, exist_ok=True)

    qr_filename = f"{certificate_id}.png"
    qr_output_path = os.path.join(qr_folder, qr_filename)

    verification_url = f"{current_app.config['SITE_BASE_URL']}/verify/{certificate_id}"
    generate_qr_code(verification_url, qr_output_path)

    svg_template_match = _get_svg_template_for_participant(participant)
    output_path = None
    output_filename = None

    if svg_template_match:
        # ---- New SVG-based generation pipeline ----
        template, event = svg_template_match

        svg_path = os.path.join(current_app.config["UPLOAD_FOLDER"], template["file_name"])
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_source = f.read()

        issue_date = datetime.now().strftime("%Y-%m-%d")

        description = (template["description"] or "").strip()
        if not description:
            description = (event["description"] or "").strip()

        rendered_svg = render_svg_certificate(
            svg_source,
            data={
                "participant_name": participant["name"],
                "event_name": participant["event_name"],
                "certificate_id": certificate_id,
                "issue_date": issue_date,
                "organization_name": event["organizer"] or "",
                "course_name": participant["event_name"],
                "description": description,
            },
            qr_code_path=qr_output_path
        )

        base_name = f"{participant['name'].replace(' ', '_')}_{certificate_id}"

        svg_folder = current_app.config["GENERATED_SVG_FOLDER"]
        png_folder = current_app.config["GENERATED_PNG_FOLDER"]
        pdf_folder = current_app.config["GENERATED_FOLDER"]
        os.makedirs(svg_folder, exist_ok=True)
        os.makedirs(png_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)

        svg_filename = f"{base_name}.svg"
        output_filename = f"{base_name}.pdf"
        png_filename = f"{base_name}.png"

        svg_output_path = os.path.join(svg_folder, svg_filename)
        output_path = os.path.join(pdf_folder, output_filename)
        png_output_path = os.path.join(png_folder, png_filename)

        with open(svg_output_path, "w", encoding="utf-8") as f:
            f.write(rendered_svg)

        try:
            svg_to_pdf(rendered_svg, output_path)   # content OK
            # or: svg_to_pdf(svg_output_path, output_path)  # path also OK
        except Exception as e:
            return False, f"Certificate PDF generation failed for {participant['name']}: {e}"

        create_certificate(
            participant["id"],
            certificate_id,
            output_filename,
            issue_date,
            "Generated",
            qr_filename
        )
        update_certificate_export_files(certificate_id, svg_filename, png_filename)

    else:
        # ---- Legacy image/HTML-based generation pipeline ----
        output_filename = f"{participant['name'].replace(' ', '_')}_{certificate_id}.pdf"
        output_path = os.path.join(current_app.config["GENERATED_FOLDER"], output_filename)

        os.makedirs(current_app.config["GENERATED_FOLDER"], exist_ok=True)

        generate_certificate(
            output_path=output_path,
            name=participant["name"],
            event_name=participant["event_name"],
            date=datetime.now().strftime("%Y-%m-%d"),
            certificate_id=certificate_id,
            qr_code_path=qr_output_path
        )

        create_certificate(
            participant["id"],
            certificate_id,
            output_filename,
            datetime.now().strftime("%Y-%m-%d"),
            "Generated",
            qr_filename
        )

    # Always set this (both SVG and legacy paths)
    should_send_email = (
        send_email if send_email is not None
        else current_app.config.get("EMAIL_AUTOMATION_ENABLED", True)
    )

    if not should_send_email:
        return True, f"Certificate generated for {participant['name']} (email skipped)"

    try:
        send_certificate_email(
            smtp_email=current_app.config["EMAIL_ADDRESS"],
            smtp_app_password=current_app.config["EMAIL_APP_PASSWORD"],
            recipient_email=participant["email"],
            participant_name=participant["name"],
            event_name=participant["event_name"],
            pdf_path=output_path
        )

        create_email_log(participant["id"], "Sent", None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        update_certificate_status(certificate_id, "Emailed")

    except Exception as e:
        create_email_log(participant["id"], "Failed", str(e), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return True, f"Certificate generated but email FAILED for {participant['name']}: {e}"

    return True, f"Certificate generated and emailed to {participant['name']}"


@certificates_gen_bp.route("/certificates/generate/<int:participant_id>")
@login_required
def generate_certificate_route(participant_id):

    send_email_param = request.args.get("send_email")
    send_email = None if send_email_param is None else send_email_param == "1"

    participant = get_participant_by_id(participant_id)
    success, message = generate_certificate_for_participant(participant, send_email=send_email)

    if not success:
        return message, 404

    return redirect(url_for("certificates_gen.certificates_list"))


@certificates_gen_bp.route("/certificates/generate_bulk/<int:event_id>")
@login_required
def generate_bulk_certificates(event_id):

    send_email_param = request.args.get("send_email")
    send_email = None if send_email_param is None else send_email_param == "1"

    participants = get_participants_by_event(event_id)

    success_count = 0
    failed = []

    for participant in participants:
        success, message = generate_certificate_for_participant(participant, send_email=send_email)

        if success:
            success_count += 1
        else:
            failed.append(message)

    return redirect(url_for(
        "certificates_gen.certificates_list",
        bulk_success=success_count,
        bulk_failed=len(failed)
    ))


@certificates_gen_bp.route("/certificates")
@login_required
def certificates_list():
    certs = get_all_certificates()
    events = get_all_events()

    total = len(certs)
    sent = sum(1 for c in certs if c["status"] == "Emailed")
    pending = sum(1 for c in certs if c["status"] == "Generated")
    failed = total - sent - pending

    completion = round((sent / total * 100), 1) if total > 0 else 0

    return render_template(
        "certificates.html",
        certs=certs,
        events=events,
        total_certs=total,
        sent_count=sent,
        pending_count=pending,
        failed_count=failed,
        completion=completion
    )


@certificates_gen_bp.route("/certificates/download/<filename>")
def download_certificate(filename):
    return send_from_directory(
        current_app.config["GENERATED_FOLDER"],
        filename,
        as_attachment=True
    )


@certificates_gen_bp.route("/certificates/download/svg/<filename>")
def download_certificate_svg(filename):
    return send_from_directory(
        current_app.config["GENERATED_SVG_FOLDER"],
        filename,
        as_attachment=True
    )


@certificates_gen_bp.route("/certificates/download/png/<filename>")
def download_certificate_png(filename):
    return send_from_directory(
        current_app.config["GENERATED_PNG_FOLDER"],
        filename,
        as_attachment=True
    )

@certificates_gen_bp.route("/certificates/print-selected", methods=["POST"])
@login_required
def print_selected_certificates():

    cert_ids = request.form.getlist("cert_ids")

    if not cert_ids:
        return "No certificates selected.", 400

    import fitz
    import uuid as uuid_module

    merged = fitz.open()
    added_any = False

    for cid in cert_ids:
        try:
            cert = get_certificate_by_id(int(cid))
        except (ValueError, TypeError):
            continue

        if cert is None:
            continue

        pdf_path = os.path.join(current_app.config["GENERATED_FOLDER"], cert["file_name"])

        if os.path.exists(pdf_path):
            with fitz.open(pdf_path) as single:
                merged.insert_pdf(single)
                added_any = True

    if not added_any:
        merged.close()
        return "None of the selected certificate files could be found.", 404

    output_filename = f"print_batch_{uuid_module.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(current_app.config["GENERATED_FOLDER"], output_filename)
    merged.save(output_path)
    merged.close()

    return send_from_directory(
        current_app.config["GENERATED_FOLDER"],
        output_filename,
        as_attachment=False  # display inline in browser so the print button/Ctrl+P works directly
    )

# ======================================
# DELETE API (used by Certificates page JS)
# ======================================

@certificates_gen_bp.route("/api/certificates/<int:cert_id>", methods=["DELETE"])
@login_required
def api_delete_certificate(cert_id):

    cert = get_certificate_by_id(cert_id)

    if cert is None:
        return jsonify({"success": False, "message": "Certificate not found."}), 404

    try:
        file_errors = delete_certificate_files(
            current_app.config,
            cert["file_name"],
            cert["qr_code"],
            cert["svg_file_name"],
            cert["png_file_name"]
        )

        if file_errors:
            return jsonify({
                "success": False,
                "message": "Failed to delete certificate files. " + " ".join(file_errors)
            }), 500

        delete_certificate_row(cert_id)

        return jsonify({"success": True, "message": "Certificate deleted successfully."})

    except Exception:
        return jsonify({"success": False, "message": "Failed to delete certificate. Please try again."}), 500


@certificates_gen_bp.route("/api/certificates", methods=["DELETE"])
@login_required
def api_delete_all_certificates():

    try:
        certs = get_all_certificates()

        file_errors = []
        for cert in certs:
            errors = delete_certificate_files(
                current_app.config,
                cert["file_name"],
                cert["qr_code"],
                cert["svg_file_name"],
                cert["png_file_name"]
            )
            file_errors.extend(errors)

        if file_errors:
            return jsonify({
                "success": False,
                "message": "Some certificate files could not be deleted. No records were removed. " + " ".join(file_errors)
            }), 500

        delete_all_certificate_rows()

        return jsonify({"success": True, "message": "All certificates deleted successfully."})

    except Exception:
        return jsonify({"success": False, "message": "Failed to delete certificates. Please try again."}), 500