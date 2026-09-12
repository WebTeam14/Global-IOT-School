from flask import Blueprint, render_template, request, redirect, url_for

from database.models import get_certificate_by_certificate_id

verify_bp = Blueprint("verify", __name__)


@verify_bp.route("/verify", methods=["GET", "POST"])
def verify_search():

    if request.method == "POST":
        certificate_id = request.form["certificate_id"].strip()
        return redirect(url_for("verify.verify_certificate", certificate_id=certificate_id))

    return render_template("verify_search.html")


@verify_bp.route("/verify/<certificate_id>")
def verify_certificate(certificate_id):

    certificate = get_certificate_by_certificate_id(certificate_id)

    return render_template(
        "verify_result.html",
        certificate=certificate,
        certificate_id=certificate_id
    )