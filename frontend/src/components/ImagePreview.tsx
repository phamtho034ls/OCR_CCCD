import { useState, useEffect } from 'react';
import { OCRResponse } from '../types/ocr';

interface ImagePreviewProps {
  file: File;
  previewUrl: string;
  onClear: () => void;
  onRunOCR: () => void;
  isLoading: boolean;
  hasResult: boolean;
  isPlaybackActive?: boolean;
  ocrResult?: OCRResponse | null;
  playbackLinesCount?: number;
  activeField?: string | null;
  docType?: string;
}

export default function ImagePreview({
  file,
  previewUrl,
  onClear,
  onRunOCR,
  isLoading,
  hasResult,
  isPlaybackActive = false,
  ocrResult = null,
  playbackLinesCount = 0,
  activeField = null,
  docType = 'a4',
}: ImagePreviewProps) {
  const [imageSize, setImageSize] = useState({ w: 0, h: 0 });

  // Reset kích thước ảnh khi đổi file
  useEffect(() => {
    setImageSize({ w: 0, h: 0 });
  }, [file]);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  
  // Hiển thị ảnh A4 đã hiệu chỉnh/lấy nét sau khi OCR thành công, ngược lại dùng URL xem trước gốc
  const displayUrl = ocrResult?.processed_image || previewUrl;
  const linesToRender = ocrResult?.lines || [];

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ w: img.naturalWidth, h: img.naturalHeight });
  };

  // Xác định tọa độ hộp của trường thông tin đang active để vẽ nổi bật
  const activeBox = (activeField && ocrResult?.cccd_boxes)
    ? (ocrResult.cccd_boxes as any)[activeField] as number[][] | undefined
    : null;

  return (
    <div className="preview-container">
      <div className="preview-wrapper" style={{ position: 'relative', overflow: 'hidden' }}>
        {isPdf ? (
          <div className="pdf-preview-placeholder">
            <svg className="pdf-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 15h6M9 11h6" />
            </svg>
            <div className="pdf-text">Tài liệu PDF</div>
          </div>
        ) : (
          <div className="image-highlight-wrapper" style={{ position: 'relative', width: '100%', display: 'inline-block' }}>
            <img 
              src={displayUrl} 
              alt="Xem trước tài liệu" 
              className="preview-image" 
              onLoad={handleImageLoad}
              style={{ display: 'block', width: '100%', height: 'auto' }}
            />
            {/* SVG overlay vẽ bounding box */}
            {imageSize.w > 0 && (linesToRender.length > 0 || activeBox) && (
              <svg
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'auto'
                }}
                viewBox={`0 0 ${imageSize.w} ${imageSize.h}`}
              >
                {linesToRender.map((line) => {
                  // Bỏ qua nếu tọa độ rỗng hoặc lỗi
                  const isValidBox = line.box && line.box.some(pt => pt[0] !== 0 || pt[1] !== 0);
                  if (!isValidBox) return null;

                  // Xác định trạng thái của dòng trong tiến trình chạy chữ
                  const isScanned = !isPlaybackActive || line.index <= playbackLinesCount;
                  const isActive = isPlaybackActive && line.index === playbackLinesCount + 1;

                  if (!isScanned && !isActive) return null;

                  const pointsStr = line.box.map(pt => `${pt[0]},${pt[1]}`).join(' ');

                  return (
                    <polygon
                      key={`poly-${line.index}`}
                      points={pointsStr}
                      fill={isActive ? "rgba(16, 185, 129, 0.25)" : "rgba(59, 130, 246, 0.12)"}
                      stroke={isActive ? "#10b981" : "rgba(59, 130, 246, 0.6)"}
                      strokeWidth={isActive ? 3 : 1.5}
                      className={`ocr-polygon-box ${isActive ? 'active' : ''}`}
                      style={{
                        transition: 'all 0.15s ease',
                        cursor: 'pointer',
                        transformOrigin: 'center'
                      }}
                    >
                      <title>{`[Dòng ${line.index}] ${line.text}`}</title>
                    </polygon>
                  );
                })}

                {/* Vẽ viền riêng biệt màu vàng hổ phách cho trường thông tin đang được hover/focus */}
                {activeBox && activeBox.length >= 4 && (
                  <polygon
                    points={activeBox.map(pt => `${pt[0]},${pt[1]}`).join(' ')}
                    fill="rgba(245, 158, 11, 0.25)"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    className="ocr-polygon-box active-field"
                    style={{
                      transition: 'all 0.15s ease',
                      pointerEvents: 'none'
                    }}
                  />
                )}
              </svg>
            )}
            
            {/* Vẽ viền ngoài bo tròn bọc toàn bộ thẻ CCCD sau khi có kết quả */}
            {docType === 'cccd' && hasResult && (
              <>
                <div className="cccd-outer-border-frame"></div>
                <div className="cccd-verified-badge">
                  <svg style={{ width: '14px', height: '14px', fill: 'currentColor' }} viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  ĐỊNH DẠNG CCCD HỢP LỆ
                </div>
              </>
            )}
          </div>
        )}
        {(isLoading || isPlaybackActive) && <div className="scanner-line"></div>}
      </div>
      
      <div className="preview-meta">
        <div style={{ minWidth: 0, flex: 1, marginRight: '1rem' }}>
          <span style={{ 
            fontWeight: 600, 
            display: 'block', 
            color: 'var(--text-main)', 
            overflow: 'hidden', 
            textOverflow: 'ellipsis', 
            whiteSpace: 'nowrap' 
          }}>
            {file.name}
          </span>
          <span style={{ fontSize: '0.8rem' }}>{formatSize(file.size)}</span>
        </div>
        <button 
          className="btn btn-secondary btn-action" 
          onClick={onClear} 
          disabled={isLoading}
        >
          Đổi ảnh khác
        </button>
      </div>

      <div className="preview-actions">
        <button 
          className="btn btn-primary" 
          style={{ flex: 1 }} 
          onClick={onRunOCR} 
          disabled={isLoading}
        >
          <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          {hasResult ? 'OCR lại' : 'Bắt đầu OCR'}
        </button>
      </div>
    </div>
  );
}
