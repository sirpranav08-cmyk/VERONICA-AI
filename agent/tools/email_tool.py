"""
V.E.R.O.N.I.C.A Email Tool
Supports Gmail and Outlook — send and read emails
"""
import imaplib
import smtplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

# Load credentials from environment
from dotenv import load_dotenv
load_dotenv("D:/jarvis-agent/agent/.env")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
OUTLOOK_ADDRESS = os.getenv("OUTLOOK_ADDRESS", "")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_APP_PASSWORD", "")

EMAIL_CONFIG = {
    "gmail": {
        "address": GMAIL_ADDRESS,
        "password": GMAIL_PASSWORD,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
    },
    "outlook": {
        "address": OUTLOOK_ADDRESS,
        "password": OUTLOOK_PASSWORD,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
    }
}

def send_email(to: str, subject: str, body: str, service: str = "gmail") -> str:
    try:
        cfg = EMAIL_CONFIG.get(service.lower(), EMAIL_CONFIG["gmail"])
        if not cfg["address"] or not cfg["password"]:
            return f"Error: {service} credentials not set in .env file."
        msg = MIMEMultipart()
        msg["From"] = cfg["address"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["address"], cfg["password"])
            server.send_message(msg)
        return f"Email sent to {to} with subject '{subject}'"
    except Exception as e:
        return f"Error sending email: {e}"

def read_emails(count: int = 5, service: str = "gmail") -> str:
    try:
        cfg = EMAIL_CONFIG.get(service.lower(), EMAIL_CONFIG["gmail"])
        if not cfg["address"] or not cfg["password"]:
            return f"Error: {service} credentials not set in .env file."
        mail = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"])
        mail.login(cfg["address"], cfg["password"])
        mail.select("INBOX")
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        if not email_ids:
            return f"No unread emails in {service}."
        latest = email_ids[-count:]
        results = []
        for eid in reversed(latest):
            status, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            sender = msg.get("From", "Unknown")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors='ignore')[:200]
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')[:200]
            results.append(f"From: {sender}\nSubject: {subject}\nPreview: {body[:100]}")
        mail.logout()
        return f"{len(results)} unread emails:\n\n" + "\n---\n".join(results)
    except Exception as e:
        return f"Error reading emails: {e}"

def get_email_count(service: str = "gmail") -> str:
    try:
        cfg = EMAIL_CONFIG.get(service.lower(), EMAIL_CONFIG["gmail"])
        if not cfg["address"] or not cfg["password"]:
            return f"Error: {service} credentials not set in .env file."
        mail = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"])
        mail.login(cfg["address"], cfg["password"])
        mail.select("INBOX")
        status, messages = mail.search(None, "UNSEEN")
        count = len(messages[0].split()) if messages[0] else 0
        mail.logout()
        return f"You have {count} unread emails in {service}."
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print("Testing email...")
    print(get_email_count("gmail"))