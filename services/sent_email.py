import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER = "astelpauly2002@gmail.com"
GMAIL_PASSWORD = os.getenv("gmail_password")
TRACKING_BASE_URL = "https://email-tracking-0au6.onrender.com/track"


def send_email(lead_id: str, user_id: str, campaign_id: str, receiver_email: str):
    tracking_url = f"{TRACKING_BASE_URL}?u={user_id}&c={campaign_id}&l={lead_id}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Test Campaign Email"
    msg["From"] = SENDER
    msg["To"] = receiver_email

    html_content = f"""
<html>
  <body>
    <p>Hello,</p>
    <p>This is campaign mail.</p>

    <!-- Hidden Tracking Pixel -->
    <img src="{tracking_url}" width="1" height="1" style="display:none;" />
  </body>
</html>
"""

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, GMAIL_PASSWORD)
        server.sendmail(SENDER, receiver_email, msg.as_string())

    print(f"Email sent to {receiver_email} (lead_id={lead_id})")
