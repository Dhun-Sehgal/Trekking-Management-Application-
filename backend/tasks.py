import os
import csv
import smtplib
import requests
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app
from sqlalchemy import func, desc

from workers import celery
from app import db
from models import User, Trek, Booking, BOOKING_STATUS_BOOKED


def _send_email(to_email, subject, html_body):
    cfg = current_app.config
    if not cfg.get("MAIL_USERNAME") or not cfg.get("MAIL_PASSWORD"):
        current_app.logger.warning(
            f"MAIL_USERNAME/MAIL_PASSWORD not configured - skipping real send. "
            f"Would have emailed '{subject}' to {to_email}"
        )
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["MAIL_USERNAME"]
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"]) as server:
        server.starttls()
        server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
        server.sendmail(cfg["MAIL_USERNAME"], to_email, msg.as_string())
    return True


def _send_gchat(message):
    url = current_app.config.get("GCHAT_WEBHOOK_URL")
    if not url:
        current_app.logger.warning(f"GCHAT_WEBHOOK_URL not configured - skipping. Message: {message}")
        return False
    try:
        requests.post(url, json={"text": message}, timeout=5)
        return True
    except requests.RequestException as exc:
        current_app.logger.error(f"Failed to send G-Chat webhook: {exc}")
        return False


@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    """Scheduled daily job: notify users about upcoming treks (within next 3 days)."""
    window_end = date.today() + timedelta(days=3)
    upcoming_bookings = (
        Booking.query.join(Trek)
        .filter(
            Booking.status == BOOKING_STATUS_BOOKED,
            Trek.start_date.isnot(None),
            Trek.start_date >= date.today(),
            Trek.start_date <= window_end,
        )
        .all()
    )

    sent = 0
    for booking in upcoming_bookings:
        user = booking.user
        trek = booking.trek
        message = (
            f"Reminder: Hi {user.name}, your trek '{trek.name}' at {trek.location} "
            f"starts on {trek.start_date.isoformat()}. Please be ready with your gear "
            f"and arrive at the meeting point on time!"
        )
        _send_email(user.email, f"Upcoming Trek Reminder: {trek.name}", f"<p>{message}</p>")
        _send_gchat(message)
        sent += 1

    return {"reminders_sent": sent, "window_end": window_end.isoformat()}


@celery.task(name="tasks.generate_monthly_report")
def generate_monthly_report():
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    first_of_last_month = last_month_end.replace(day=1)

    treks_conducted = Trek.query.filter(
        Trek.status == "Completed",
        Trek.end_date >= first_of_last_month,
        Trek.end_date <= last_month_end,
    ).count()

    participants = (
        db.session.query(Booking.user_id)
        .join(Trek)
        .filter(
            Trek.status == "Completed",
            Trek.end_date >= first_of_last_month,
            Trek.end_date <= last_month_end,
        )
        .distinct()
        .count()
    )

    popular = (
        db.session.query(Trek.name, func.count(Booking.id).label("cnt"))
        .join(Booking, Booking.trek_id == Trek.id)
        .group_by(Trek.id)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )

    rows = "".join(f"<tr><td>{name}</td><td>{count}</td></tr>" for name, count in popular)
    html = f"""
    <html><body>
    <h2>Monthly Trekking Activity Report</h2>
    <p>Period: {first_of_last_month.isoformat()} to {last_month_end.isoformat()}</p>
    <ul>
      <li>Treks conducted: {treks_conducted}</li>
      <li>Users participated: {participants}</li>
    </ul>
    <h3>Most Popular Treks</h3>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Trek Name</th><th>Bookings</th></tr>
      {rows or '<tr><td colspan="2">No data</td></tr>'}
    </table>
    </body></html>
    """
    from pathlib import Path
    report_dir = Path(current_app.config["EXPORT_DIR"])
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / "monthly_report.html"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html)

    admin_email = current_app.config.get("ADMIN_EMAIL")
    _send_email(admin_email, "Monthly Trekking Activity Report", html)

    return {
        "treks_conducted": treks_conducted,
        "participants": participants,
        "period": f"{first_of_last_month.isoformat()} to {last_month_end.isoformat()}",
    }



@celery.task(name="tasks.export_booking_history_csv")
def export_booking_history_csv(user_id):
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}

    export_dir = current_app.config["EXPORT_DIR"]
    os.makedirs(export_dir, exist_ok=True)
    filename = f"booking_history_user_{user_id}.csv"
    filepath = os.path.join(export_dir, filename)

    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Trek Name", "Location", "Booking Status", "Booking Date", "Trek Start Date"])
        for b in bookings:
            writer.writerow(
                [
                    user_id,
                    b.trek.name if b.trek else "",
                    b.trek.location if b.trek else "",
                    b.status,
                    b.booking_date.isoformat() if b.booking_date else "",
                    b.trek.start_date.isoformat() if b.trek and b.trek.start_date else "",
                ]
            )

    message = f"Hi {user.name}, your trekking history export is ready ({len(bookings)} records)."
    _send_gchat(message)
    _send_email(user.email, "Your Booking History Export is Ready", f"<p>{message}</p>")

    return {"filename": filename, "path": filepath, "record_count": len(bookings)}
