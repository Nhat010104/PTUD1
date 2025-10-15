"""Simple conversational agent orchestrating product description generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Literal, Optional

from fastapi import HTTPException

from . import content, seo
from .gemini import get_model


AgentRole = Literal["user", "assistant"]


@dataclass
class AgentMessage:
    role: AgentRole
    content: str


@dataclass
class AgentResult:
    reply: str
    finished: bool
    description: Optional[str] = None
    seo_score: Optional[int] = None
    seo_factors: Optional[list[str]] = None
    style: Optional[str] = None


EXTRACTION_PROMPT = """
Bạn là bộ phân tích thông tin sản phẩm.
Từ cuộc hội thoại giữa người dùng và trợ lý dưới đây, hãy trích xuất thông tin sản phẩm và phong cách viết.

- Nếu chưa có thông tin sản phẩm rõ ràng, trả về JSON với product_info là chuỗi rỗng.
- Nếu chưa có phong cách viết, đặt style = "Marketing".
- Chỉ trả về một JSON hợp lệ với hai khóa: product_info, style.

Cuộc hội thoại:
{conversation}
"""


FOLLOW_UP_PROMPT = """
Bạn là một AI agent thân thiện hỗ trợ tạo content.
Người dùng chưa cung cấp đủ thông tin. Hãy hỏi họ rõ ràng để lấy thông tin sản phẩm cần thiết
(ví dụ: loại sản phẩm, đặc điểm nổi bật, đối tượng khách hàng, phong cách mong muốn).
Trả lời bằng tiếng Việt.
"""


FINAL_PROMPT = """
Bạn là chuyên gia Content AI. Dựa trên mô tả chi tiết dưới đây, hãy tạo câu trả lời tự tin, súc tích:

Thông tin sản phẩm: {product_info}
Phong cách: {style}

Đã tạo mô tả với điểm SEO {seo_score}/100.
Hãy tóm tắt lợi ích chính và hướng dẫn người dùng có thể tải xuống hoặc xem chi tiết trong ứng dụng.
Trả lời bằng tiếng Việt.
"""


def _format_conversation(messages: List[AgentMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        prefix = "Người dùng" if message.role == "user" else "Trợ lý"
        lines.append(f"{prefix}: {message.content}")
    return "\n".join(lines)


def generate_session_title(content: str) -> str:
    sanitized = " ".join(content.split())[:80]
    return sanitized or "Phiên agent"


def _extract_requirements(api_key: str, messages: List[AgentMessage]) -> tuple[str, str]:
    model = get_model(api_key)
    formatted = _format_conversation(messages)
    raw = model.generate_content(EXTRACTION_PROMPT.format(conversation=formatted))
    if not raw or not raw.text:
        return "", "Marketing"
    try:
        data = json.loads(raw.text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="Không thể phân tích thông tin sản phẩm") from exc
    product_info = str(data.get("product_info", "")).strip()
    style = str(data.get("style", "Marketing")).strip() or "Marketing"
    return product_info, style


def _build_follow_up(api_key: str) -> str:
    model = get_model(api_key)
    response = model.generate_content(FOLLOW_UP_PROMPT)
    return response.text.strip() if response and response.text else "Bạn có thể cung cấp thêm thông tin về sản phẩm không?"


def run_agent(api_key: str, messages: List[AgentMessage]) -> AgentResult:
    if not messages:
        raise HTTPException(status_code=400, detail="Thiếu hội thoại đầu vào")

    product_info, style = _extract_requirements(api_key, messages)
    if not product_info:
        follow_up = _build_follow_up(api_key)
        return AgentResult(reply=follow_up, finished=False)

    description = content.generate_from_text(api_key, product_info, style)
    if not description:
        raise HTTPException(status_code=502, detail="Không tạo được mô tả từ thông tin đã cung cấp")

    seo_score, seo_factors = seo.calculate_seo_score(description)

    model = get_model(api_key)
    summary_prompt = FINAL_PROMPT.format(
        product_info=product_info,
        style=style,
        seo_score=seo_score,
    )
    reply_content = model.generate_content(summary_prompt)
    reply = reply_content.text.strip() if reply_content and reply_content.text else description

    return AgentResult(
        reply=reply,
        finished=True,
        description=description,
        seo_score=seo_score,
        seo_factors=seo_factors,
        style=style,
    )
