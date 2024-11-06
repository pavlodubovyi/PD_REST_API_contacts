import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from app.auth import create_email_token
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASS"),
    MAIL_FROM=os.getenv("EMAIL_FROM"),
    MAIL_PORT=os.getenv("EMAIL_PORT"),
    MAIL_SERVER=os.getenv("SMTP_SERVER"),
    MAIL_FROM_NAME="Pavlo",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

FRONTEND_URL = os.getenv("FRONTEND_URL")
print(FRONTEND_URL)


async def send_verification_email(email: EmailStr, username: str, host: str):
    try:
        token_verification = await create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": FRONTEND_URL,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_reset_email(email: EmailStr, host: str, token: str):
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        template_body={"host": host, "token": token, "username": email.split("@")[0]},
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="reset_pass_email.html")
