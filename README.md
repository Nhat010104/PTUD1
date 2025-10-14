# 🍎 AI Mô Tả Sản Phẩm Trái Cây Tự Động

Ứng dụng AI thông minh giúp tạo mô tả sản phẩm trái cây chuyên nghiệp cho sàn thương mại điện tử, sử dụng Google Gemini AI.

## ✨ Tính năng

- **Phân tích từ hình ảnh**: Upload hình ảnh trái cây và AI tự động tạo mô tả chi tiết
- **Tạo từ text**: Nhập mô tả ngắn gọn, AI mở rộng thành mô tả chuyên nghiệp
- **Mô tả đầy đủ**: Bao gồm tên, đặc điểm, lợi ích sức khỏe, hướng dẫn bảo quản
- **Giao diện thân thiện**: Dễ sử dụng với Streamlit
- **Tải xuống**: Xuất mô tả dạng file text

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8 trở lên
- Kết nối internet

### Các bước cài đặt

1. **Clone hoặc tải project**

2. **Cài đặt thư viện**
```bash
pip install -r requirements.txt
```

3. **Cấu hình API Key**

   a. Lấy Gemini API key miễn phí:
   - Truy cập: https://makersuite.google.com/app/apikey
   - Đăng nhập với tài khoản Google
   - Nhấn "Create API Key" để tạo key mới

   b. Tạo file `.env` từ template:
   ```bash
   copy .env.example .env
   ```
   
   c. Mở file `.env` và thêm API key của bạn:
   ```
   GEMINI_API_KEY=AIzaSy...your_api_key_here
   ```

## 📖 Hướng dẫn sử dụng

### Khởi động ứng dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ mở tự động trên trình duyệt tại: http://localhost:8501

### Chế độ 1: Phân tích từ hình ảnh

1. Chọn tab "📸 Phân Tích Từ Hình Ảnh"
2. Click "Browse files" để upload hình ảnh trái cây (JPG, JPEG, PNG)
3. Nhấn nút "🚀 Phân Tích & Tạo Mô Tả"
4. Đợi AI xử lý và xem kết quả
5. Nhấn "📥 Tải xuống mô tả" để lưu file

### Chế độ 2: Tạo từ text

1. Chọn tab "✍️ Tạo Từ Mô Tả Text"
2. Nhập thông tin cơ bản về sản phẩm, ví dụ:
   ```
   Táo Fuji nhập khẩu Nhật Bản, quả to, màu đỏ tươi, ngọt giòn
   ```
3. Nhấn nút "✨ Tạo Mô Tả Chi Tiết"
4. Xem và tải xuống mô tả đã tạo

## 📝 Cấu trúc mô tả được tạo

AI sẽ tạo mô tả theo cấu trúc chuẩn cho e-commerce:

- **Tên sản phẩm**: Hấp dẫn và tối ưu SEO
- **Mô tả ngắn gọn**: Câu giới thiệu thu hút
- **Đặc điểm nổi bật**: Màu sắc, kích thước, chất lượng, nguồn gốc
- **Lợi ích sức khỏe**: Giá trị dinh dưỡng
- **Hướng dẫn bảo quản**: Cách bảo quản tốt nhất
- **Gợi ý sử dụng**: Cách chế biến và sử dụng
- **Cam kết chất lượng**: (chỉ ở chế độ text)

## 💡 Mẹo sử dụng

- Sử dụng hình ảnh **rõ nét**, **đủ ánh sáng** để có kết quả tốt nhất
- Chụp ảnh trái cây từ nhiều góc độ khác nhau
- Cung cấp thông tin chi tiết khi dùng chế độ text
- Có thể **chỉnh sửa** mô tả sau khi AI tạo để phù hợp hơn với sản phẩm

## 🛠️ Công nghệ sử dụng

- **Streamlit**: Framework tạo web app Python
- **Google Gemini AI**: Model AI phân tích hình ảnh và tạo text
- **Pillow**: Xử lý hình ảnh
- **python-dotenv**: Quản lý biến môi trường

## ⚠️ Lưu ý

- API key Gemini có giới hạn requests miễn phí (60 requests/phút)
- Không chia sẻ API key của bạn với người khác
- File `.env` đã được thêm vào `.gitignore` để bảo mật

## 📞 Hỗ trợ

Nếu gặp lỗi:
1. Kiểm tra API key đã được cấu hình đúng chưa
2. Đảm bảo đã cài đặt đầy đủ thư viện từ `requirements.txt`
3. Kiểm tra kết nối internet

## 📄 License

MIT License - Tự do sử dụng cho mục đích cá nhân và thương mại.
