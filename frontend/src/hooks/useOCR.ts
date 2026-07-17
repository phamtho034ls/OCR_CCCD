import { useState, useEffect } from 'react';
import { OCRResponse, CCCDInfo } from '../types/ocr';
import { uploadAndPreprocess, recognizePreprocessed } from '../services/ocrApi';
import { validateFile } from '../utils/fileValidation';
import axios from 'axios';

export function useOCR() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResponse | null>(null);
  const [editedText, setEditedText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [docType, setDocType] = useState<string>('a4');
  const [cccdInfo, setCccdInfo] = useState<CCCDInfo | null>(null);

  // New scanning progress states
  const [scanLogs, setScanLogs] = useState<string[]>([]);
  const [playbackLines, setPlaybackLines] = useState<string[]>([]);
  const [isPlaybackActive, setIsPlaybackActive] = useState<boolean>(false);
  const [playbackProgress, setPlaybackProgress] = useState<number>(0);

  // Generate image object URL for local browser preview
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Cleanup object URL to prevent memory leaks
    return () => {
      if (url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
      }
    };
  }, [file]);

  const selectFile = (newFile: File) => {
    setError(null);
    const validationError = validateFile(newFile);
    if (validationError) {
      setError(validationError);
      return;
    }
    setFile(newFile);
    // Reset previous state when uploading a new document
    setOcrResult(null);
    setEditedText('');
    setScanLogs([]);
    setPlaybackLines([]);
    setIsPlaybackActive(false);
    setPlaybackProgress(0);
    setCccdInfo(null);
  };

  const clearFile = () => {
    setFile(null);
    setOcrResult(null);
    setEditedText('');
    setError(null);
    setScanLogs([]);
    setPlaybackLines([]);
    setIsPlaybackActive(false);
    setPlaybackProgress(0);
    setCccdInfo(null);
  };

  const runOCR = async () => {
    if (!file) {
      setError('Vui lòng chọn hoặc kéo thả một file ảnh trước.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOcrResult(null);
    setEditedText('');
    setPlaybackLines([]);
    setPlaybackProgress(0);
    setIsPlaybackActive(false);

    // Giai đoạn 1: Nhật ký tiền xử lý ảnh
    setScanLogs([
      '🚀 Khởi động tiến trình nhận dạng tài liệu local...',
      '🛠️ Đang tải ảnh lên và chạy tiền xử lý (cắt viền, xoay hướng EXIF, lọc nhiễu)...'
    ]);

    try {
      // Gọi API 1 để tải và tiền xử lý
      const uploadResult = await uploadAndPreprocess(file, docType);
      
      if (!uploadResult.success) {
        setError('Tiền xử lý ảnh thất bại. Vui lòng thử lại.');
        setIsLoading(false);
        return;
      }

      // Đưa ảnh đã cắt viền/tiền xử lý lên làm ảnh xem trước luôn để tăng độ hài lòng người dùng
      if (uploadResult.processed_image) {
        setPreviewUrl(uploadResult.processed_image);
      }

      // Cập nhật trạng thái logs chuyển tiếp giai đoạn 2
      setScanLogs(prev => [
        ...prev,
        uploadResult.warped_successfully 
          ? '🎯 Đã phát hiện và cắt viền tài liệu thành công!' 
          : '⚠️ Không phát hiện rõ viền tài liệu, sử dụng ảnh gốc làm nét.',
        '🤖 Khởi chạy mô hình DeepSeek-OCR trên card đồ họa CUDA GPU...',
        '🔍 Mô hình DeepEncoder phân tích mảnh ảnh (Image cropping & resizing)...',
        '🧠 Đang nhận diện ký tự tiếng Việt bằng mô hình AI...'
      ]);

      // Gọi API 2 chạy mô hình DeepSeek-OCR nhận dạng
      const result = await recognizePreprocessed(uploadResult.file_token, docType);
      
      if (result.success) {
        setScanLogs(prev => [...prev, '⚖️ Định dạng văn bản và hiển thị kết quả...']);
        setOcrResult(result);
        if (result.cccd_info) {
          setCccdInfo(result.cccd_info);
        }
        
        // Phase 2: Start playing back line-by-line scanning animation
        setIsPlaybackActive(true);
        setIsLoading(false); // Done loading from API
        
        const linesToScan = result.lines || [];
        let currentLineIndex = 0;
        
        if (linesToScan.length === 0) {
          setIsPlaybackActive(false);
          setEditedText(result.full_text);
          setPlaybackProgress(100);
          return;
        }

        const scanInterval = setInterval(() => {
          if (currentLineIndex < linesToScan.length) {
            const newLine = linesToScan[currentLineIndex].text;
            setPlaybackLines(prev => [...prev, newLine]);
            currentLineIndex++;
            setPlaybackProgress(Math.round((currentLineIndex / linesToScan.length) * 100));
          } else {
            clearInterval(scanInterval);
            setIsPlaybackActive(false);
            setEditedText(result.full_text);
          }
        }, 120); // 120ms per line scanning effect
        
      } else {
        setError('Nhận dạng thất bại. Không rõ nguyên nhân từ mô hình.');
        setIsLoading(false);
      }
    } catch (err: any) {
      setIsLoading(false);
      console.error(err);
      if (axios.isAxiosError(err)) {
        if (err.response?.data?.detail) {
          setError(err.response.data.detail);
        } else if (err.response?.data?.message) {
          setError(err.response.data.message);
        } else if (err.code === 'ECONNABORTED') {
          setError('Yêu cầu quá hạn (Timeout). Backend xử lý quá lâu.');
        } else {
          setError('Không thể kết nối tới Backend. Vui lòng kiểm tra xem Backend đã khởi chạy chưa (Port 8000).');
        }
      } else {
        setError(err.message || 'Đã xảy ra lỗi không xác định.');
      }
    }
  };

  const resetOCR = () => {
    setOcrResult(null);
    setEditedText('');
    setError(null);
    setScanLogs([]);
    setPlaybackLines([]);
    setIsPlaybackActive(false);
    setPlaybackProgress(0);
    setCccdInfo(null);
  };

  return {
    file,
    previewUrl,
    ocrResult,
    editedText,
    isLoading,
    error,
    scanLogs,
    playbackLines,
    isPlaybackActive,
    playbackProgress,
    selectFile,
    clearFile,
    runOCR,
    setEditedText,
    resetOCR,
    setError,
    docType,
    setDocType,
    cccdInfo,
    setCccdInfo,
  };
}
