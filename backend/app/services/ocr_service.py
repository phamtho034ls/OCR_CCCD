import os
import sys
import threading
import unicodedata
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.exceptions import OCRInferenceError

class BaseOCREngine(ABC):
    """Lớp giao diện cơ sở (Interface) cho các OCR Model Engine khác nhau."""
    
    @abstractmethod
    def load(self) -> None:
        """Khởi tạo và nạp mô hình vào bộ nhớ."""
        pass

    @abstractmethod
    def recognize_image(self, file_path: Path) -> str:
        """Nhận dạng chữ viết từ file ảnh và trả về chuỗi văn bản thô."""
        pass


class DeepSeekOCREngine(BaseOCREngine):
    """Cấu hình tích hợp mô hình ngôn ngữ-hình ảnh DeepSeek-OCR."""
    
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None
        self._lock = threading.Lock()

    def load(self) -> None:
        if self._model is not None:
            return
            
        with self._lock:
            if self._model is not None:
                return
                
            import torch
            from transformers import AutoModel, AutoTokenizer

            # Xác định GPU/CPU tối ưu
            if "cuda" in settings.OCR_DEVICE.lower() and torch.cuda.is_available():
                device = "cuda"
                dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            else:
                device = "cpu"
                dtype = torch.float32

            print(f"[DeepSeekOCREngine] Initializing DeepSeek-OCR '{settings.OCR_MODEL_ID}' on '{device}' with dtype '{dtype}'...")

            try:
                # Thử nạp offline cache trước
                try:
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        settings.OCR_MODEL_ID,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    self._model = AutoModel.from_pretrained(
                        settings.OCR_MODEL_ID,
                        trust_remote_code=True,
                        torch_dtype=dtype,
                        use_safetensors=True,
                        local_files_only=True
                    ).to(device=device).eval()
                except Exception as offline_err:
                    print(f"[DeepSeekOCREngine] Offline load failed ({offline_err}), falling back to online check...")
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        settings.OCR_MODEL_ID,
                        trust_remote_code=True
                    )
                    self._model = AutoModel.from_pretrained(
                        settings.OCR_MODEL_ID,
                        trust_remote_code=True,
                        torch_dtype=dtype,
                        use_safetensors=True
                    ).to(device=device).eval()
                    
                self._device = device
                print(f"[DeepSeekOCREngine] DeepSeek-OCR model loaded successfully!")
            except Exception as e:
                raise OCRInferenceError(
                    f"Không thể khởi tạo DeepSeek-OCR ({settings.OCR_MODEL_ID}). Lỗi: {str(e)}"
                )

    def recognize_image(self, file_path: Path) -> str:
        self.load()
        with self._lock:
            try:
                abs_file_path = file_path.resolve()
                full_text = self._model.infer(
                    self._tokenizer,
                    prompt=settings.OCR_PROMPT,
                    image_file=str(abs_file_path),
                    output_path=str(abs_file_path.parent),
                    base_size=settings.OCR_BASE_SIZE,
                    image_size=settings.OCR_IMAGE_SIZE,
                    crop_mode=settings.OCR_CROP_MODE,
                    eval_mode=True
                )
                return full_text or ""
            except Exception as e:
                raise OCRInferenceError(f"Lỗi trong quá trình chạy model DeepSeek-OCR: {str(e)}")


class MockOCREngine(BaseOCREngine):
    """Mô hình giả lập (Mock) phục vụ viết Unit Test nhanh chóng không cần GPU."""
    
    def load(self) -> None:
        pass

    def recognize_image(self, file_path: Path) -> str:
        # Trả về kết quả grounding mock tiêu chuẩn để khớp các bộ phân tích
        return (
            "<|ref|>CONG HOA XÃ HỘI CHỦ NGHĨA VIỆT NAM<|/ref|><|det|>[10, 10, 100, 20]\n"
            "<|ref|>Số / No.: 037083008319<|/ref|><|det|>[10, 30, 80, 40]\n"
            "<|ref|>TRẦN VĂN NGHỊ<|/ref|><|det|>[10, 50, 60, 60]"
        )


def get_ocr_engine() -> BaseOCREngine:
    """Factory function để sinh đối tượng OCR Engine dựa vào cấu hình."""
    engine_type = getattr(settings, "OCR_ENGINE", "deepseek").lower()
    if engine_type == "deepseek":
        return DeepSeekOCREngine()
    elif engine_type == "mock":
        return MockOCREngine()
    else:
        # Nếu muốn đổi sang Tesseract/EasyOCR/PaddleOCR chỉ cần tạo Class kế thừa và đăng ký tại đây
        raise ValueError(f"Không hỗ trợ OCR Engine: {engine_type}")


