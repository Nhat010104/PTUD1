import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Mô Tả Sản Phẩm Trái Cây",
    page_icon="🍎",
    layout="wide"
)

def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Vui lòng cấu hình GEMINI_API_KEY trong file .env")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def analyze_image(model, image):
    prompt = """
    Bạn là chuyên gia Content Marketing và Copywriter hàng đầu cho sàn thương mại điện tử.
    Nhiệm vụ: Phân tích hình ảnh trái cây và viết mô tả BÁN HÀNG CỰC KỲ HẤP DẪN, tối ưu SEO.
    
    YÊU CẦU QUAN TRỌNG:
    ✅ Viết theo phong cách MARKETING, không khô khan
    ✅ Sử dụng từ ngữ GỢI CẢM XÚC, kích thích mua hàng
    ✅ Tích hợp từ khóa SEO tự nhiên
    ✅ Tạo cảm giác KHAN HIẾM, GIÁ TRỊ CAO
    ✅ Storytelling (kể chuyện về sản phẩm)
    
    **🎯 TIÊU ĐỀ SẢN PHẨM (Tối ưu SEO):**
    [Viết tiêu đề BẮT MẮT 60-80 ký tự, có từ khóa chính + từ khóa phụ]
    VD: "🍎 Táo Fuji Nhật Bản Cao Cấp - Ngọt Giòn, Thơm Ngon - Hộp 2kg Tươi Ngon 100%"
    
    **✨ SLOGAN HẤP DẪN:**
    [1 câu slogan ngắn gọn, ấn tượng, dễ nhớ]
    
    **📝 MÔ TẢ CHI TIẾT (100-150 từ):**
    Viết đoạn văn sinh động, hấp dẫn:
    - Mở đầu bằng câu hook thu hút (đặt câu hỏi hoặc câu chuyện ngắn)
    - Miêu tả cảm giác khi thưởng thức (vị ngọt tan trong miệng, hương thơm...)
    - Nguồn gốc xuất xứ rõ ràng (tạo niềm tin)
    - Lợi ích CỤ THỂ cho khách hàng
    - Kết thúc bằng call-to-action mềm mại
    
    **💎 5 ĐIỂM NỔI BẬT (Viết dạng bullet point hấp dẫn):**
    - ✅ [Điểm 1: Chất lượng cao cấp + con số cụ thể nếu có]
    - ✅ [Điểm 2: Nguồn gốc/xuất xứ uy tín + chi tiết]
    - ✅ [Điểm 3: Hương vị đặc biệt + cảm giác khi ăn]
    - ✅ [Điểm 4: Giá trị dinh dưỡng + lợi ích sức khỏe]
    - ✅ [Điểm 5: Độ tươi/cam kết chất lượng]
    
    **🌟 LỢI ÍCH VƯỢT TRỘI:**
    [3-4 lợi ích CỤ THỂ, dùng số liệu nếu có]
    VD: "Giàu Vitamin C (gấp 3 lần cam), tăng cường miễn dịch tức thì"
    
    **🎁 CAM KẾT & ƯU ĐÃI:**
    [Các cam kết về chất lượng, đổi trả, giao hàng nhanh...]
    
    **🍽️ GỢI Ý THƯỞNG THỨC:**
    [2-3 cách sử dụng sáng tạo, hấp dẫn]
    
    **#️⃣ TỪ KHÓA SEO:**
    [5-7 hashtag và từ khóa liên quan]
    
    LƯU Ý: Viết bằng TIẾNG VIỆT tự nhiên, thân thiện, không dùng ngôn ngữ quá hoa mỹ giả tạo.
    """
    
    try:
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi phân tích hình ảnh: {str(e)}"

