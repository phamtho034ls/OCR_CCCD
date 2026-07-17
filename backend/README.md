# Local OCR API - Backend

Backend dịch vụ nhận dạng chữ viết cục bộ chạy **DeepSeek-OCR** sử dụng FastAPI, Uvicorn và Hugging Face Transformers.

## 1. Yêu cầu hệ thống

- Python 3.10, 3.11 hoặc 3.12.
- Môi trường chạy Windows, Linux hoặc macOS.
- **Khuyến nghị**: Máy tính có card đồ họa NVIDIA GPU hỗ trợ CUDA (với VRAM tối thiểu 6GB-8GB) để chạy mượt mà ở chế độ `bfloat16`/`float16`. (Nếu không có GPU, hệ thống tự động fallback về CPU nhưng sẽ chạy chậm hơn đáng kể).

## 2. Cài đặt môi trường

Chuyển vào thư mục backend:

```bash
cd backend
```

Tạo môi trường ảo (Virtual Environment):

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:

- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```

## 3. Cài đặt các gói phụ thuộc

Cài đặt tất cả gói phụ thuộc cần thiết (bao gồm PyTorch và Hugging Face Transformers) bằng cách chạy lệnh:

```bash
pip install -r requirements.txt
```

*Lưu ý: Nếu sử dụng GPU, bạn nên đảm bảo phiên bản `torch` tương thích với phiên bản CUDA hiện tại trên máy của bạn.*

## 4. Cấu hình biến môi trường

Sao chép file `.env.example` thành `.env`:

- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux/macOS:**
  ```bash
  cp .env.example .env
  ```

Các tham số chính trong `.env`:
- `OCR_DEVICE`: đặt thành `cuda` nếu máy của bạn hỗ trợ GPU NVIDIA (hoặc `cpu` để chạy chậm hơn trên CPU).
- `OCR_MODEL_ID`: định danh model Hugging Face, mặc định là `"deepseek-ai/DeepSeek-OCR"`.
- `MAX_FILE_SIZE_MB`: giới hạn dung lượng tải lên (mặc định là `15` MB).
- `CORS_ORIGINS`: nguồn CORS cho phép Frontend truy cập (mặc định là `http://localhost:5173`).

## 5. Chạy ứng dụng

Chạy backend API bằng lệnh sau:

```bash
python run.py
```

Hoặc sử dụng trực tiếp Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

*Lưu ý quan trọng: Trong lần chạy đầu tiên, hệ thống sẽ tự động tải các file trọng số mô hình (~3.1GB) từ Hugging Face về bộ đệm cục bộ của bạn. Quá trình này có thể mất từ vài phút đến hàng chục phút tùy thuộc vào đường truyền mạng.*

Giao diện tài liệu API tự động (Swagger UI) sẽ hoạt động tại:
[http://localhost:8000/docs](http://localhost:8000/docs)

## 6. Chạy kiểm thử (Unit Tests)

Kích hoạt môi trường ảo và chạy lệnh:

```bash
python -m pytest
```

