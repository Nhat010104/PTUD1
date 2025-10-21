"""SMTP email helpers."""

import smtplib
from email.message import EmailMessage
from typing import Optional

from ..config import get_settings


class EmailConfigurationError(RuntimeError):
    """Raised when SMTP configuration is missing."""


def _build_message(subject: str, body: str, sender: str, recipient: str, reply_to: Optional[str] = None) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)
    return message


def send_password_reset_email(recipient: str, code: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_sender:
        raise EmailConfigurationError("SMTP host hoặc sender chưa được cấu hình")

    username = settings.smtp_username
    password = settings.smtp_password
    if username and not password:
        raise EmailConfigurationError("SMTP password chưa được cấu hình")

    subject = "Mã đặt lại mật khẩu"
    body = (
            "Kính chào Quý khách,\n\n"
                "Chúng tôi đã nhận được yêu cầu đặt lại mật khẩu cho tài khoản của Quý khách.\n"
                f"Mã xác nhận để khôi phục mật khẩu của Quý khách là: {code}\n\n"
                "Mã có hiệu lực trong vòng 30 phút kể từ thời điểm nhận email này.\n"
                "Nếu Quý khách không gửi yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.\n\n"
                "Trân trọng,\n"
                "Đội ngũ Hỗ trợ Khách hàng\n"
                "[AI Mô Tả Sản Phẩm]"
    )

    message = _build_message(subject, body, settings.smtp_sender, recipient)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        try:
            server.starttls()
            server.ehlo()
        except smtplib.SMTPException:
            pass

        if username:
            server.login(username, password or "")

        server.send_message(message)