class OCRService:
    """Lớp điều phối dịch vụ OCR cấp cao (Xử lý ảnh đơn lẻ, phân trang PDF, tính toán khung tọa độ)."""
    
    def __init__(self):
        self.engine = get_ocr_engine()

    def recognize(self, file_path: Path) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Thực hiện OCR nhận dạng chữ trên tệp (Ảnh hoặc PDF).
        Trả về tuple chứa: (danh sách dòng văn bản + tọa độ, văn bản thô hoàn chỉnh, độ tin cậy trung bình)
        """
        if not file_path.exists():
            raise OCRInferenceError(f"Không tìm thấy file tài liệu tại {file_path}")
            
        if file_path.suffix.lower() == '.pdf':
            return self._recognize_pdf(file_path)
            
        # 1. Gọi Engine nhận dạng văn bản thô
        raw_output = self.engine.recognize_image(file_path)
        if not raw_output:
            return [], "", 0.0

        # 2. Phân tích các grounding tags (nếu có) để lấy khung tọa độ (bounding boxes)
        # Định dạng chuẩn: <|ref|>text<|/ref|><|det|>[xmin, ymin, xmax, ymax]<|/det|>
        grounding_pattern = re.compile(
            r'<\|ref\|>(?P<text>.*?)<\|/ref\|><\|det\|>\[?\[?(?P<coords>[0-9,\s]+)\]?\]?<\|/det\|>'
        )

        # Lấy kích thước ảnh gốc phục vụ quy đổi tọa độ tỉ lệ [0, 1000] sang pixel thực tế
        from PIL import Image
        try:
            with Image.open(file_path) as img:
                img_w, img_h = img.size
        except Exception:
            img_w, img_h = 1000, 1000

        raw_lines = raw_output.split("\n")
        final_lines = []
        clean_lines = []
        index = 1

        for line in raw_lines:
            matches = list(grounding_pattern.finditer(line))
            clean_line = grounding_pattern.sub(lambda m: m.group("text"), line).strip()
            clean_line = unicodedata.normalize("NFC", clean_line).strip()
            
            if not clean_line and not matches:
                continue

            box = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
            
            if matches:
                # Tính bounding box gộp dòng
                min_x, min_y = float('inf'), float('inf')
                max_x, max_y = float('-inf'), float('-inf')
                
                for m in matches:
                    coords_str = m.group("coords")
                    coords = [int(x.strip()) for x in coords_str.split(",") if x.strip()]
                    if len(coords) == 4:
                        x1, y1, x2, y2 = coords
                        min_x = min(min_x, x1)
                        min_y = min(min_y, y1)
                        max_x = max(max_x, x2)
                        max_y = max(max_y, y2)
                
                if min_x != float('inf'):
                    real_xmin = float((min_x / 1000.0) * img_w)
                    real_ymin = float((min_y / 1000.0) * img_h)
                    real_xmax = float((max_x / 1000.0) * img_w)
                    real_ymax = float((max_y / 1000.0) * img_h)
                    
                    box = [
                        [real_xmin, real_ymin],
                        [real_xmax, real_ymin],
                        [real_xmax, real_ymax],
                        [real_xmin, real_ymax]
                    ]

            final_lines.append({
                "index": index,
                "text": clean_line,
                "confidence": 1.0,
                "box": box
            })
            clean_lines.append(clean_line)
            index += 1

        clean_text = "\n".join(clean_lines)
        avg_confidence = 1.0 if final_lines else 0.0
        
        return final_lines, clean_text, avg_confidence

    def _recognize_pdf(self, pdf_path: Path) -> Tuple[List[Dict[str, Any]], str, float]:
        """Chia tách PDF thành từng trang ảnh để nhận dạng tuần tự và gộp kết quả."""
        import fitz  # PyMuPDF
        import uuid
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise OCRInferenceError(f"Không thể mở tài liệu PDF: {str(e)}")
            
        num_pages = len(doc)
        if num_pages == 0:
            return [], "", 0.0
            
        pages_to_process = min(num_pages, settings.MAX_PDF_PAGES)
        all_lines = []
        combined_text_parts = []
        global_line_index = 1
        temp_dir = pdf_path.parent
        
        for page_num in range(pages_to_process):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            
            temp_img_name = f"temp_page_{page_num + 1}_{uuid.uuid4().hex[:8]}.png"
            temp_img_path = temp_dir / temp_img_name
            
            try:
                pix.save(str(temp_img_path))
                page_lines, page_text, _ = self.recognize(temp_img_path)
            except Exception as e:
                raise e
            finally:
                if temp_img_path.exists():
                    try:
                        os.remove(temp_img_path)
                    except:
                        pass
            
            page_header = f"# Trang {page_num + 1}\n"
            combined_text_parts.append(f"{page_header}{page_text}")
            
            for line in page_lines:
                clean_text = line["text"]
                all_lines.append({
                    "index": global_line_index,
                    "text": f"[Trang {page_num + 1}] {clean_text}",
                    "confidence": line["confidence"],
                    "box": line["box"]
                })
                global_line_index += 1
                
        doc.close()
        full_text = "\n\n---\n\n".join(combined_text_parts)
        avg_confidence = 1.0 if all_lines else 0.0
        
        return all_lines, full_text, avg_confidence


# Dịch vụ OCR đơn thể (Singleton)
ocr_service = None

def init_ocr_service() -> OCRService:
    global ocr_service
    if ocr_service is None:
        ocr_service = OCRService()
    return ocr_service
