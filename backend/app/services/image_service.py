from pathlib import Path
from typing import Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps
from app.core.config import settings
from app.core.exceptions import ImageProcessingError

class ImageService:
    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """
        Sắp xếp 4 tọa độ của hình tứ giác theo thứ tự nhất quán:
        [top-left, top-right, bottom-right, bottom-left].
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Điểm top-left có tổng x+y nhỏ nhất, bottom-right có tổng x+y lớn nhất
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Điểm top-right có hiệu y-x nhỏ nhất, bottom-left có hiệu y-x lớn nhất
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    @staticmethod
    def detect_and_warp_document(cv_img: np.ndarray, doc_type: str = "a4") -> Tuple[np.ndarray, bool]:
        """
        Phát hiện viền tài liệu bằng thuật toán Contour Detection.
        Nếu tìm thấy hình dạng tài liệu có 4 góc hợp lệ, thực hiện warp phối cảnh
        để đưa tài liệu về đúng định dạng chữ nhật với tỷ lệ tương ứng (giấy A4 hoặc thẻ CCCD).
        Trả về: (ảnh đã xử lý, cờ báo đã warp thành công).
        """
        h_orig, w_orig = cv_img.shape[:2]
        
        # Thay đổi kích thước tạm thời để tăng tốc độ và độ chính xác của tìm viền
        target_h = 1000
        ratio = h_orig / target_h
        cv_img_resized = cv2.resize(cv_img, (int(w_orig / ratio), target_h))
        h_res, w_res = cv_img_resized.shape[:2]
        
        # 1. Chuyển sang ảnh xám và lọc mịn nhiễu tần số cao giữ biên bằng bilateral filter
        gray = cv2.cvtColor(cv_img_resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 2. Tìm biên cạnh bằng Canny trực tiếp trên ảnh xám đã lọc mịn
        edged = cv2.Canny(blurred, 30, 120)
        
        # 3. Phép đóng hình thái học để nối các đường biên bị đứt khúc
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
        
        # 4. Tìm các đường bao (Contours) từ ảnh biên cạnh đã được đóng khép kín
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        doc_contour = None
        for c in contours:
            # Xấp xỉ đa giác cho đường bao
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            if len(approx) == 4:
                # Đảm bảo diện tích tài liệu chiếm ít nhất 15% tổng diện tích ảnh để loại trừ nhiễu nền
                area = cv2.contourArea(approx)
                if area > (w_res * h_res * 0.15):
                    doc_contour = approx
                    break
                    
        # Nếu bộ xấp xỉ nghiêm ngặt không ra 4 đỉnh, thử bộ lỏng hơn một chút
        if doc_contour is None:
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    if area > (w_res * h_res * 0.15):
                        doc_contour = approx
                        break
                        
        if doc_contour is not None:
            # Chuyển đổi tọa độ các đỉnh về kích thước ảnh gốc ban đầu
            pts = doc_contour.reshape(4, 2) * ratio
            
            # Sắp xếp các điểm góc chuẩn hóa
            rect = ImageService.order_points(pts)
            (tl, tr, br, bl) = rect
            
            # Tính toán kích thước tối đa của tài liệu được xoay thẳng
            width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            max_width = max(int(width_a), int(width_b))
            
            height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            max_height = max(int(height_a), int(height_b))
            
            # Áp đặt tỷ lệ kích thước tương ứng với từng loại tài liệu
            # Đồng thời đảm bảo độ phân giải đủ cao để model OCR nhìn rõ chữ nhỏ
            if doc_type == "cccd":
                # Tỷ lệ thẻ ID-1 tiêu chuẩn (85.60mm x 53.98mm ~ 1.5858 : 1)
                if max_height > max_width:
                    h_target = max(max_height, 1500)
                    w_target = int(h_target / 1.5858)
                else:
                    w_target = max(max_width, 1500)
                    h_target = int(w_target / 1.5858)
            else:
                # Tỷ lệ giấy A4 tiêu chuẩn (1 : 1.4142)
                if max_height > max_width:
                    w_target = max(max_width, 1500)
                    h_target = int(w_target * 1.4142)
                else:
                    h_target = max(max_height, 1500)
                    w_target = int(h_target * 1.4142)
                
            dst = np.array([
                [0, 0],
                [w_target - 1, 0],
                [w_target - 1, h_target - 1],
                [0, h_target - 1]
            ], dtype="float32")
            
            # Biến đổi phối cảnh sang định dạng thẳng thớm
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(cv_img, M, (w_target, h_target))
            return warped, True
            
        return cv_img, False

    @staticmethod
    def sharpen_image(cv_img: np.ndarray, strength: float = 0.8) -> np.ndarray:
        """
        Áp dụng Unsharp Masking để lấy nét biên chữ sắc nét hơn mà không làm tăng nhiễu hạt nền phẳng.
        """
        # Chuyển đổi sang float32 để tính toán chính xác không bị tràn số
        cv_img_float = cv_img.astype(np.float32)
        
        # Làm mịn ảnh bằng Gaussian Blur
        blurred = cv2.GaussianBlur(cv_img_float, (5, 5), 1.5)
        
        # Công thức Unsharp Masking: sharpened = original + strength * (original - blurred)
        sharpened = cv_img_float + strength * (cv_img_float - blurred)
        
        # Giới hạn giá trị màu về khoảng [0, 255] và đổi về định dạng uint8
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        return sharpened

    @staticmethod
    def preprocess_image(file_path: Path, doc_type: str = "a4") -> tuple[Path, bool]:
        """
        Đọc, tiền xử lý (sửa xoay, thay đổi kích thước, tìm viền A4/CCCD, tối ưu tương phản, lấy nét),
        và lưu đè lại file ảnh gốc.
        """
        if not file_path.exists():
            raise ImageProcessingError(f"Không tìm thấy file ảnh tại {file_path}")
            
        try:
            warped_successfully = False
            is_screenshot = file_path.suffix.lower() in (".png", ".webp")
            
            # 1. Tự động xoay ảnh theo EXIF và đọc dưới dạng RGB bằng Pillow
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img)
                
                # Xử lý kênh alpha (độ trong suốt) của ảnh chụp màn hình bằng cách ghép lên nền trắng
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    background.paste(img, (0, 0), img.convert("RGBA"))
                    img = background.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Kiểm tra kích thước
                width, height = img.size
                
                # 2. Resize lại nếu vượt quá giới hạn thiết lập tối đa
                max_w = settings.MAX_IMAGE_WIDTH
                max_h = settings.MAX_IMAGE_HEIGHT
                
                if width > max_w or height > max_h:
                    ratio = min(max_w / width, max_h / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Chuyển đổi từ PIL sang OpenCV (định dạng BGR)
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
            if settings.ENABLE_IMAGE_PREPROCESSING:
                # Nếu là định dạng CCCD, luôn áp dụng tiền xử lý (cắt viền, khử nhiễu, làm nét)
                # kể cả khi đuôi là PNG/WEBP (do Zalo/Facebook tự động chuyển ảnh chụp sang PNG)
                should_preprocess = (not is_screenshot) or (doc_type == "cccd")
                
                # 3. Phát hiện viền và xoay thẳng A4/CCCD cho ảnh chụp thực tế
                warped_successfully = False
                if should_preprocess:
                    cv_img, warped_successfully = ImageService.detect_and_warp_document(cv_img, doc_type=doc_type)
                
                # Chỉ áp dụng các bộ lọc nâng cao (khử nhiễu, cân bằng sáng CLAHE, làm nét)
                # nếu đã tìm thấy biên giấy tờ và warp thành công lên độ phân giải cao.
                # Nếu không warp thành công (ảnh chụp màn hình, ảnh tự cắt sẵn sát biên),
                # ta giữ nguyên ảnh gốc (RAW) để tránh nhiễu nền hoặc mờ nét chữ.
                if warped_successfully:
                    # Chuyển đổi sang hệ màu xám để đo độ sáng trung bình
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    mean_val = np.mean(gray)
                    
                    # 4. Phát hiện và đảo ngược màu của ảnh chế độ tối (chữ trắng nền đen)
                    if mean_val < 95:
                        cv_img = cv2.bitwise_not(cv_img)
                    
                    # 5. Khử nhiễu cục bộ bằng Bilateral Filter cho ảnh chụp máy ảnh
                    cv_img = cv2.bilateralFilter(cv_img, d=7, sigmaColor=35, sigmaSpace=35)
                    
                    # 6. Áp dụng CLAHE để cải thiện độ tương phản cục bộ, tăng độ sáng đều cho giấy tờ bị bóng râm
                    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
                    cl = clahe.apply(l)
                    limg = cv2.merge((cl, a, b))
                    cv_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
                    
                    # 7. Áp dụng Unsharp Masking để làm sắc nét nét chữ ("lấy nét")
                    cv_img = ImageService.sharpen_image(cv_img, strength=0.8)
                
            # Ghi đè lại ảnh đã được tiền xử lý tối ưu
            cv2.imwrite(str(file_path), cv_img)
            return file_path, warped_successfully
            
        except Exception as e:
            raise ImageProcessingError(f"Lỗi khi xử lý ảnh: {str(e)}")
