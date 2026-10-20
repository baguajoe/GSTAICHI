import smtplib
from email.message import EmailMessage
import os

MAIL_SERVER = "smtp.gmail.com"

MAIL_PORT = 465
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv("GMAIL")
MAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")


def send_email(recipient, body, subject):
    if os.getenv("EMAIL_MODE", "smtp").lower() == "console":
        # Local development and tests: print instead of sending real email
        print(f"EMAIL (not sent) to {recipient}: {subject}\n{body}\n---")
        return
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            smg = EmailMessage()
            smg["Subject"] = subject
            smg["From"] = MAIL_USERNAME
            smg["To"] = recipient
            smg.set_content(body)
            server.send_message(smg)
    except smtplib.SMTPException as e: 
        #log the exception e
        raise Exception(f"failed to send email: {str(e)}")