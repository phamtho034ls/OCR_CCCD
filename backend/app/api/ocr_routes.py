import time
import shutil
import logging
import re
import unicodedata
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.core.config import settings
from app.schemas.ocr_schema import OCRResponse, CCCDInfo, CCCDBoxes, UploadResponse, CCCDOCRResponse, A4OCRResponse
from typing import Optional
from app.utils.file_utils import (
    validate_uploaded_file, 
    validate_file_size, 
    sanitize_filename
)
from app.services.image_service import ImageService
from app.services.ocr_service import init_ocr_service, OCRService

router = APIRouter()

# Initialize path
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def parse_cccd_text(ocr_lines: list, full_text: str) -> tuple[CCCDInfo, CCCDBoxes]:
    """
    Trích xuất các trường thông tin CCCD từ văn bản OCR thô bằng biểu thức chính quy (Regex) cải tiến.
    Hỗ trợ bỏ qua dòng rác (text, image, markdown bold) và ghép địa chỉ bị xáo trộn do thứ tự đọc.
    Đồng thời lấy ra tọa độ (bounding boxes) tương ứng của từng trường dữ liệu.
    """
    info = {
        "card_number": "",
        "full_name": "",
        "dob": "",
        "gender": "",
        "nationality": "",
        "place_of_origin": "",
        "place_of_residence": ""
    }
    
    boxes = {
        "card_number": None,
        "full_name": None,
        "dob": None,
        "gender": None,
        "nationality": None,
        "place_of_origin": None,
        "place_of_residence": None
    }
    
    # Tách dòng, chuẩn hóa NFC và lọc bỏ các dòng rác ("text", "image", trống)
    lines = []
    for item in ocr_lines:
        line_text = item.get("text", "").strip()
        box = item.get("box", None)
        
        # Chuẩn hóa unicode tiếng Việt
        line_text = unicodedata.normalize("NFC", line_text)
        # Loại bỏ các ký tự định dạng markdown bold/italic
        line_text = line_text.replace("**", "").replace("***", "").replace("*", "").strip()
        
        # Bỏ qua dòng rác chỉ chứa chữ "text" hoặc "image" hoặc trống
        cleaned_lower = line_text.lower()
        if cleaned_lower in ("text", "image", ""):
            continue
        lines.append({
            "text": line_text,
            "box": box
        })
        
    # Danh sách các từ khóa đánh dấu để tránh lấy nhầm dòng tiếp theo
    keys_pat = [
        r'Số\s*/\s*No', r'No\.?', r'Họ\s*(?:và\s*)?tên', r'Full\s*name',
        r'Ngày\s*sinh', r'Date\s*of\s*birth', r'Giới\s*tính', r'Sex',
        r'Quốc\s*tịch', r'Nationality', r'Quê\s*quán', r'Place\s*of\s*origin',
        r'Nơi\s*thường\s*trú', r'Place\s*of\s*residence', r'Có\s*giá\s*trị\s*đến', r'Date\s*of\s*expiry'
    ]
    
    for i, item in enumerate(lines):
        line = item["text"]
        box = item["box"]
        
        # 1. Số CCCD / No.
        num_match = re.search(r'(?:Số|No)[\s/|Il1\\:\.]+(?:No)?[\s:\.]*(\d{9,12})', line, re.IGNORECASE)
        if num_match:
            info["card_number"] = num_match.group(1)
            boxes["card_number"] = box
        elif not info["card_number"]:
            fb_num = re.search(r'\b(\d{9}|\d{12})\b', line)
            if fb_num:
                info["card_number"] = fb_num.group(1)
                boxes["card_number"] = box
                
        # 2. Họ và tên / Full name
        name_match = re.search(r'(?:Họ\s*(?:và\s*)?tên|Full\s*name)(?:[\s/|Il1\\:\.]+Full\s*name)?[\s/|Il1\\:\.]*(.*)', line, re.IGNORECASE)
        if name_match:
            val = name_match.group(1).strip()
            if val and val.lower() not in ["full name", "fullname", "name"]:
                info["full_name"] = val
                boxes["full_name"] = box
            elif i + 1 < len(lines):
                next_line = lines[i+1]["text"].strip()
                if not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    info["full_name"] = next_line
                    boxes["full_name"] = lines[i+1]["box"]
                
        # 3. Ngày sinh / Date of birth
        dob_match = re.search(r'(?:Ngày\s*sinh|Date\s*of\s*birth)(?:[\s/|Il1\\:\.]+Date\s*of\s*birth)?[\s/|Il1\\:\.]*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
        if dob_match:
            info["dob"] = dob_match.group(1)
            boxes["dob"] = box
        elif not info["dob"]:
            fb_dob = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', line)
            if fb_dob:
                info["dob"] = fb_dob.group(1)
                boxes["dob"] = box
                
        # 4. Giới tính / Sex
        gender_match = re.search(r'(?:Giới\s*tính|Sex)(?:[\s/|Il1\\:\.]+Sex)?[\s/|Il1\\:\.]*(Nam|Nữ)', line, re.IGNORECASE)
        if gender_match:
            info["gender"] = gender_match.group(1)
            boxes["gender"] = box
            
        # 5. Quốc tịch / Nationality
        nat_match = re.search(r'(?:Quốc\s*tịch|Nationality)(?:[\s/|Il1\\:\.]+Nationality)?[\s/|Il1\\:\.]*(.*)', line, re.IGNORECASE)
        if nat_match:
            val = nat_match.group(1).strip()
            if val and val.lower() not in ["nationality", "national", "nationally"]:
                info["nationality"] = val
                boxes["nationality"] = box
            elif i + 1 < len(lines):
                next_line = lines[i+1]["text"].strip()
                if not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    info["nationality"] = next_line
                    boxes["nationality"] = lines[i+1]["box"]
                    
        # Fallback mặc định cho quốc tịch nếu trống hoặc nhận diện nhầm sang nhãn tiếng Anh
        if not info.get("nationality") or info["nationality"].lower() in ["nationality", "national", "nationally", ""]:
            info["nationality"] = "Việt Nam"
            
        # 6. Quê quán / Place of origin
        origin_match = re.search(r'(?:Quê\s*quán|Place\s*of\s*origin)(?:[\s/|Il1\\:\.]+Place\s*of\s*origin)?[\s/|Il1\\:\.]*(.*)', line, re.IGNORECASE)
        if origin_match:
            val = origin_match.group(1).strip()
            if val and val.lower() not in ["place of origin", "placeoforigin", "origin"]:
                info["place_of_origin"] = val
                boxes["place_of_origin"] = box
            elif i + 1 < len(lines):
                next_line = lines[i+1]["text"].strip()
                if not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    info["place_of_origin"] = next_line
                    boxes["place_of_origin"] = lines[i+1]["box"]
            
            # Hỗ trợ địa chỉ quê quán xuống dòng
            curr_idx = i + 1
            while curr_idx < len(lines):
                next_line = lines[curr_idx]["text"].strip()
                if any(k in next_line.lower() for k in ["nơi thường trú", "place of residence", "có giá trị đến", "date of expiry"]):
                    break
                if next_line and not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    if not info["place_of_origin"]:
                        info["place_of_origin"] = next_line
                    elif next_line not in info["place_of_origin"]:
                        info["place_of_origin"] += ", " + next_line
                curr_idx += 1
                
        # 7. Nơi thường trú / Place of residence
        residence_match = re.search(r'(?:Nơi\s*thường\s*trú|Place\s*of\s*residence)(?:[\s/|Il1\\:\.]+Place\s*of\s*residence)?[\s/|Il1\\:\.]*(.*)', line, re.IGNORECASE)
        if residence_match:
            val = residence_match.group(1).strip()
            if val and val.lower() not in ["place of residence", "placeofresidence", "residence"]:
                info["place_of_residence"] = val
                boxes["place_of_residence"] = box
            elif i + 1 < len(lines):
                next_line = lines[i+1]["text"].strip()
                if not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    info["place_of_residence"] = next_line
                    boxes["place_of_residence"] = lines[i+1]["box"]
                    
            # Hỗ trợ địa chỉ thường trú xuống dòng
            curr_idx = i + 1
            while curr_idx < len(lines):
                next_line = lines[curr_idx]["text"].strip()
                if next_line.lower() in ["text", "image", ""]:
                    curr_idx += 1
                    continue
                if any(k in next_line.lower() for k in ["có giá trị đến", "date of expiry"]) or re.search(r'\b\d{2}/\d{2}/\d{4}\b', next_line):
                    curr_idx += 1
                    continue
                if any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    break
                if next_line and not any(re.search(pat, next_line, re.IGNORECASE) for pat in keys_pat):
                    if not info["place_of_residence"]:
                        info["place_of_residence"] = next_line
                    elif next_line not in info["place_of_residence"]:
                        info["place_of_residence"] += ", " + next_line
                curr_idx += 1

    # Hậu xử lý: Ghép phần địa chỉ bị trôi xuống sau nhãn "Có giá trị đến / Date of expiry" do thứ tự đọc OCR
    for item in lines:
        line = item["text"]
        box = item["box"]
        if any(x in line.lower() for x in ["expiry", "giá trị", "đến"]):
            parts = line.split(":", 1)
            if len(parts) > 1:
                val = parts[1].strip()
                # Nếu phần giá trị không phải là ngày sinh/ngày hết hạn và chứa thông tin địa chỉ
                if val and not re.search(r'\b\d{2}/\d{2}/\d{4}\b', val):
                    if val not in info["place_of_residence"]:
                        if info["place_of_residence"]:
                            info["place_of_residence"] += ", " + val
                        else:
                            info["place_of_residence"] = val
                        # Lưu tọa độ cho Nơi thường trú
                        boxes["place_of_residence"] = box
                
    # Dọn dẹp dấu phẩy thừa
    for k in info:
        val = info[k]
        val = re.sub(r'\s+', ' ', val)
        # Loại bỏ các dấu phẩy liên tiếp (ví dụ: Xóm 5,, Côn Thọi)
        val = re.sub(r',\s*,', ',', val)
        val = re.sub(r',+', ',', val)
        val = re.sub(r'^,\s*|,\s*$', '', val)
        info[k] = val.strip()
        
    return CCCDInfo(**info), CCCDBoxes(**boxes)

def image_to_base64(image_path: Path) -> Optional[str]:
    """Chuyển đổi tệp ảnh đã xử lý sang định dạng Base64 URI."""
    if image_path.suffix.lower() == '.pdf' or not image_path.exists():
        return None
    import base64
    try:
        with open(image_path, "rb") as img_file:
            encoded_data = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type = "image/png"
            suffix = image_path.suffix.lower()
            if suffix in (".jpg", ".jpeg"):
                mime_type = "image/jpeg"
            elif suffix == ".webp":
                mime_type = "image/webp"
            return f"data:{mime_type};base64,{encoded_data}"
    except Exception as e:
        logging.error(f"Lỗi chuyển đổi ảnh sang base64: {e}")
        return None

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "local-ocr-api",
        "ocr_model": settings.OCR_MODEL_ID,
        "device": settings.OCR_DEVICE
    }



