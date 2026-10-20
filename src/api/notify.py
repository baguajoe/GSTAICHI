"""Emails to the school (SiteSettings.notification_email) and to members. Never breaks a request if sending fails."""
from .models import SiteSettings
from .send_email import send_email


def email(recipient, subject, body):
    if not recipient:
        return False
    try:
        send_email(recipient=recipient, subject=subject, body=body)
        return True
    except Exception as e:
        print(f"Email to {recipient} failed: {e}")
        return False


def notify_school(subject, body):
    settings = SiteSettings.get()
    return email(settings.notification_email, f"[{settings.app_name}] {subject}", body)


def signature():
    settings = SiteSettings.get()
    lines = [settings.school_name or settings.app_name]
    if settings.contact_phone:
        lines.append(f"Need help? Call {settings.contact_phone}")
    return "\n".join(lines)
