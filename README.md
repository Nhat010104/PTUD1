# 🍎 AI Mô Tả Sản Phẩm Trái Cây Tự Động

Ứng dụng web AI thông minh giúp tạo mô tả sản phẩm trái cây chuyên nghiệp cho sàn thương mại điện tử, sử dụng Google Gemini AI với kiến trúc FastAPI + Next.js.

## ✨ Tính năng

### 🎨 Tạo Mô Tả AI
- **Phân tích từ hình ảnh**: Upload hoặc chụp ảnh trái cây, AI tự động tạo mô tả chi tiết
- **Tạo từ text**: Nhập mô tả ngắn gọn, AI mở rộng thành mô tả chuyên nghiệp
- **Đa phong cách viết**: Tiếp thị, Chuyên nghiệp, Thân thiện, Kể chuyện
- **Đánh giá SEO tự động**: Tính điểm SEO và đưa ra gợi ý tối ưu

### 👤 Quản Lý Tài Khoản
- **Đăng ký/Đăng nhập**: Hỗ trợ cả **Email** và **Số điện thoại**
- **Xác thực JWT**: Bảo mật với JSON Web Token
- **Quên mật khẩu**: Khôi phục mật khẩu với mã đặt lại
- **Lịch sử cá nhân**: Lưu trữ và xem lại các mô tả đã tạo

## 🔄 Workflow tổng quan

```mermaid
flowchart TD
    subgraph UI[Frontend Next.js]
        A1[1. Người dùng truy cập web/app]
        A2[2. Đăng nhập/đăng ký]
        A3[3. Chọn chế độ: Hình ảnh / Text / Agent]
        A4[4. Nhập dữ liệu hoặc gửi yêu cầu]
        A5[5. Xem kết quả, tải xuống, xem lịch sử]
    end

    subgraph BE[Backend FastAPI]
        B1[6. /auth/login - xác thực JWT]
        B2[7. /api/descriptions/image]
        B3[8. /api/descriptions/text]
        B4[9. /api/agent/chat]
        B5[10. Lưu lịch sử mô tả]
        B6[11. Lưu phiên agent & hội thoại]
        B7[12. /api/history & /api/agent/sessions]
        B8[13. /api/export/docx|pdf]
    end

    subgraph External[External Services]
        C1[Google Gemini API]
        C2[SQLite data.db]
    end

    A1 --> A2
    A2 -->|Gửi email/mật khẩu| B1
    B1 -->|JWT token| A2
    A2 --> A3
    A3 --> A4

    A4 -->|POST /api/descriptions/image| B2
    A4 -->|POST /api/descriptions/text| B3
    A4 -->|POST /api/agent/chat| B4

    B2 -->|Gọi Gemini phân tích hình| C1
    B3 -->|Gọi Gemini sinh text| C1
    B4 -->|Agent quyết định & gọi Gemini| C1

    B2 -->|Lưu mô tả| B5
    B3 -->|Lưu mô tả| B5
    B4 -->|Lưu mô tả (nếu hoàn thành)| B5
    B4 -->|Lưu hội thoại| B6

    B5 -->|Ghi dữ liệu| C2
    B6 -->|Ghi dữ liệu| C2

    A5 -->|GET /api/history| B7
    A5 -->|GET /api/agent/sessions| B7
    B7 -->|Trả dữ liệu lịch sử & phiên| A5

    A5 -->|POST /api/export/docx| B8
    A5 -->|POST /api/export/pdf| B8
    B8 -->|Trả file DOCX/PDF| A5
```

## 🚀 Cài đặt

### Yêu cầu hệ thống
- **Python 3.8+** (Backend)
- **Node.js 18+** và **npm** (Frontend)
- Kết nối internet

### Cấu trúc dự án
```
PTUD1/
├── backend/          # FastAPI Backend
│   ├── app/
│   │   ├── db/      # Database models & session
│   │   ├── services/ # Business logic
│   │   └── main.py  # API endpoints
│   └── requirements.txt
├── frontend/         # Next.js Frontend
│   ├── app/
│   └── package.json
├── .env             # Environment variables
└── data.db          # SQLite database
```

### Các bước cài đặt

1. **Clone hoặc tải project**

2. **Cấu hình API Key**

   a. Lấy Gemini API key miễn phí:
   - Truy cập: https://makersuite.google.com/app/apikey
   - Đăng nhập với tài khoản Google
   - Nhấn "Create API Key" để tạo key mới

   b. File `.env` đã có sẵn, cập nhật API key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_api_key_here
   JWT_SECRET=your_secret_key_here
   ```

3. **Cài đặt Backend**
```bash
# Cài đặt dependencies Python
pip install -r backend/requirements.txt
```

4. **Cài đặt Frontend**
```bash
cd frontend
npm install
cd ..
```

## 📖 Hướng dẫn chạy ứng dụng

### 🔴 Backend (FastAPI)

**Terminal 1:**
```bash
# Windows PowerShell
cd C:\path\to\PTUD1
python -m uvicorn backend.app.main:app --reload --port 8000

