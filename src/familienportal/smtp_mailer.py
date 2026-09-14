from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from sqlalchemy import select

from familienportal.calendar_models import CalendarEvent
from familienportal.config import Settings, get_settings
from familienportal.database import SessionLocal
from familienportal.job_state import JobDelivery
from familienportal.models import User


class MailDeliveryError(RuntimeError):
    pass


def send_mail(settings: Settings, recipient: str, subject: str, body: str) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        raise MailDeliveryError("SMTP ist nicht vollständig konfiguriert")
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
            client.ehlo()
            if settings.smtp_starttls:
                client.starttls()
                client.ehlo()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password or "")
            client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise MailDeliveryError(str(exc)) from exc


def deliver_queued_reminders() -> int:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delivered = 0
    with SessionLocal() as db:
        jobs = db.scalars(select(JobDelivery).where(JobDelivery.scheduled_for <= now, JobDelivery.status.in_(["pending", "failed"]), JobDelivery.attempts < 5)).all()
        for job in jobs:
            event = db.get(CalendarEvent, job.event_id)
            user = db.get(User, job.user_id)
            if not event or not user or event.deleted_at is not None:
                job.status = "cancelled"
                continue
            job.attempts += 1
            job.last_attempt_at = now
            body = f"{event.title}\nBeginn: {event.starts_at}\n"
            if event.location:
                body += f"Ort: {event.location}\n"
            try:
                send_mail(settings, user.email, f"Terminerinnerung: {event.title}", body)
            except MailDeliveryError as exc:
                job.status = "failed"
                job.message = str(exc)[:500]
            else:
                job.status = "delivered"
                job.message = None
                job.delivered_at = now
                delivered += 1
        db.commit()
    return delivered
