import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from modules.template_converter import convert_uploaded_template, TemplateConversionError
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    send_from_directory,
    jsonify,
    abort
)
from modules.auth_decorators import login_required

from database.models import (
    get_all_templates,
    get_template_by_id,
    create_template,
    update_template,
    delete_template,
    get_events_by_template
)

templates_bp = Blueprint("templates", __name__)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def _extension_of(filename):
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@templates_bp.route("/templates")
@login_required
def templates_list():

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    template_type = request.args.get("type", "").strip()

    templates = get_all_templates(
        search=search or None,
        status=status or None,
        template_type=template_type or None
    )

    templates_with_events = []
    for template in templates:
        assigned_events = get_events_by_template(template["id"])
        templates_with_events.append({
            "template": template,
            "assigned_events": assigned_events
        })

    return render_template(
        "templates_list.html",
        templates_with_events=templates_with_events,
        search=search,
        status=status,
        template_type=template_type,
        total_templates=len(templates)
    )


@templates_bp.route("/templates/upload", methods=["GET", "POST"])
@login_required
def upload_template():

    if request.method == "POST":

        template_name = request.form.get("template_name", "").strip()
        description = request.form.get("description", "").strip()
        file = request.files.get("template_file")

        if not template_name:
            return render_template(
                "upload_template.html",
                error="Template name is required."
            ), 400

        if not file or file.filename == "":
            return render_template(
                "upload_template.html",
                error="Please choose a template file to upload."
            ), 400

        if not allowed_file(file.filename):
            return render_template(
                "upload_template.html",
                error="Unsupported file type. Please upload an SVG, PDF, DOCX, PPTX, PNG, or JPG file."
            ), 400

        safe_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_filename = f"{timestamp}_{safe_name}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        temp_path = os.path.join(upload_folder, temp_filename)
        file.save(temp_path)

        extension = _extension_of(safe_name)

        try:
            svg_source, warning = convert_uploaded_template(temp_path, extension)
        except TemplateConversionError as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return render_template(
                "upload_template.html",
                error=str(e)
            ), 400

        # Always store the converted/normalized SVG (not the raw upload).
        # Guarantees every template has real {{placeholders}} + a QR slot.
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

        base = secure_filename(template_name) or safe_name.rsplit(".", 1)[0]
        svg_filename = f"{timestamp}_{base}.svg"
        svg_path = os.path.join(upload_folder, svg_filename)

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_source)

        create_template(
            template_name,
            svg_filename,
            _now(),
            "Active",
            template_type="svg",
            description=description
        )

        return redirect(url_for("templates.templates_list", converted_warning=warning or ""))

    return render_template("upload_template.html")


@templates_bp.route("/templates/edit/<int:template_id>", methods=["GET", "POST"])
@login_required
def edit_template(template_id):

    template = get_template_by_id(template_id)
    if template is None:
        abort(404)

    if request.method == "POST":

        template_name = request.form.get("template_name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "Active")
        file = request.files.get("template_file")

        if not template_name:
            return render_template(
                "edit_template.html",
                template=template,
                error="Template name is required."
            ), 400

        new_filename = None

        if file and file.filename != "":
            if not allowed_file(file.filename):
                return render_template(
                    "edit_template.html",
                    template=template,
                    error="Unsupported file type. Please upload an SVG, PDF, DOCX, PPTX, PNG, or JPG file."
                ), 400

            safe_name = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            temp_filename = f"{timestamp}_{safe_name}"

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)

            temp_path = os.path.join(upload_folder, temp_filename)
            file.save(temp_path)

            extension = _extension_of(safe_name)

            try:
                svg_source, warning = convert_uploaded_template(temp_path, extension)
            except TemplateConversionError as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return render_template(
                    "edit_template.html",
                    template=template,
                    error=str(e)
                ), 400

            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            base = secure_filename(template_name) or safe_name.rsplit(".", 1)[0]
            new_filename = f"{timestamp}_{base}.svg"
            svg_path = os.path.join(upload_folder, new_filename)

            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_source)

        update_template(
            template_id,
            template_name,
            description,
            status,
            _now(),
            file_name=new_filename
        )

        return redirect(url_for("templates.templates_list"))

    return render_template("edit_template.html", template=template)


@templates_bp.route("/templates/duplicate/<int:template_id>")
@login_required
def duplicate_template(template_id):

    template = get_template_by_id(template_id)
    if template is None:
        abort(404)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    original_path = os.path.join(upload_folder, template["file_name"])

    extension = _extension_of(template["file_name"])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{timestamp}_copy.{extension}" if extension else f"{timestamp}_copy"

    if os.path.exists(original_path):
        shutil.copyfile(original_path, os.path.join(upload_folder, new_filename))
    else:
        new_filename = template["file_name"]

    create_template(
        f"{template['template_name']} (Copy)",
        new_filename,
        _now(),
        "Inactive",
        template_type=template["template_type"] or "svg",
        description=template["description"] or ""
    )

    return redirect(url_for("templates.templates_list"))


@templates_bp.route("/templates/delete/<int:template_id>")
@login_required
def delete_template_route(template_id):

    template = get_template_by_id(template_id)

    if template is not None:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        file_path = os.path.join(upload_folder, template["file_name"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    delete_template(template_id)

    return redirect(url_for("templates.templates_list"))


@templates_bp.route("/templates/file/<int:template_id>")
@login_required
def template_file(template_id):
    """Serves the raw template file - used for the preview modal / <object>/<img> tags."""
    template = get_template_by_id(template_id)
    if template is None:
        abort(404)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        template["file_name"]
    )


@templates_bp.route("/api/templates/<int:template_id>/raw")
@login_required
def template_raw_svg(template_id):
    """Returns the raw SVG source as JSON text, for the in-browser preview panel."""
    template = get_template_by_id(template_id)
    if template is None:
        return jsonify({"success": False, "message": "Template not found."}), 404

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], template["file_name"])

    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "Template file is missing on disk."}), 404

    if template["template_type"] != "svg":
        return jsonify({"success": False, "message": "This template is not an SVG template."}), 400

    with open(file_path, "r", encoding="utf-8") as f:
        svg_source = f.read()

    return jsonify({"success": True, "svg": svg_source})