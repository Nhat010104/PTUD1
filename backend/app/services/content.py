"""Content generation helpers leveraging Gemini."""

from typing import Optional

from PIL import Image

from .gemini import get_model


STYLE_PROMPTS = {
    "Tiếp thị": """
Viết theo phong cách MARKETING mạnh mẽ và truyền cảm hứng.
- Mở đầu gây chú ý bằng lợi ích nổi bật hoặc cảm xúc (ví dụ: “Chỉ còn hôm nay...”, “Sẵn sàng bứt phá cùng...”).
- Thân bài nhấn mạnh giá trị, tính năng, sự khác biệt, thể hiện cảm giác KHAN HIẾM và GIÁ TRỊ CAO.
- Dùng ngôn từ gợi cảm xúc và hành động (mua ngay, trải nghiệm, tận hưởng, đừng bỏ lỡ).
- Kết bài có lời kêu gọi hành động rõ ràng (CTA) như “Đặt hàng ngay hôm nay để nhận ưu đãi đặc biệt!”.
""",

"Chuyên nghiệp": """
Viết theo phong cách CHUYÊN NGHIỆP, chuẩn mực và thuyết phục.
- Trình bày mạch lạc, thông tin rõ ràng về nguồn gốc, tiêu chuẩn chất lượng, quy trình sản xuất.
- Dùng ngôn ngữ trang trọng, có căn cứ, tạo niềm tin và uy tín.
- Nhấn mạnh các chứng nhận, thông số kỹ thuật, cam kết chất lượng.
- Kết bài khẳng định uy tín thương hiệu và lời mời trải nghiệm.
""",

"Thân thiện": """
Viết theo phong cách THÂN THIỆN và gần gũi.
- Dùng giọng văn tự nhiên, như đang trò chuyện hoặc tư vấn cho bạn bè.
- Mở đầu nhẹ nhàng, khơi gợi cảm xúc tích cực (“Nếu bạn đang tìm...”, “Bạn sẽ yêu ngay hương vị này!”).
- Giải thích lợi ích theo cách dễ hiểu, giúp người đọc cảm thấy an tâm và vui vẻ.
- Kết bài có thể kèm câu khích lệ thân thiện (“Hãy thử một lần và cảm nhận sự khác biệt nhé!”).
""",

"Kể chuyện": """
Viết theo phong cách KỂ CHUYỆN sinh động và cuốn hút.
- Mở đầu bằng một câu chuyện thực tế hoặc tưởng tượng liên quan đến sản phẩm (hành trình, kỷ niệm, nguồn gốc).
- Lồng ghép tự nhiên thông tin sản phẩm vào diễn biến câu chuyện.
- Tạo cảm xúc (ấm áp, tự hào, bất ngờ...) để người đọc đồng cảm và nhớ lâu.
- Kết bài nhẹ nhàng, khơi gợi hành động (“Hãy để câu chuyện này tiếp tục cùng bạn hôm nay!”).
""",

}


def get_style_prompt(style: str) -> str:
    """Return the Gemini writing style prompt."""
    return STYLE_PROMPTS.get(style, STYLE_PROMPTS["Tiếp thị"])


def _image_prompt(style: str) -> str:
    return f"""Viết mô tả bán hàng cho sản phẩm trái cây trong ảnh. {get_style_prompt(style)}

Thông tin sản phẩm: "{product_info}"

Hãy đảm bảo:
- Giọng văn tự nhiên, mạch lạc, đúng phong cách {style}.
- Tập trung vào giá trị sản phẩm (nguồn gốc, chất lượng, lợi ích thực tế).
- Gợi cảm xúc người đọc và thúc đẩy hành động mua hàng.
- Kết hợp khéo léo từ ngữ cảm xúc và từ khóa bán hàng.
- Dài khoảng 120–160 từ, tránh liệt kê khô khan.

Trả về **đúng định dạng sau**, không thêm lời dẫn hay chú thích khác:

🎯 [Tiêu đề sản phẩm ngắn gọn, chứa từ khóa SEO chính]

✨ [Slogan 1 câu thật ấn tượng, gợi cảm xúc hoặc giá trị sản phẩm]

📝 Mô tả: [Đoạn văn 100–150 từ miêu tả hấp dẫn, gồm: nguồn gốc, đặc điểm nổi bật, giá trị sản phẩm, lợi ích và lời kêu gọi hành động rõ ràng]

💎 Điểm nổi bật:
• [Chất lượng: mô tả ngắn]
• [Nguồn gốc: mô tả ngắn]
• [Hương vị: mô tả ngắn]
• [Dinh dưỡng: mô tả ngắn]
• [Độ tươi: mô tả ngắn]

🌟 Lợi ích:
1. [Lợi ích cụ thể 1]
2. [Lợi ích cụ thể 2]
3. [Lợi ích cụ thể 3]
4. [Lợi ích cụ thể 4]

🎁 Cam kết:
[1-2 câu ngắn khẳng định chất lượng, chính sách đổi trả và giao hàng]

🍽️ Gợi ý:
- [Cách dùng 1]
- [Cách dùng 2]
- [Cách dùng 3]

#️⃣ Từ khóa:
[5–7 hashtag, phân tách bằng dấu phẩy, có liên quan đến sản phẩm và cảm xúc]

Viết hoàn toàn bằng TIẾNG VIỆT, giọng văn mượt, tự nhiên, lôi cuốn.
Không thêm ghi chú, chỉ trả về nội dung đúng khung trên.
"""


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
