"""Content generation helpers leveraging Gemini."""

from typing import Optional

from PIL import Image

from .gemini import get_model


STYLE_PROMPTS = {
    "Marketing": """
        Viết theo phong cách MARKETING mạnh mẽ, gợi cảm xúc, kích thích mua hàng.
        Sử dụng từ ngữ hấp dẫn, tạo cảm giác KHAN HIẾM và GIÁ TRỊ CAO.
    """,
    "Professional": """
        Viết theo phong cách CHUYÊN NGHIỆP, trang trọng, chính xác.
        Tập trung vào thông tin chi tiết, nguồn gốc, chất lượng sản phẩm.
    """,
    "Casual": """
        Viết theo phong cách THÂN THIỆN, gần gũi, dễ hiểu.
        Như đang tư vấn cho bạn bè, tự nhiên và chân thực.
    """,
    "Storytelling": """
        Viết theo phong cách KỂ CHUYỆN, tạo câu chuyện hấp dẫn về sản phẩm.
        Mở đầu bằng câu chuyện, lồng ghép thông tin sản phẩm vào câu chuyện.
    """,
}


def get_style_prompt(style: str) -> str:
    """Return the Gemini writing style prompt."""
    return STYLE_PROMPTS.get(style, STYLE_PROMPTS["Marketing"])


def _image_prompt(style: str) -> str:
    return f"""
    Bạn là chuyên gia Content Marketing và Copywriter hàng đầu cho sàn thương mại điện tử.
    Nhiệm vụ: Phân tích hình ảnh trái cây và viết mô tả BÁN HÀNG CỰC KỲ HẤP DẪN, tối ưu SEO.

    {get_style_prompt(style)}

    YÊU CẦU QUAN TRỌNG:
    ✅ Tích hợp từ khóa SEO tự nhiên
    ✅ Storytelling (kể chuyện về sản phẩm)

    **🎯 TIÊU ĐỀ SẢN PHẨM (Tối ưu SEO):**
    [Viết tiêu đề BẮT MẮT 60-80 ký tự, có từ khóa chính + từ khóa phụ]

    **✨ SLOGAN HẤP DẪN:**
    [1 câu slogan ngắn gọn, ấn tượng, dễ nhớ]

    **📝 MÔ TẢ CHI TIẾT (100-150 từ):**
    Viết đoạn văn sinh động, hấp dẫn với:
    - Mở đầu bằng câu hook thu hút
    - Miêu tả cảm giác khi thưởng thức
    - Nguồn gốc xuất xứ rõ ràng
    - Lợi ích CỤ THỂ cho khách hàng
    - Kết thúc bằng call-to-action

    **💎 5 ĐIỂM NỔI BẬT:**
    - ✅ [Điểm 1: Chất lượng cao cấp]
    - ✅ [Điểm 2: Nguồn gốc/xuất xứ]
    - ✅ [Điểm 3: Hương vị đặc biệt]
    - ✅ [Điểm 4: Giá trị dinh dưỡng]
    - ✅ [Điểm 5: Độ tươi/cam kết]

    **🌟 LỢI ÍCH VƯỢT TRỘI:**
    [3-4 lợi ích CỤ THỂ, dùng số liệu nếu có]

    **🎁 CAM KẾT & ƯU ĐÃI:**
    [Các cam kết về chất lượng, đổi trả, giao hàng]

    **🍽️ GỢI Ý THƯỞNG THỨC:**
    [2-3 cách sử dụng sáng tạo]

    **#️⃣ TỪ KHÓA SEO:**
    [5-7 hashtag và từ khóa liên quan]

    Viết bằng TIẾNG VIỆT tự nhiên, thân thiện.
    """


def _text_prompt(product_info: str, style: str) -> str:
    return f"""
    Bạn là chuyên gia Content Marketing và Copywriter hàng đầu cho sàn thương mại điện tử.
    Nhiệm vụ: Dựa vào thông tin "{product_info}" - viết mô tả BÁN HÀNG CỰC KỲ HẤP DẪN, tối ưu SEO.

    {get_style_prompt(style)}

    [Cấu trúc giống như trong yêu cầu phân tích hình ảnh]
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
