"""Email utilities for transactional messages."""

import smtplib
from email.message import EmailMessage

from ..config import get_settings


def _require_smtp_settings() -> tuple[str, int, str, str, str]:
    settings = get_settings()
    host = settings.smtp_host
    port = settings.smtp_port
    username = settings.smtp_username
    password = settings.smtp_password
    sender = settings.smtp_sender
    if not all([host, port, username, password, sender]):
        raise RuntimeError("Thiếu cấu hình SMTP")
    return host, int(port), username, password, sender


def send_password_reset_code(recipient: str, code: str) -> None:
    host, port, username, password, sender = _require_smtp_settings()
    message = EmailMessage()
    message["Subject"] = "Mã xác thực đặt lại mật khẩu"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        """Xin chào,

Bạn đã yêu cầu đặt lại mật khẩu. Mã xác thực của bạn là: {code}
Mã có hiệu lực trong 30 phút. Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.

Trân trọng.
"""
.format(code=code)
    )

    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
    except smtplib.SMTPException as exc:
        raise RuntimeError("Không thể gửi email xác thực") from exc
