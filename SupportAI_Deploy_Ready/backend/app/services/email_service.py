import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
APP_FRONTEND_URL = os.getenv("APP_FRONTEND_URL", "http://localhost:3000").rstrip("/")


def send_unanswered_alert(company_name: str, question: str):
    """
    Sends an email to the admin when the chatbot could not answer a question.
    Runs synchronously — call it in a background task so it doesn't block the response.
    """
    if not SMTP_USER or not SMTP_PASSWORD or not ADMIN_EMAIL:
        print("[Email] SMTP credentials not configured — skipping email alert.")
        return

    try:
        subject = f"[{company_name}] Unanswered Customer Question"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
            <div style="max-width: 560px; margin: auto; background: white; border-radius: 10px;
                        padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                <h2 style="color: #7c3aed; margin-top: 0;">⚠️ Unanswered Question Alert</h2>

                <p style="color: #444;">
                    A customer asked a question that your chatbot <strong>could not answer</strong>
                    for <strong>{company_name}</strong>.
                </p>

                <div style="background: #f8f4ff; border-left: 4px solid #7c3aed;
                            padding: 16px 20px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; color: #333; font-size: 16px;">
                        💬 <em>"{question}"</em>
                    </p>
                </div>

                <p style="color: #444;">
                    Log in to your dashboard to provide an answer.
                    Once submitted, your chatbot will automatically answer
                    this question for future customers.
                </p>

                <a href="{APP_FRONTEND_URL}/dashboard"
                   style="display: inline-block; background: #7c3aed; color: white;
                          padding: 12px 24px; border-radius: 8px; text-decoration: none;
                          font-weight: bold; margin-top: 10px;">
                    Answer in Dashboard →
                </a>

                <p style="color: #aaa; font-size: 12px; margin-top: 30px;">
                    This is an automated alert from SupportAI.
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ADMIN_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ADMIN_EMAIL, msg.as_string())

        print(f"[Email] Unanswered alert sent to {ADMIN_EMAIL} for question: '{question}'")

    except Exception as e:
        print(f"[Email] Failed to send alert: {e}")