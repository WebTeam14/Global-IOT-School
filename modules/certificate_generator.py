import base64
from flask import render_template
from weasyprint import HTML


def generate_certificate(output_path, name, event_name, date, certificate_id, qr_code_path):

    with open(qr_code_path, "rb") as f:
        qr_base64 = base64.b64encode(f.read()).decode("utf-8")

    qr_data_uri = f"data:image/png;base64,{qr_base64}"

    html_string = render_template(
        "certificate_pdf.html",
        name=name,
        event_name=event_name,
        date=date,
        certificate_id=certificate_id,
        qr_data_uri=qr_data_uri
    )

    HTML(string=html_string, base_url=".").write_pdf(output_path)

    return output_path