def handle_upload_preprocess(file: UploadFile, doc_type: str) -> UploadResponse:
    """Hàm helper thống nhất cho tiến trình upload và tiền xử lý ảnh theo loại tài liệu."""
    # 1. Validation cơ bản
    validate_uploaded_file(file)
    
    # 2. Tạo định danh an toàn
    import uuid
    safe_name = sanitize_filename(file.filename)
    ext = Path(file.filename).suffix.lower()
    file_token = f"{uuid.uuid4().hex}{ext}"
    processed_path = UPLOAD_DIR / f"processed_{file_token}"
    
    try:
        # 3. Ghi file trực tiếp
        with open(processed_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 4. Kiểm tra kích thước file
        validate_file_size(processed_path)
        
        # 5. Tiền xử lý (Cắt viền, xoay thẳng, bộ lọc)
        warped_successfully = False
        if ext == '.pdf':
            pass
        else:
            processed_path, warped_successfully = ImageService.preprocess_image(processed_path, doc_type=doc_type)
            
        # 6. Chuyển đổi sang base64 để hiển thị xem trước
        processed_image_base64 = image_to_base64(processed_path)
        
        return UploadResponse(
            success=True,
            file_token=file_token,
            file_name=safe_name,
            processed_image=processed_image_base64,
            warped_successfully=warped_successfully
        )
    except Exception as e:
        # Xóa file nếu lỗi phát sinh trong khâu tiền xử lý
        if processed_path.exists():
            try:
                processed_path.unlink()
            except Exception:
                pass
        raise e

@router.post("/ocr/cccd/upload", response_model=UploadResponse)
def upload_cccd(file: UploadFile = File(...)):
    """API 1 (CCCD): Tiếp nhận ảnh CCCD, chạy tiền xử lý tối ưu CCCD và trả về token."""
    return handle_upload_preprocess(file, doc_type="cccd")

@router.post("/ocr/a4/upload", response_model=UploadResponse)
def upload_a4(file: UploadFile = File(...)):
    """API 1 (A4): Tiếp nhận ảnh/PDF A4, chạy tiền xử lý tối ưu A4 và trả về token."""
    return handle_upload_preprocess(file, doc_type="a4")

@router.post("/ocr/cccd/recognize", response_model=CCCDOCRResponse)
def recognize_cccd(
    file_token: str = Form(...),
    ocr_service: OCRService = Depends(init_ocr_service)
):
    """API 2 (CCCD): Nhận dạng chữ viết trên CCCD, trích xuất cấu trúc trường thông tin CCCD và trả về."""
    if not re.match(r'^[a-f0-9]{32}\.[a-zA-Z0-9]+$', file_token):
        raise HTTPException(status_code=400, detail="Token tệp không hợp lệ")
        
    processed_path = UPLOAD_DIR / f"processed_{file_token}"
    if not processed_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp ảnh đã tiền xử lý hoặc phiên làm việc đã hết hạn.")
        
    start_time = time.time()
    try:
        # 1. Chạy mô hình DeepSeek-OCR
        lines, full_text, avg_confidence = ocr_service.recognize(processed_path)
        
        # 2. Lấy base64 ảnh phục vụ vẽ Bounding Box
        processed_image_base64 = image_to_base64(processed_path)
        
        # 3. Phân tích trường thông tin chuyên biệt cho CCCD
        cccd_info, cccd_boxes = parse_cccd_text(lines, full_text)
            
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        return CCCDOCRResponse(
            success=True,
            file_name=file_token,
            processing_time_ms=elapsed_ms,
            full_text=full_text,
            line_count=len(lines),
            average_confidence=avg_confidence,
            lines=lines,
            processed_image=processed_image_base64,
            cccd_info=cccd_info,
            cccd_boxes=cccd_boxes
        )
    finally:
        # Đảm bảo xóa tệp sau khi hoàn thành
        if processed_path.exists():
            try:
                processed_path.unlink()
            except Exception as e:
                logging.error(f"Lỗi khi xóa tệp đã tiền xử lý {processed_path}: {e}")

@router.post("/ocr/a4/recognize", response_model=A4OCRResponse)
def recognize_a4(
    file_token: str = Form(...),
    ocr_service: OCRService = Depends(init_ocr_service)
):
    """API 2 (A4): Nhận dạng chữ viết trên A4 và trả về toàn bộ dòng chữ nhận diện được."""
    if not re.match(r'^[a-f0-9]{32}\.[a-zA-Z0-9]+$', file_token):
        raise HTTPException(status_code=400, detail="Token tệp không hợp lệ")
        
    processed_path = UPLOAD_DIR / f"processed_{file_token}"
    if not processed_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp ảnh đã tiền xử lý hoặc phiên làm việc đã hết hạn.")
        
    start_time = time.time()
    try:
        # 1. Chạy mô hình DeepSeek-OCR
        lines, full_text, avg_confidence = ocr_service.recognize(processed_path)
        
        # 2. Lấy base64 ảnh phục vụ xem trước
        processed_image_base64 = image_to_base64(processed_path)
            
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        return A4OCRResponse(
            success=True,
            file_name=file_token,
            processing_time_ms=elapsed_ms,
            full_text=full_text,
            line_count=len(lines),
            average_confidence=avg_confidence,
            lines=lines,
            processed_image=processed_image_base64
        )
    finally:
        # Đảm bảo xóa tệp sau khi hoàn thành
        if processed_path.exists():
            try:
                processed_path.unlink()
            except Exception as e:
                logging.error(f"Lỗi khi xóa tệp đã tiền xử lý {processed_path}: {e}")
