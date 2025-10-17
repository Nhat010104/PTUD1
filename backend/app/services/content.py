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

    HÃY TRẢ KẾT QUẢ THEO ĐỊNH DẠNG SAU (KHÔNG DÙNG KÝ TỰ * HOẶC -):
    Tiêu đề sản phẩm: [viết tiêu đề bắt mắt 60-80 ký tự, có từ khóa chính và phụ]
    Slogan: [1 câu slogan ngắn gọn, ấn tượng, dễ nhớ]
    Mô tả chi tiết: [đoạn văn 100-150 từ, mở đầu bằng câu hook, miêu tả cảm giác khi thưởng thức, nêu nguồn gốc, lợi ích cụ thể và call-to-action]
    Điểm nổi bật 1: [chất lượng cao cấp]
    Điểm nổi bật 2: [nguồn gốc/xuất xứ]
    Điểm nổi bật 3: [hương vị đặc biệt]
    Điểm nổi bật 4: [giá trị dinh dưỡng]
    Điểm nổi bật 5: [độ tươi hoặc cam kết]
    Lợi ích vượt trội: [3 đến 4 lợi ích cụ thể, dùng số liệu nếu có]
    Cam kết và ưu đãi: [các cam kết về chất lượng, đổi trả, giao hàng]
    Gợi ý thưởng thức: [2 đến 3 cách sử dụng sáng tạo]
    Từ khóa SEO: [5 đến 7 hashtag hoặc từ khóa liên quan, viết cách nhau bằng dấu phẩy]

    Viết bằng TIẾNG VIỆT tự nhiên, thân thiện.
    """


def _text_prompt(product_info: str, style: str) -> str:
    return f"""
    Bạn là chuyên gia Content Marketing và Copywriter hàng đầu cho sàn thương mại điện tử.
    Nhiệm vụ: Dựa vào thông tin "{product_info}" - viết mô tả BÁN HÀNG CỰC KỲ HẤP DẪN, tối ưu SEO.

    {get_style_prompt(style)}

    HÃY TRẢ KẾT QUẢ THEO ĐỊNH DẠNG SAU (KHÔNG DÙNG KÝ TỰ * HOẶC -):
    Tiêu đề sản phẩm: ...
    Slogan: ...
    Mô tả chi tiết: ...
    Điểm nổi bật 1: ...
    Điểm nổi bật 2: ...
    Điểm nổi bật 3: ...
    Điểm nổi bật 4: ...
    Điểm nổi bật 5: ...
    Lợi ích vượt trội: ...
    Cam kết và ưu đãi: ...
    Gợi ý thưởng thức: ...
    Từ khóa SEO: ...

    Viết bằng TIẾNG VIỆT tự nhiên, thân thiện.
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
