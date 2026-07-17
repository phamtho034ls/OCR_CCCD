from pydantic import BaseModel
from typing import List, Optional

class OCRLine(BaseModel):
    index: int
    text: str
    confidence: float
    box: List[List[float]]

class CCCDInfo(BaseModel):
    card_number: str = ""
    full_name: str = ""
    dob: str = ""
    gender: str = ""
    nationality: str = ""
    place_of_origin: str = ""
    place_of_residence: str = ""

class CCCDBoxes(BaseModel):
    card_number: Optional[List[List[float]]] = None
    full_name: Optional[List[List[float]]] = None
    dob: Optional[List[List[float]]] = None
    gender: Optional[List[List[float]]] = None
    nationality: Optional[List[List[float]]] = None
    place_of_origin: Optional[List[List[float]]] = None
    place_of_residence: Optional[List[List[float]]] = None

class OCRResponse(BaseModel):
    """Lược đồ phản hồi OCR chung (tương thích ngược)."""
    success: bool = True
    file_name: str
    processing_time_ms: float
    full_text: str
    line_count: int
    average_confidence: float
    lines: List[OCRLine]
    processed_image: Optional[str] = None
    cccd_info: Optional[CCCDInfo] = None
    cccd_boxes: Optional[CCCDBoxes] = None

class UploadResponse(BaseModel):
    """Lược đồ phản hồi sau khi upload và tiền xử lý ảnh xong."""
    success: bool = True
    file_token: str
    file_name: str
    processed_image: Optional[str] = None
    warped_successfully: bool = False

class CCCDOCRResponse(BaseModel):
    """Lược đồ phản hồi chuyên biệt cho thẻ CCCD."""
    success: bool = True
    file_name: str
    processing_time_ms: float
    full_text: str
    line_count: int
    average_confidence: float
    lines: List[OCRLine]
    processed_image: Optional[str] = None
    cccd_info: CCCDInfo
    cccd_boxes: CCCDBoxes

class A4OCRResponse(BaseModel):
    """Lược đồ phản hồi chuyên biệt cho giấy tờ văn bản A4."""
    success: bool = True
    file_name: str
    processing_time_ms: float
    full_text: str
    line_count: int
    average_confidence: float
    lines: List[OCRLine]
    processed_image: Optional[str] = None
