"""Content generation helpers leveraging Gemini."""

from typing import Optional

from PIL import Image

from .gemini import get_model


STYLE_PROMPTS = {
    "Tiếp thị": """
        Viết theo phong cách MARKETING mạnh mẽ, gợi cảm xúc, kích thích mua hàng.
        Sử dụng từ ngữ hấp dẫn, tạo cảm giác KHAN HIẾM và GIÁ TRỊ CAO.
    """,
    "Chuyên nghiệp": """
        Viết theo phong cách CHUYÊN NGHIỆP, trang trọng, chính xác.
        Tập trung vào thông tin chi tiết, nguồn gốc, chất lượng sản phẩm.
    """,
    "Thân thiện": """
        Viết theo phong cách THÂN THIỆN, gần gũi, dễ hiểu.
        Như đang tư vấn cho bạn bè, tự nhiên và chân thực.
    """,
    "Kể chuyện": """
        Viết theo phong cách KỂ CHUYỆN, tạo câu chuyện hấp dẫn về sản phẩm.
        Mở đầu bằng câu chuyện, lồng ghép thông tin sản phẩm vào câu chuyện.
    """,
}


def get_style_prompt(style: str) -> str:
    """Return the Gemini writing style prompt."""
    return STYLE_PROMPTS.get(style, STYLE_PROMPTS["Tiếp thị"])


def _image_prompt(style: str) -> str:
    return f"""Viết mô tả bán hàng cho sản phẩm trái cây trong ảnh. {get_style_prompt(style)}

Trả về theo định dạng:
🎯 [Tiêu đề sản phẩm ngắn gọn, có từ khóa]

✨ [Slogan 1 câu ấn tượng]

📝 Mô tả: [100-150 từ miêu tả sản phẩm hấp dẫn, có nguồn gốc, lợi ích và call-to-action]

💎 Điểm nổi bật:
• [Chất lượng]
• [Nguồn gốc]
• [Hương vị]
• [Dinh dưỡng]
• [Độ tươi]

🌟 Lợi ích: [3-4 lợi ích cụ thể]

🎁 Cam kết: [Chất lượng, đổi trả, giao hàng]

🍽️ Gợi ý: [2-3 cách dùng]

#️⃣ Từ khóa: [5-7 hashtag/từ khóa, cách nhau bằng dấu phẩy]

Viết TIẾNG VIỆT tự nhiên."""


def _text_prompt(product_info: str, style: str) -> str:
    return f"""Viết mô tả bán hàng cho: "{product_info}". {get_style_prompt(style)}

Trả về theo định dạng:
🎯 [Tiêu đề sản phẩm ngắn gọn]

✨ [Slogan 1 câu]

📝 Mô tả: [100-150 từ miêu tả hấp dẫn]

💎 Điểm nổi bật:
• [Chất lượng]
• [Nguồn gốc]
• [Hương vị]
• [Dinh dưỡng]
• [Độ tươi]

🌟 Lợi ích: [3-4 lợi ích]

🎁 Cam kết: [Chất lượng, đổi trả, giao hàng]

🍽️ Gợi ý: [2-3 cách dùng]

#️⃣ Từ khóa: [5-7 hashtag, cách nhau bằng dấu phẩy]

Viết TIẾNG VIỆT."""


def generate_from_image(api_key: str, image: Image.Image, style: str) -> str:
    """Generate a product description from an image."""
    model = get_model(api_key)
    response = model.generate_content([_image_prompt(style), image])
    return response.text if response else ""


def generate_from_text(api_key: str, product_info: str, style: str) -> str:
    """Generate a product description from product information text."""
    model = get_model(api_key)
    response = model.generate_content(_text_prompt(product_info, style))
    return response.text if response else ""
