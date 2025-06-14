import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
import requests

load_dotenv("mail_data.env")  # または ".env"

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(charset, errors="ignore")
                return body
        return ""
    else:
        charset = msg.get_content_charset() or "utf-8"
        body = msg.get_payload(decode=True).decode(charset, errors="ignore")
        return body

def fetch_all_unread_emails():
    emails = []
    with imaplib.IMAP4_SSL(IMAP_SERVER, 993) as mail:
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()
        if not mail_ids:
            return emails
        for mail_id in mail_ids:
            result, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            body = get_email_body(msg)
            emails.append((subject, body))
    return emails

def send_each_email_to_discord(emails):
    for subject, body in emails:
        snippet = body[:1500].replace("\n", " ")
        content = f"件名: {subject}\n本文: {snippet}"
        requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

if __name__ == "__main__":
    emails = fetch_all_unread_emails()
    if emails:
        send_each_email_to_discord(emails)
    else:
        print("未読メールはありません。")