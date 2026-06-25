"""
Email Sender Module
Uses Python smtplib and email libraries to send HTML emails
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')


def build_html(title, body, tracking_id=None):
    tid_block = ''
    if tracking_id:
        tid_block = f'''
        <div style="background:#e8f5ee;border:1px solid #b8ddc8;border-radius:10px;padding:14px;margin-top:16px;text-align:center">
            <div style="font-size:11px;color:#6b7f6b;margin-bottom:5px">Your Tracking ID</div>
            <div style="font-size:22px;font-weight:800;color:#1a6b3c">{tracking_id}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html><body style="margin:0;background:#f0f4f0;font-family:Arial,sans-serif">
<div style="max-width:560px;margin:0 auto;padding:24px 16px">
    <div style="background:#1a6b3c;color:#fff;padding:18px 22px;border-radius:12px 12px 0 0;text-align:center">
        <div style="font-size:20px;font-weight:800">🏛️ CivicTrack</div>
        <div style="font-size:11px;opacity:.75;margin-top:3px">Smart Civic Complaint Management</div>
    </div>
    <div style="background:#fff;padding:24px 22px;border-radius:0 0 12px 12px;border:1px solid #dce8dc;border-top:none">
        <h3 style="color:#1a2e1a;margin-bottom:12px;font-size:16px">{title}</h3>
        {body}
        {tid_block}
        <div style="margin-top:20px;padding-top:14px;border-top:1px solid #dce8dc;font-size:11px;color:#9aaa9a;text-align:center">
            CivicTrack — Bridging Citizens and Government<br>
            Powered by Python | Flask | OpenCV | Pandas
        </div>
    </div>
</div></body></html>'''


def send_email(to, subject, title, body, tracking_id=None, attachment=None, attachment_name=None):
    """Send HTML email using Python smtplib"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f'"CivicTrack" <{GMAIL_USER}>'
        msg['To']      = to
        msg['Subject'] = subject

        html = build_html(title, body, tracking_id)
        msg.attach(MIMEText(html, 'html'))

        # Attach PDF if provided
        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_name or "report.pdf"}"')
            msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, to, msg.as_string())

        print(f'📧 Email sent to {to}')
        return True
    except Exception as e:
        print(f'❌ Email error: {e}')
        return False


def send_confirmation(email, name, complaint):
    """Send complaint registration confirmation email"""
    return send_email(
        to=email,
        subject=f"Complaint Registered — {complaint.get('trackingId')}",
        title=f"Hello {name}, your complaint has been registered!",
        body=f'''
        <p style="color:#6b7f6b;font-size:14px;line-height:1.6">
            Your complaint has been successfully submitted and automatically routed to
            <strong>{complaint.get('department', 'the concerned department')}</strong>.
        </p>
        <div style="background:#f0f4f0;border-radius:10px;padding:14px;margin-top:14px;font-size:13px">
            <div style="margin-bottom:6px"><strong>Issue:</strong> {complaint.get('title')}</div>
            <div style="margin-bottom:6px"><strong>Type:</strong> {complaint.get('issueType','').replace('_',' ').title()}</div>
            <div style="margin-bottom:6px"><strong>Priority:</strong> {complaint.get('priority','').upper()}</div>
            <div><strong>Python AI Confidence:</strong> {round(float(complaint.get('aiClassification',{}).get('confidence',0))*100,1)}%</div>
        </div>''',
        tracking_id=complaint.get('trackingId')
    )


def send_status_update(email, name, complaint, message):
    """Send status update email to citizen"""
    status_msgs = {
        'acknowledged': 'Your complaint has been acknowledged and is under review.',
        'in_progress':  'Work has started on resolving your complaint.',
        'resolved':     'Great news! Your complaint has been successfully resolved.',
        'rejected':     'Unfortunately, your complaint could not be addressed at this time.',
        'assigned':     'A field officer has been assigned to handle your complaint.',
    }
    status = complaint.get('status', '')
    return send_email(
        to=email,
        subject=f"Complaint Update — {complaint.get('trackingId')}",
        title=f"Update on your complaint",
        body=f'''
        <p style="color:#6b7f6b;font-size:14px;line-height:1.6">
            Hello {name},<br><br>
            {status_msgs.get(status, 'Your complaint status has been updated.')}
        </p>
        {f'<div style="background:#f0f4f0;border-radius:10px;padding:14px;margin-top:12px;font-size:13px"><strong>Message from authorities:</strong> {message}</div>' if message else ''}''',
        tracking_id=complaint.get('trackingId')
    )
