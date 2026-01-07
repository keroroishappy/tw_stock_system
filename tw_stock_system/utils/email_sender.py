# tw_stock_system/utils/email_sender.py
import smtplib
from email.mime.text import MIMEText
import config

def send_email(subject, body):
    if not config.EMAIL_USER or "your_email" in config.EMAIL_USER:
        print("[System] Email not configured. Skipping.")
        return

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_USER
        msg['To'] = config.EMAIL_TARGET
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(config.EMAIL_USER, config.EMAIL_PASS)
            smtp.sendmail(config.EMAIL_USER, config.EMAIL_TARGET, msg.as_string())
        print(f"[System] Email sent: {subject}")
    except Exception as e:
        print(f"[Error] Email failed: {e}")