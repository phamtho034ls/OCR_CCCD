interface LoadingOverlayProps {
  message?: string;
  submessage?: string;
}

export default function LoadingOverlay({ 
  message = "Đang nhận dạng văn bản...", 
  submessage = "Quá trình này chạy hoàn toàn cục bộ trên máy tính" 
}: LoadingOverlayProps) {
  return (
    <div className="loading-overlay">
      <div className="spinner"></div>
      <div className="loading-text">{message}</div>
      {submessage && <div className="loading-subtext">{submessage}</div>}
    </div>
  );
}
