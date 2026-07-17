import { useRef, useState, DragEvent, ChangeEvent } from 'react';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  docType: string;
}

export default function UploadZone({ onFileSelect, docType }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  return (
    <div className="upload-section">
      <input
        ref={inputRef}
        type="file"
        style={{ display: 'none' }}
        accept=".jpg,.jpeg,.png,.bmp,.tiff,.webp,.pdf"
        onChange={handleChange}
      />

      <div 
        className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        style={{ minHeight: '220px' }}
      >
        <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p>
          {docType === 'cccd' 
            ? 'Kéo thả ảnh CCCD vào đây hoặc nhấp để chọn ảnh'
            : 'Kéo thả ảnh hoặc tài liệu PDF vào đây hoặc nhấp để chọn'
          }
        </p>
        <span>Hỗ trợ ảnh (JPG, PNG, WEBP...) {docType !== 'cccd' && 'và PDF (Tối đa 100MB)'}</span>
      </div>
    </div>
  );
}
