import smtplib
from email.message import EmailMessage


def send_certificate_email(smtp_email, smtp_app_password, recipient_email, participant_name, event_name, pdf_path):

    msg = EmailMessage()

    msg["Subject"] = f"Your Certificate - {event_name}"
    msg["From"] = smtp_email
    msg["To"] = recipient_email

    msg.set_content(
        f"Dear {participant_name},\n\n"
        f"Congratulations! Please find attached your certificate for {event_name}.\n\n"
        f"Best regards,\nGlobal IOT School Team"
    )

    # Attach the PDF file
    with open(pdf_path, "rb") as f:
        file_data = f.read()
        file_name = pdf_path.split("\\")[-1].split("/")[-1]

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="pdf",
        filename=file_name
    )

    # Connect to Gmail's SMTP server over a secure connection and send
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(smtp_email, smtp_app_password)
        smtp.send_message(msg)