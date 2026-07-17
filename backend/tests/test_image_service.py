import numpy as np
import cv2
import pytest
from pathlib import Path
from app.services.image_service import ImageService

def test_order_points():
    # 4 points: tl, tr, br, bl
    # Sắp xếp đúng phải là: tl=[0, 0], tr=[200, 0], br=[200, 300], bl=[0, 300]
    shuffled = np.array([[200, 300], [0, 0], [0, 300], [200, 0]], dtype="float32")
    ordered = ImageService.order_points(shuffled)
    
    assert np.allclose(ordered[0], [0, 0])
    assert np.allclose(ordered[1], [200, 0])
    assert np.allclose(ordered[2], [200, 300])
    assert np.allclose(ordered[3], [0, 300])

def test_detect_and_warp_document_no_doc():
    # Nền đen hoàn toàn, không có tài liệu -> Trả về ảnh gốc và cờ False
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    warped, flag = ImageService.detect_and_warp_document(img)
    assert flag is False
    assert warped.shape == img.shape

def test_detect_and_warp_document_with_doc():
    # Tạo ảnh nền xám tối
    img = np.ones((1200, 1200, 3), dtype=np.uint8) * 50
    # Vẽ một hình tứ giác màu trắng đại diện cho tờ giấy tài liệu chiếm phần lớn ảnh
    pts = np.array([[200, 150], [1000, 200], [950, 1100], [150, 1050]], dtype=np.int32)
    cv2.fillPoly(img, [pts], (255, 255, 255))
    
    warped, flag = ImageService.detect_and_warp_document(img)
    assert flag is True
    # Kích thước kết quả phải tuân theo tỷ lệ A4 tiêu chuẩn (h/w ~ 1.414)
    h, w = warped.shape[:2]
    assert abs((h / w) - 1.4142) < 0.05

def test_detect_and_warp_document_with_cccd():
    # Tạo ảnh nền xám tối
    img = np.ones((1200, 1200, 3), dtype=np.uint8) * 50
    # Vẽ một hình tứ giác màu trắng đại diện cho thẻ CCCD (landscape) chiếm phần lớn ảnh
    pts = np.array([[200, 350], [1000, 350], [1000, 854], [200, 854]], dtype=np.int32)
    cv2.fillPoly(img, [pts], (255, 255, 255))
    
    warped, flag = ImageService.detect_and_warp_document(img, doc_type="cccd")
    assert flag is True
    # Kích thước kết quả phải tuân theo tỷ lệ CCCD (w/h ~ 1.5858)
    h, w = warped.shape[:2]
    assert abs((w / h) - 1.5858) < 0.05

def test_sharpen_image():
    # Kiểm tra hàm lấy nét chạy bình thường và giữ nguyên kích thước, kiểu dữ liệu
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    sharpened = ImageService.sharpen_image(img)
    assert sharpened.shape == img.shape
    assert sharpened.dtype == np.uint8

def test_grounding_parser(tmp_path):
    from unittest.mock import MagicMock
    from app.services.ocr_service import OCRService
    
    # Tạo ảnh thử nghiệm có kích thước Rộng=200, Cao=100
    img_path = tmp_path / "test.png"
    cv2.imwrite(str(img_path), np.zeros((100, 200, 3), dtype=np.uint8))
    
    # Giả lập đầu ra chứa grounding từ model
    # Tọa độ [100, 200, 300, 400] tương ứng:
    # xmin = 100/1000 * 200 = 20
    # ymin = 200/1000 * 100 = 20
    # xmax = 300/1000 * 200 = 60
    # ymax = 400/1000 * 100 = 40
    dummy_output = "<|ref|>Hello World<|/ref|><|det|>[100, 200, 300, 400]<|/det|>"
    
    service = OCRService()
    service.engine.recognize_image = MagicMock(return_value=dummy_output)
    
    lines, full_text, avg_conf = service.recognize(img_path)
    
    assert full_text == "Hello World"
    assert len(lines) == 1
    assert lines[0]["text"] == "Hello World"
    
    # Kiểm tra tọa độ quy đổi ngược lại điểm ảnh pixel
    expected_box = [
        [20.0, 20.0],
        [60.0, 20.0],
        [60.0, 40.0],
        [20.0, 40.0]
    ]
    assert np.allclose(lines[0]["box"], expected_box)

