import os


def delete_certificate_files(config, file_name, qr_filename, svg_filename=None, png_filename=None):
    """
    Deletes the generated PDF, QR code, and (if present) SVG/PNG export
    files for one certificate. Returns a list of error messages (empty list
    = fully successful). Missing files are NOT treated as errors (already
    gone is fine). svg_filename/png_filename are optional so existing
    callers that only know about the PDF keep working unchanged.
    """

    errors = []

    if file_name:
        pdf_path = os.path.join(config["GENERATED_FOLDER"], file_name)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError as e:
                errors.append(f"Could not delete PDF '{file_name}': {e}")

    if qr_filename:
        qr_path = os.path.join(config["QR_FOLDER"], qr_filename)
        if os.path.exists(qr_path):
            try:
                os.remove(qr_path)
            except OSError as e:
                errors.append(f"Could not delete QR code '{qr_filename}': {e}")

    if svg_filename and "GENERATED_SVG_FOLDER" in config:
        svg_path = os.path.join(config["GENERATED_SVG_FOLDER"], svg_filename)
        if os.path.exists(svg_path):
            try:
                os.remove(svg_path)
            except OSError as e:
                errors.append(f"Could not delete SVG '{svg_filename}': {e}")

    if png_filename and "GENERATED_PNG_FOLDER" in config:
        png_path = os.path.join(config["GENERATED_PNG_FOLDER"], png_filename)
        if os.path.exists(png_path):
            try:
                os.remove(png_path)
            except OSError as e:
                errors.append(f"Could not delete PNG '{png_filename}': {e}")

    return errors