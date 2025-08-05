import requests
from bs4 import BeautifulSoup
import hashlib
import smtplib
from email.mime.text import MIMEText
import os

URLS = {
    "caps": "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps",
    "news": "https://immi.homeaffairs.gov.au/what-we-do/whm-program/latest-news"
}

CACHE_FILE = "cache.txt"

def fetch_and_hash(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    text = soup.get_text()
    return hashlib.md5(text.encode()).hexdigest()

def read_previous_hashes():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        lines = f.readlines()
        return dict(line.strip().split("=") for line in lines)

def save_hashes(hashes):
    with open(CACHE_FILE, "w") as f:
        for key, h in hashes.items():
            f.write(f"{key}={h}\n")

def send_email(msg):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    to_email = os.getenv("TO_EMAIL")

    email = MIMEText(msg)
    email["Subject"] = "🔔 WHM Australia: Page Changed!"
    email["From"] = smtp_user
    email["To"] = to_email

    # Connect first
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()               # Say hello to server
        server.starttls()           # Start TLS
        server.ehlo()               # Re-identify after TLS
        server.login(smtp_user, smtp_pass)
        server.send_message(email)


def main():
    prev = read_previous_hashes()
    updated = {}
    changed = []

    for key, url in URLS.items():
        new_hash = fetch_and_hash(url)
        updated[key] = new_hash
        if key not in prev or prev[key] != new_hash:
            changed.append(key)

    if changed:
        msg = "The following WHM pages have changed:\n\n" + "\n".join(
            f"{key}: {URLS[key]}" for key in changed)
        send_email(msg)

    save_hashes(updated)

if __name__ == "__main__":
    main()
# trigger test run
