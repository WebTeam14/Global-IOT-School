import os
from dotenv import load_dotenv

load_dotenv()

# Absolute path to the project's root folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Where uploaded certificate templates get stored
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "templates")

# Only these file types are allowed to be uploaded
ALLOWED_EXTENSIONS = {"svg", "png", "jpg", "jpeg", "pdf", "docx", "pptx"}

# Max upload size: 5 MB (in bytes)
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

# Default text positions on a certificate template (x, y) in pixels.
# Open your template file in an image editor (e.g. Paint, Photoshop) and
# hover your mouse over where you want each text to appear to find these values.
CERTIFICATE_TEXT_POSITIONS = {
    "name": {
        "cover_box": (120, 160, 410, 222),
        "text_position": (135, 178)
    },
    "event": {
        "cover_box": (55, 222, 480, 270),
        "text_position": (65, 235)
    },
    "date": {
        "cover_box": (65, 285, 230, 332),
        "text_position": (65, 300)
    },
    "certificate_id": {
        "cover_box": (335, 335, 480, 368),
        "text_position": (340, 345)
    },
}

CERTIFICATE_FONT_SIZE = 15

QR_CODE_POSITION = (440, 20)   # top-right corner-ish; adjust after previewing
QR_CODE_SIZE = 80

GENERATED_FOLDER = os.path.join(BASE_DIR, "generated_certificates")
GENERATED_SVG_FOLDER = os.path.join(BASE_DIR, "generated_certificates", "svg")
GENERATED_PNG_FOLDER = os.path.join(BASE_DIR, "generated_certificates", "png")

EMAIL_AUTOMATION_ENABLED = os.environ.get("EMAIL_AUTOMATION_ENABLED", "true").lower() == "true"
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")

SITE_BASE_URL = "http://127.0.0.1:5000"

QR_FOLDER = os.path.join(BASE_DIR, "generated_certificates", "qr_codes")