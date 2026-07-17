import { useEffect, useState } from 'react';
import { checkHealth } from '../services/ocrApi';

export default function Header() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [device, setDevice] = useState<string>('');

  useEffect(() => {
    checkHealth()
      .then((data) => {
        if (data.status === 'ok') {
          setBackendStatus('connected');
          setDevice(data.device.toUpperCase());
        } else {
          setBackendStatus('error');
        }
      })
      .catch(() => {
        setBackendStatus('error');
      });
  }, []);

  return (
    <header className="header">
      <h1>OCR tài liệu bằng PP-OCRv6</h1>
      <p>Chuyển đổi tài liệu dạng ảnh thành văn bản thuần chạy 100% offline trên máy tính</p>
      
      <div style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: '0.5rem', 
        marginTop: '0.75rem', 
        fontSize: '0.8rem', 
        padding: '0.35rem 0.75rem', 
        borderRadius: '50px', 
        background: 'rgba(255, 255, 255, 0.7)', 
        border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: backendStatus === 'connected' ? 'var(--success-color)' : backendStatus === 'checking' ? 'var(--warning-color)' : 'var(--danger-color)',
          display: 'inline-block'
        }} />
        <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>
          {backendStatus === 'connected' 
            ? `Cổng Backend: Connected (${device})` 
            : backendStatus === 'checking' 
              ? 'Đang kiểm tra kết nối Backend...' 
              : 'Mất kết nối Backend (Vui lòng chạy `python run.py`)'}
        </span>
      </div>
    </header>
  );
}