def test_parse_cccd_text():
    from app.api.ocr_routes import parse_cccd_text
    
    # Giả lập kết quả OCR thực tế chứa lỗi nhận dạng phân tách (dùng 'I' thay cho '/')
    dummy_ocr_text = """
    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
    Độc lập - Tự do - Hạnh phúc
    CĂN CƯỚC CÔNG DÂN
    Citizen Identity Card
    Số / No.: 03719002153
    Họ và tên I Full name:
    NGUYỄN THỊ HỒNG
    Ngày sinh / Date of birth: 28/09/1997
    Giới tính / Sex: Nữ Quốc tịch / Nationality: Việt Nam
    Quê quán / Place of origin:
    Cồn Thoi, Kim Sơn, Ninh Bình
    Nơi thường trú I Place of residence: Xóm 5
    Cồn Thoi, Kim Sơn, Ninh Bình
    Có giá trị đến / Date of expiry: 28/09/2037
    """
    
    ocr_lines = [{"text": line.strip(), "box": [[0,0],[0,0],[0,0],[0,0]]} for line in dummy_ocr_text.split("\n") if line.strip()]
    info, boxes = parse_cccd_text(ocr_lines, dummy_ocr_text)
    assert info.card_number == "03719002153"
    assert info.full_name == "NGUYỄN THỊ HỒNG"
    assert info.dob == "28/09/1997"
    assert info.gender == "Nữ"
    assert info.nationality == "Việt Nam"
    assert info.place_of_origin == "Cồn Thoi, Kim Sơn, Ninh Bình"
    assert info.place_of_residence == "Xóm 5, Cồn Thoi, Kim Sơn, Ninh Bình"

def test_parse_cccd_text_user_case():
    from app.api.ocr_routes import parse_cccd_text
    
    dummy_text = """
    text
    **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**
    image
    text
    **Độc lập - Tự do - Hạnh phúc**
    text
    **SOCIALIST REPUBLIC OF VIET NAM**
    text
    Independence - Freedom - Happiness
    text
    **CĂN CƯỚC CỘNG DÂN**
    image
    text
    **Citizen Identity Card**
    image
    text
    Số **/ No.:** **037197002153**
    text
    Họ và tên / Full name:
    text
    NGUYỄN THỊ HỒNG
    Ngày sinh / Date of birth: 28/09/1997
    text
    Giới tính / Sex: Nữ Quốc tịch / Nationality: Việt Nam
    text
    Quê quán / Place of origin:
    text
    Côn Thoị, Kim Sơn, Ninh Bình
    text
    Nơi thường trú / Place of residence: Xóm 5
    text
    Có giá trị đến: 28/09/2037
    text
    Date of expiry: Côn Thoị, Kim Sơn, Ninh Bình
    """
    
    ocr_lines = [{"text": line.strip(), "box": [[0,0],[0,0],[0,0],[0,0]]} for line in dummy_text.split("\n") if line.strip()]
    info, boxes = parse_cccd_text(ocr_lines, dummy_text)
    assert info.card_number == "037197002153"
    assert info.full_name == "NGUYỄN THỊ HỒNG"
    assert info.dob == "28/09/1997"
    assert info.gender == "Nữ"
    assert info.nationality == "Việt Nam"
    assert info.place_of_origin == "Côn Thoị, Kim Sơn, Ninh Bình"
    assert info.place_of_residence == "Xóm 5, Côn Thoị, Kim Sơn, Ninh Bình"