# Linux/Mac
python -m uvicorn backend.app.main:app --reload --port 8000
```

✅ Backend chạy tại: **http://localhost:8000**  
📄 API Documentation: **http://localhost:8000/docs**

### 🟢 Frontend (Next.js)

**Terminal 2:**
```bash
cd frontend
npm run dev
```

✅ Frontend chạy tại: **http://localhost:3000**

---

## 🎯 Hướng dẫn sử dụng

### 1. Đăng ký/Đăng nhập

**Đăng ký mới:**
- Nhấn "Đăng nhập / Đăng ký"
- Chọn "Đăng ký tài khoản"
- Nhập **Email** hoặc **Số điện thoại** (10-11 số)
- Nhập mật khẩu (tối thiểu 6 ký tự)

**Đăng nhập:**
- Nhập email/số điện thoại đã đăng ký
- Nhập mật khẩu

### 2. Tạo mô tả từ hình ảnh

1. Chọn tab "📸 Phân tích hình ảnh"
2. Chọn phong cách viết (Tiếp thị, Chuyên nghiệp, Thân thiện...)
3. Upload hình hoặc dùng camera chụp ảnh
4. Nhấn "🚀 AI tạo mô tả ngay"
5. Xem kết quả với điểm SEO và các gợi ý

### 3. Tạo mô tả từ text

1. Chọn tab "✍️ Tạo từ mô tả text"
2. Chọn phong cách viết
3. Nhập thông tin sản phẩm:
   ```
   Táo Fuji nhập khẩu Nhật Bản, quả to, màu đỏ tươi, ngọt giòn
   ```
4. Nhấn "✨ Tạo mô tả chi tiết"

### 4. Xem lịch sử

- Sau khi đăng nhập, tất cả mô tả được lưu tự động
- Cuộn xuống phần "Lịch sử mô tả"
- Click "Xem chi tiết" để xem lại
- Sao chép hoặc tải xuống mô tả

## 📝 Cấu trúc mô tả được tạo

AI sẽ tạo mô tả theo cấu trúc chuẩn cho e-commerce:

- **Tên sản phẩm**: Hấp dẫn và tối ưu SEO
- **Mô tả ngắn gọn**: Câu giới thiệu thu hút
- **Đặc điểm nổi bật**: Màu sắc, kích thước, chất lượng, nguồn gốc
- **Lợi ích sức khỏe**: Giá trị dinh dưỡng
- **Hướng dẫn bảo quản**: Cách bảo quản tốt nhất
- **Gợi ý sử dụng**: Cách chế biến và sử dụng
- **Điểm SEO**: Tự động tính toán và đánh giá từ khóa, hashtag, CTA

## 💡 Mẹo sử dụng

- **Đăng nhập** để lưu lịch sử và quản lý mô tả
- Sử dụng hình ảnh **rõ nét**, **đủ ánh sáng** để có kết quả tốt nhất
- Thử nhiều **phong cách viết** khác nhau để chọn phù hợp
- Kiểm tra **điểm SEO** và áp dụng gợi ý để tối ưu
- Có thể **sao chép** mô tả để chỉnh sửa theo ý muốn

## 🛠️ Công nghệ sử dụng

### Backend
- **FastAPI**: Modern Python web framework
- **SQLModel**: ORM dựa trên SQLAlchemy & Pydantic
- **Google Gemini AI**: Model AI phân tích hình ảnh và tạo text
- **JWT Authentication**: Xác thực người dùng an toàn
- **SQLite**: Database nhẹ, dễ deploy

### Frontend
- **Next.js 15**: React framework với App Router
- **TypeScript**: Type-safe JavaScript
- **Axios**: HTTP client
- **CSS-in-JS**: Inline styling

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - Đăng ký (email hoặc số điện thoại)
- `POST /auth/login` - Đăng nhập
- `GET /auth/me` - Thông tin user hiện tại
- `POST /auth/forgot-password` - Quên mật khẩu
- `POST /auth/reset-password` - Đặt lại mật khẩu

### Descriptions
- `POST /api/descriptions/image` - Tạo mô tả từ hình ảnh
- `POST /api/descriptions/text` - Tạo mô tả từ text
- `GET /api/history` - Lịch sử mô tả (yêu cầu đăng nhập)
- `GET /api/styles` - Danh sách phong cách viết

### Utilities
- `GET /health` - Health check

**Swagger UI**: http://localhost:8000/docs

## ⚠️ Lưu ý

- API key Gemini có giới hạn requests miễn phí (60 requests/phút)
- Không chia sẻ API key và JWT secret
- File `.env` đã được thêm vào `.gitignore` để bảo mật
- Database SQLite phù hợp cho development và ứng dụng nhỏ
- Đăng ký bằng số điện thoại: chỉ chấp nhận 10-11 chữ số

## 🔧 Troubleshooting

**Backend không chạy:**
```bash
# Xóa cache Python
Remove-Item -Recurse backend/__pycache__, backend/app/__pycache__

# Cài lại dependencies
pip install -r backend/requirements.txt
```

**Frontend không chạy:**
```bash
cd frontend
# Xóa node_modules và cài lại
Remove-Item -Recurse node_modules
npm install
```

**Database bị lỗi:**
```bash
# Xóa và tạo lại database
del data.db
# Restart backend để tự động tạo lại
```

## 📞 Hỗ trợ

Nếu gặp lỗi:
1. Kiểm tra backend và frontend đều đang chạy
2. Kiểm tra API key Gemini đã cấu hình đúng
3. Đảm bảo port 8000 và 3000 không bị chiếm
4. Xem logs trong terminal để biết lỗi cụ thể
5. Check Developer Tools (F12) trong browser

## 📄 License

MIT License - Tự do sử dụng cho mục đích cá nhân và thương mại.