def generate_from_text(model, product_info):
    prompt = f"""
    Bạn là chuyên gia Content Marketing và Copywriter hàng đầu cho sàn thương mại điện tử.
    Nhiệm vụ: Dựa vào thông tin "{product_info}" - viết mô tả BÁN HÀNG CỰC KỲ HẤP DẪN, tối ưu SEO.
    
    YÊU CẦU QUAN TRỌNG:
    ✅ Viết theo phong cách MARKETING, không khô khan
    ✅ Sử dụng từ ngữ GỢI CẢM XÚC, kích thích mua hàng
    ✅ Tích hợp từ khóa SEO tự nhiên
    ✅ Tạo cảm giác KHAN HIẾM, GIÁ TRỊ CAO
    ✅ Storytelling (kể chuyện về sản phẩm)
    
    **🎯 TIÊU ĐỀ SẢN PHẨM (Tối ưu SEO):**
    [Viết tiêu đề BẮT MẮT 60-80 ký tự, có từ khóa chính + từ khóa phụ]
    VD: "🍎 Táo Fuji Nhật Bản Cao Cấp - Ngọt Giòn, Thơm Ngon - Hộp 2kg Tươi Ngon 100%"
    
    **✨ SLOGAN HẤP DẪN:**
    [1 câu slogan ngắn gọn, ấn tượng, dễ nhớ]
    
    **📝 MÔ TẢ CHI TIẾT (100-150 từ):**
    Viết đoạn văn sinh động, hấp dẫn:
    - Mở đầu bằng câu hook thu hút (đặt câu hỏi hoặc câu chuyện ngắn)
    - Miêu tả cảm giác khi thưởng thức (vị ngọt tan trong miệng, hương thơm...)
    - Nguồn gốc xuất xứ rõ ràng (tạo niềm tin)
    - Lợi ích CỤ THỂ cho khách hàng
    - Kết thúc bằng call-to-action mềm mại
    
    **💎 5 ĐIỂM NỔI BẬT (Viết dạng bullet point hấp dẫn):**
    - ✅ [Điểm 1: Chất lượng cao cấp + con số cụ thể nếu có]
    - ✅ [Điểm 2: Nguồn gốc/xuất xứ uy tín + chi tiết]
    - ✅ [Điểm 3: Hương vị đặc biệt + cảm giác khi ăn]
    - ✅ [Điểm 4: Giá trị dinh dưỡng + lợi ích sức khỏe]
    - ✅ [Điểm 5: Độ tươi/cam kết chất lượng]
    
    **🌟 LỢI ÍCH VƯỢT TRỘI:**
    [3-4 lợi ích CỤ THỂ, dùng số liệu nếu có]
    VD: "Giàu Vitamin C (gấp 3 lần cam), tăng cường miễn dịch tức thì"
    
    **🎁 CAM KẾT & ƯU ĐÃI:**
    [Các cam kết về chất lượng, đổi trả, giao hàng nhanh...]
    
    **🍽️ GỢI Ý THƯỞNG THỨC:**
    [2-3 cách sử dụng sáng tạo, hấp dẫn]
    
    **#️⃣ TỪ KHÓA SEO:**
    [5-7 hashtag và từ khóa liên quan]
    
    LƯU Ý: Viết bằng TIẾNG VIỆT tự nhiên, thân thiện, không dùng ngôn ngữ quá hoa mỹ giả tạo.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi tạo mô tả: {str(e)}"

def main():
    st.title("🍎 AI Mô Tả Sản Phẩm Trái Cây Tự Động")
    st.markdown("### Hệ thống AI thông minh giúp tạo mô tả sản phẩm chuyên nghiệp cho sàn TMĐT")
    
    model = configure_gemini()
    
    tab1, tab2 = st.tabs(["📸 Phân Tích Từ Hình Ảnh", "✍️ Tạo Từ Mô Tả Text"])
    
    with tab1:
        st.header("Upload Hình Ảnh Trái Cây")
        st.markdown("*Tải lên hình ảnh sản phẩm và AI sẽ tự động tạo mô tả chi tiết*")
        
        uploaded_file = st.file_uploader(
            "Chọn hình ảnh trái cây",
            type=["jpg", "jpeg", "png"],
            help="Hỗ trợ định dạng: JPG, JPEG, PNG"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                image = Image.open(uploaded_file)
                st.image(image, caption="Hình ảnh đã tải lên", use_column_width=True)
            
            with col2:
                if st.button("🚀 Phân Tích & Tạo Mô Tả", type="primary"):
                    with st.spinner("🤖 AI đang phân tích hình ảnh..."):
                        description = analyze_image(model, image)
                        st.success("✅ Hoàn thành!")
                        st.markdown("---")
                        st.markdown(description)
                        
                        st.download_button(
                            label="📥 Tải xuống mô tả",
                            data=description,
                            file_name="mo_ta_san_pham.txt",
                            mime="text/plain"
                        )
    
    with tab2:
        st.header("Tạo Mô Tả Từ Thông Tin Text")
        st.markdown("*Nhập thông tin cơ bản về sản phẩm và AI sẽ mở rộng thành mô tả chi tiết*")
        
        product_info = st.text_area(
            "Nhập thông tin sản phẩm",
            placeholder="Ví dụ: Táo Fuji nhập khẩu Nhật Bản, quả to, màu đỏ tươi, ngọt giòn",
            height=150,
            help="Nhập mô tả ngắn gọn về trái cây: tên, nguồn gốc, đặc điểm..."
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✨ Tạo Mô Tả Chi Tiết", type="primary"):
                if product_info.strip():
                    with st.spinner("🤖 AI đang tạo mô tả chuyên nghiệp..."):
                        description = generate_from_text(model, product_info)
                        st.success("✅ Hoàn thành!")
                        st.markdown("---")
                        st.markdown(description)
                        
                        st.download_button(
                            label="📥 Tải xuống mô tả",
                            data=description,
                            file_name="mo_ta_san_pham.txt",
                            mime="text/plain"
                        )
                else:
                    st.warning("⚠️ Vui lòng nhập thông tin sản phẩm")
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>💡 <b>Mẹo sử dụng:</b></p>
        <p>• Sử dụng hình ảnh rõ nét, đủ ánh sáng để có kết quả tốt nhất</p>
        <p>• Cung cấp thông tin càng chi tiết càng tốt khi dùng chế độ Text</p>
        <p>• Bạn có thể chỉnh sửa mô tả sau khi AI tạo để phù hợp hơn</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
