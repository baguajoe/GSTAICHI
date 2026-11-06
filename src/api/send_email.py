import smtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
import os

MAIL_SERVER = "smtp.gmail.com"

MAIL_PORT = 465
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv("GMAIL")
MAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Every email is sent from the school's Gmail with Vincent's name; replies go to Vincent unless a caller
# chooses otherwise (a member's question goes to Vincent with Reply-To set to the member).
FROM_NAME = os.getenv("EMAIL_FROM_NAME") or "Vincent Chu – The Tai Chi Company"
DEFAULT_REPLY_TO = os.getenv("EMAIL_REPLY_TO") or "chu.v@usa.com"


def send_email(recipient, body, subject, reply_to=None, html=None, headers=None):
    """body is the plain-text version; html, when given, is the designed version (both are sent).
    headers: extra headers such as List-Unsubscribe. Never logs the Gmail password."""
    reply_to = reply_to or DEFAULT_REPLY_TO
    if os.getenv("EMAIL_MODE", "smtp").lower() == "console":
        # Local development and tests: print instead of sending real email
        extra = f" [+html {len(html)} chars]" if html else ""
        print(f"EMAIL (not sent) to {recipient} (Reply-To: {reply_to}): {subject}{extra}\n{body}\n---")
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, MAIL_USERNAME))
    msg["To"] = recipient
    msg["Reply-To"] = reply_to
    msg["Message-ID"] = make_msgid(domain=(MAIL_USERNAME or "gstaichi.org").split("@")[-1])
    for name, value in (headers or {}).items():
        msg[name] = value
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise Exception(f"failed to send email: {type(e).__name__}: {str(e)[:200]}")
