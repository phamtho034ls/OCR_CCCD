# Local OCR API - Frontend

Giao diện người dùng (React, TypeScript, Vite) để tải ảnh tài liệu lên, chạy OCR PP-OCRv6, hiển thị, chỉnh sửa và tải về kết quả văn bản.

## 1. Yêu cầu hệ thống

- Node.js (phiên bản v18 trở lên được khuyến nghị).
- npm (đi kèm khi cài đặt Node.js).

## 2. Cài đặt các gói phụ thuộc

Chuyển vào thư mục frontend:

```bash
cd frontend
```

Cài đặt các thư viện liên quan:

```bash
npm install
```

## 3. Cấu hình biến môi trường

Sao chép `.env.example` thành `.env` (Nếu chưa có):

- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux/macOS:**
  ```bash
  cp .env.example .env
  ```

Biến môi trường cần chú ý:
- `VITE_API_BASE_URL`: Địa chỉ API Backend (mặc định là `http://localhost:8000/api`).

## 4. Chạy ứng dụng chế độ Phát triển (Development Mode)

Chạy lệnh:

```bash
npm run dev
```

Sau khi khởi chạy thành công, mở trình duyệt truy cập:
[http://localhost:5173](http://localhost:5173)

## 5. Xây dựng phiên bản Production

Để tối ưu hóa hiệu năng và đóng gói dự án:

```bash
npm run build
```
Dự án được biên dịch sẽ nằm trong thư mục `dist`.
