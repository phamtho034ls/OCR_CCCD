import { useState, useEffect, useRef } from 'react';
import { OCRResponse, CCCDInfo } from '../types/ocr';
import { downloadText } from '../utils/downloadText';

interface OCRResultProps {
  result: OCRResponse | null;
  editedText: string;
  onTextChange: (text: string) => void;
  onClear: () => void;
  isLoading: boolean;
  scanLogs: string[];
  playbackLines: string[];
  isPlaybackActive: boolean;
  playbackProgress: number;
  docType: string;
  cccdInfo: CCCDInfo | null;
  onCccdInfoChange: (info: CCCDInfo | null) => void;
  activeField: string | null;
  onActiveFieldChange: (field: string | null) => void;
}

export default function OCRResult({
  result,
  editedText,
  onTextChange,
  onClear,
  isLoading,
  scanLogs,
  playbackLines,
  isPlaybackActive,
  playbackProgress,
  docType,
  cccdInfo,
  onCccdInfoChange,
  onActiveFieldChange,
}: OCRResultProps) {
  const [showToast, setShowToast] = useState<boolean>(false);
  const terminalBodyRef = useRef<HTMLDivElement>(null);

  // Hàm định dạng thông tin CCCD thành chuỗi văn bản thuần để sao chép/tải xuống
  const getCccdFormattedText = (info: CCCDInfo | null): string => {
    if (!info) return '';
    return `Số CCCD: ${info.card_number || ''}
Họ tên: ${info.full_name || ''}
Ngày sinh: ${info.dob || ''}
Giới tính: ${info.gender || ''}
Quốc tịch: ${info.nationality || ''}
Quê quán: ${info.place_of_origin || ''}
Nơi thường trú: ${info.place_of_residence || ''}`;
  };

  const handleCopy = async () => {
    try {
      const textToCopy = docType === 'cccd' ? getCccdFormattedText(cccdInfo) : editedText;
      await navigator.clipboard.writeText(textToCopy);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 2000);
    } catch (err) {
      console.error('Không thể sao chép văn bản:', err);
    }
  };

  const handleDownload = () => {
    if (result) {
      const textToDownload = docType === 'cccd' ? getCccdFormattedText(cccdInfo) : editedText;
      downloadText(textToDownload, result.file_name);
    }
  };

  const handleCccdFieldChange = (field: keyof CCCDInfo, value: string) => {
    if (cccdInfo) {
      onCccdInfoChange({
        ...cccdInfo,
        [field]: value,
      });
    }
  };

  // Tự động cuộn terminal xuống dưới cùng
  useEffect(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [scanLogs, playbackLines, isPlaybackActive]);

  if (!result && !isLoading) {
    return (
      <div className="result-container" style={{ justifyContent: 'center' }}>
        <div className="result-placeholder">
          <svg className="placeholder-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}>Chưa có kết quả OCR</h3>
          <p style={{ fontSize: '0.85rem', marginTop: '0.35rem', maxWidth: '300px' }}>
            Chọn ảnh tài liệu phía bên trái, sau đó nhấn "Bắt đầu OCR" để trích xuất chữ.
          </p>
        </div>
      </div>
    );
  }

  const confidencePercentage = result ? (result.average_confidence * 100).toFixed(1) : '0.0';
  const timeSeconds = result ? (result.processing_time_ms / 1000).toFixed(2) : '0.00';
  const lineCount = result ? result.line_count : playbackLines.length;

  const hasCccdData = docType === 'cccd' && cccdInfo;

  return (
    <div className="result-container">
      <div className="result-header">
        <div className="result-meta">
          <span className="meta-item">
            Dòng: <strong>{lineCount}</strong>
          </span>
          <span className="meta-item">
            Độ tin cậy: <strong>{confidencePercentage}%</strong>
          </span>
          <span className="meta-item">
            Thời gian: <strong>{timeSeconds}s</strong>
          </span>
        </div>
        <button 
          className="btn btn-secondary btn-action" 
          style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }} 
          onClick={onClear}
          disabled={isLoading || isPlaybackActive}
        >
          Xóa kết quả
        </button>
      </div>

      {/* Terminal Scan Progress Panel */}
      <div className="terminal-panel">
        <div className="terminal-header">
          <div className="terminal-actions">
            <span className="terminal-dot red"></span>
            <span className="terminal-dot yellow"></span>
            <span className="terminal-dot green"></span>
          </div>
          <div>DeepSeek-OCR Terminal Scanner v1.0.0</div>
          <div>{isPlaybackActive ? `SCANNING ${playbackProgress}%` : isLoading ? 'CONNECTING...' : 'COMPLETED'}</div>
        </div>
        
        <div className="terminal-body" ref={terminalBodyRef}>
          {/* Phase 1: Hiển thị log loading từ backend */}
          {isLoading && scanLogs.map((log, index) => (
            <div key={`log-${index}`} className="terminal-log-line">
              {log}
            </div>
          ))}
          
          {/* Phase 2: Hiển thị dòng chữ quét được */}
          {(result || isPlaybackActive) && playbackLines.map((line, index) => (
            <div key={`line-${index}`} className="terminal-scanned-line">
              [Line {index + 1}] {line}
            </div>
          ))}
          
          {isPlaybackActive && (
            <div className="terminal-active-scan">
              Đang phân tích dòng {playbackLines.length + 1}...
            </div>
          )}

          {!isPlaybackActive && result && (
            <div style={{ color: '#10b981', marginTop: '0.5rem', fontWeight: 600 }}>
              🎉 [HOÀN TẤT] Trích xuất thành công {result.line_count} dòng!
            </div>
          )}
        </div>
        
        {/* Thanh tiến trình */}
        {(isLoading || isPlaybackActive) && (
          <div className="progress-bar-container">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${isPlaybackActive ? playbackProgress : Math.min(scanLogs.length * 14, 98)}%` }}
            ></div>
          </div>
        )}
      </div>

      {/* Hiển thị form CCCD hoặc Textarea A4 */}
      {hasCccdData ? (
        <div className="cccd-form" style={{ opacity: isPlaybackActive ? 0.6 : 1 }}>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Số CCCD</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.card_number} 
              onChange={(e) => handleCccdFieldChange('card_number', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('card_number')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('card_number')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Họ tên</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.full_name} 
              onChange={(e) => handleCccdFieldChange('full_name', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('full_name')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('full_name')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Ngày sinh</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.dob} 
              onChange={(e) => handleCccdFieldChange('dob', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('dob')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('dob')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Giới tính</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.gender} 
              onChange={(e) => handleCccdFieldChange('gender', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('gender')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('gender')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Quốc tịch</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.nationality} 
              onChange={(e) => handleCccdFieldChange('nationality', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('nationality')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('nationality')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row">
            <label className="cccd-form-label">Quê quán</label>
            <input 
              type="text" 
              className="cccd-form-input" 
              value={cccdInfo.place_of_origin} 
              onChange={(e) => handleCccdFieldChange('place_of_origin', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              onMouseEnter={() => onActiveFieldChange('place_of_origin')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('place_of_origin')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
          <div className="cccd-form-row" style={{ alignItems: 'flex-start' }}>
            <label className="cccd-form-label" style={{ marginTop: '0.4rem' }}>Nơi thường trú</label>
            <textarea 
              className="cccd-form-input cccd-form-textarea" 
              value={cccdInfo.place_of_residence} 
              onChange={(e) => handleCccdFieldChange('place_of_residence', e.target.value)}
              disabled={isPlaybackActive || isLoading}
              rows={2}
              onMouseEnter={() => onActiveFieldChange('place_of_residence')}
              onMouseLeave={() => onActiveFieldChange(null)}
              onFocus={() => onActiveFieldChange('place_of_residence')}
              onBlur={() => onActiveFieldChange(null)}
            />
          </div>
        </div>
      ) : (
        <textarea
          className="result-textarea"
          value={editedText}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder={isPlaybackActive ? "Vui lòng đợi tiến trình quét hoàn tất..." : "Nội dung nhận dạng..."}
          disabled={isPlaybackActive || isLoading}
          spellCheck={false}
          style={{
            opacity: (isPlaybackActive || isLoading) ? 0.6 : 1,
            cursor: (isPlaybackActive || isLoading) ? 'not-allowed' : 'text',
            minHeight: '200px'
          }}
        />
      )}

      <div className="toolbar">
        <button 
          className="btn btn-secondary" 
          onClick={handleCopy} 
          disabled={isPlaybackActive || isLoading || (!editedText && !hasCccdData)}
        >
          <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          Sao chép
        </button>
        
        <button 
          className="btn btn-secondary" 
          onClick={handleDownload} 
          disabled={isPlaybackActive || isLoading || (!editedText && !hasCccdData)}
        >
          <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Tải TXT
        </button>
      </div>

      {showToast && (
        <div className="toast">
          <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Đã sao chép văn bản!
        </div>
      )}
    </div>
  );
}
