import { useState } from 'react';
import Header from '../components/Header';
import ErrorMessage from '../components/ErrorMessage';
import UploadZone from '../components/UploadZone';
import ImagePreview from '../components/ImagePreview';
import OCRResult from '../components/OCRResult';
import { useOCR } from '../hooks/useOCR';

export default function OCRPage() {
  const {
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
    docType,
    setDocType,
    cccdInfo,
    setCccdInfo,
  } = useOCR();

  const [activeField, setActiveField] = useState<string | null>(null);

  return (
    <div className="app-container">
      <Header />
      
      <ErrorMessage message={error || ''} />

      <main className="main-grid">
        {/* Left Side: Upload or Image Preview */}
        <div className="glass-card">
          <h2 className="card-title">
            <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {docType === 'cccd' ? 'Ảnh CCCD' : 'Ảnh Giấy A4'}
          </h2>

          {/* Bộ chọn định dạng xử lý: Giấy A4 vs Thẻ CCCD */}
          <div className="doc-type-selector">
            <button
              className={`doc-type-tab ${docType === 'a4' ? 'active' : ''}`}
              onClick={() => !isLoading && !isPlaybackActive && setDocType('a4')}
              disabled={isLoading || isPlaybackActive}
            >
              <svg style={{ width: '16px', height: '16px', marginRight: '6px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Giấy tờ A4 (Nhà đất, Văn bản)
            </button>
            <button
              className={`doc-type-tab ${docType === 'cccd' ? 'active' : ''}`}
              onClick={() => !isLoading && !isPlaybackActive && setDocType('cccd')}
              disabled={isLoading || isPlaybackActive}
            >
              <svg style={{ width: '16px', height: '16px', marginRight: '6px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Căn cước công dân (Thẻ CCCD)
            </button>
          </div>
          
          {!file ? (
            <UploadZone onFileSelect={selectFile} docType={docType} />
          ) : (
            previewUrl && (
              <ImagePreview
                file={file}
                previewUrl={previewUrl}
                onClear={clearFile}
                onRunOCR={runOCR}
                isLoading={isLoading}
                isPlaybackActive={isPlaybackActive}
                hasResult={!!ocrResult}
                ocrResult={ocrResult}
                playbackLinesCount={playbackLines.length}
                activeField={activeField}
                docType={docType}
              />
            )
          )}
        </div>

        {/* Right Side: OCR Text Output */}
        <div className="glass-card">
          <h2 className="card-title">
            <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Văn bản trích xuất
          </h2>
          
          <OCRResult
            result={ocrResult}
            editedText={editedText}
            onTextChange={setEditedText}
            onClear={resetOCR}
            isLoading={isLoading}
            scanLogs={scanLogs}
            playbackLines={playbackLines}
            isPlaybackActive={isPlaybackActive}
            playbackProgress={playbackProgress}
            docType={docType}
            cccdInfo={cccdInfo}
            onCccdInfoChange={setCccdInfo}
            activeField={activeField}
            onActiveFieldChange={setActiveField}
          />
        </div>
      </main>
    </div>
  );
}
