import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Send email via SMTP.
    Falls back to console print if credentials not configured.
    """
    smtp_server = os.getenv('MAIL_SERVER')
    smtp_port = int(os.getenv('MAIL_PORT', 587))
    smtp_user = os.getenv('MAIL_USERNAME')
    smtp_pass = os.getenv('MAIL_PASSWORD')
    sender = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@techservices.pl')

    if not smtp_user or not smtp_pass:
        print(f"[EMAIL - DEV] To: {to_email} | Subject: {subject}\n{body}")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender, to_email, msg.as_string())
        print(f"[EMAIL] Sent to {to_email}: {subject}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


def send_reservation_confirmation(to_email: str, reservation):
    subject = "✅ Potwierdzenie rezerwacji — TECH.SERVICES"
    slot_time = (
        reservation.time_slot.start_time.strftime('%d.%m.%Y %H:%M')
        if reservation.time_slot
        else (reservation.manual_datetime.strftime('%d.%m.%Y %H:%M') if reservation.manual_datetime else 'Do ustalenia')
    )
    body = (
        f"Cześć!\n\n"
        f"Twoja rezerwacja została potwierdzona.\n\n"
        f"📅 Termin: {slot_time}\n"
        f"🔗 Link do spotkania: {reservation.meeting_link or 'Wkrótce'}\n\n"
        f"Do zobaczenia!\n"
        f"Zespół TECH.SERVICES"
    )
    html_body = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
      <h2 style="border-bottom:2px solid #000;padding-bottom:16px">TECH.SERVICES</h2>
      <h3>✅ Rezerwacja potwierdzona</h3>
      <table style="width:100%;border-collapse:collapse;margin:24px 0">
        <tr><td style="padding:8px 0;color:#666">Termin</td><td style="padding:8px 0;font-weight:700">{slot_time}</td></tr>
        <tr><td style="padding:8px 0;color:#666">Spotkanie</td>
            <td style="padding:8px 0"><a href="{reservation.meeting_link or '#'}" style="color:#000">{reservation.meeting_link or 'Wkrótce'}</a></td></tr>
      </table>
      <p style="color:#555">Życzymy miłego dnia i do zobaczenia!</p>
      <p style="font-weight:700">Zespół TECH.SERVICES</p>
    </div>
    """
    send_email(to_email, subject, body, html_body)
