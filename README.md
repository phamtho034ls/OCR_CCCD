# Local DeepSeek-OCR Document Recognition System

Hệ thống OCR nhận dạng chữ viết tiếng Việt chạy hoàn toàn local (offline) trên máy tính, sử dụng mô hình học sâu **DeepSeek-OCR** kết hợp với giao diện React/Vite/TypeScript và backend FastAPI.

---

## 🛠️ Tính năng Mới đã Cập nhật

1. **Pipeline Xử lý Split-API Tuần tự (Cho cả Giấy A4 và CCCD)**:
   - **API 1 (`POST /api/ocr/upload`)**: Tiếp nhận tệp ảnh tải lên, chạy khâu tiền xử lý (cắt viền Warping phối cảnh, xoay thẳng, lọc ảnh) và trả về Base64 ảnh đã làm sạch cùng cờ hiệu năng. 
   - **Xem trước tức thì**: Giao diện hiển thị ngay ảnh đã cắt viền, phẳng phiu cho người dùng xem trước trong khi mô hình AI đang chạy ngầm, mang lại trải nghiệm UX vượt trội.
   - **API 2 (`POST /api/ocr/recognize`)**: Nhận token tệp tạm thời, chạy mô hình AI nhận dạng chữ viết và cấu trúc JSON trường dữ liệu, sau đó tự động xóa sạch tệp tạm để bảo vệ không gian đĩa.
2. **Kiến trúc Engine OCR Mô-đun (Dễ dàng thay thế mô hình)**:
   - Backend được tái cấu trúc theo mẫu thiết kế Factory và giao diện lớp cơ sở `BaseOCREngine` (trong `ocr_service.py`).
   - Hỗ trợ thay thế/cắm thêm các mô hình OCR khác (như EasyOCR, PaddleOCR, Tesseract) chỉ bằng cách viết lớp kế thừa giao diện và thay đổi cấu hình `OCR_ENGINE` trong tệp `.env`.
3. **Hiệu ứng Quét Chữ và Vẽ Bounding Box Động**:
   - Vẽ khung bao (polygon) phát sáng màu vàng hổ phách nổi bật trên vùng ảnh của trường thông tin đang được hover/focus bên bảng kết quả.
   - Hiệu ứng quét từng dòng chữ xuất hiện động sau khi mô hình AI nhận dạng xong.

---

## 📂 Cấu trúc thư mục

```text
local-ocr-system/
├── backend/          # FastAPI Backend (DeepSeek-OCR, PyTorch, Transformers, OpenCV)
│   ├── app/
│   │   ├── api/            # API Endpoints (ocr_routes.py)
│   │   ├── core/           # Cấu hình cài đặt & Xử lý ngoại lệ
│   │   ├── schemas/        # Định nghĩa Pydantic schemas (ocr_schema.py)
│   │   └── services/       # OCR Service orchestrator & Image preprocessing logic
│   └── tests/              # Bộ unit tests tích hợp (pytest)
└── frontend/         # React, Vite, TS, Axios Frontend
```

---

## 🚀 Hướng dẫn khởi chạy hệ thống

### Bước 1: Khởi chạy Backend

1. Di chuyển vào thư mục backend:
   ```bash
   cd backend
   ```
2. Tạo môi trường ảo và kích hoạt:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux/macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
3. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
   *Lưu ý: Nếu máy có GPU NVIDIA CUDA, hãy cài đặt phiên bản PyTorch CUDA tương ứng để chạy OCR với hiệu năng tăng tốc vượt trội.*

4. Cấu hình biến môi trường:
   Sao chép file `.env.example` thành `.env`:
   - **Windows:** `copy .env.example .env`
   - **Linux/macOS:** `cp .env.example .env`

   Mở tệp `.env` vừa tạo và chỉnh sửa:
   - `OCR_DEVICE`: đặt thành `cuda` nếu chạy bằng GPU NVIDIA, hoặc `cpu` nếu chạy bằng CPU.
   - `OCR_ENGINE`: `deepseek` để chạy mô hình AI DeepSeek-OCR thật, hoặc `mock` để kiểm thử cục bộ siêu nhanh không cần GPU.
   - `OCR_MODEL_ID`: mặc định là `"deepseek-ai/DeepSeek-OCR"`.

5. Chạy Backend API:
   ```bash
   python run.py
   ```
   *Backend sẽ chạy tại: http://localhost:8000*
   *Tài liệu Swagger API: http://localhost:8000/docs*

---

### Bước 2: Khởi chạy Frontend

1. Di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```
2. Cài đặt thư viện Node.js:
   ```bash
   npm install
   ```
3. Chạy Frontend phát triển:
   ```bash
   npm run dev
   ```
   *Frontend hoạt động tại: http://localhost:5173*
