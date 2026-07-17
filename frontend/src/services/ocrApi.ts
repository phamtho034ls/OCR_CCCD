import axios from 'axios';
import { OCRResponse, UploadResponse } from '../types/ocr';

// Access API base url from Vite environment or fallback to default local port
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 600000, // 10 minutes timeout for processing large PDFs page by page
});


export async function uploadAndPreprocess(file: File, docType: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const endpoint = docType === 'cccd' ? '/ocr/cccd/upload' : '/ocr/a4/upload';
  const response = await api.post<UploadResponse>(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

export async function recognizePreprocessed(fileToken: string, docType: string): Promise<OCRResponse> {
  const formData = new FormData();
  formData.append('file_token', fileToken);

  const endpoint = docType === 'cccd' ? '/ocr/cccd/recognize' : '/ocr/a4/recognize';
  const response = await api.post<OCRResponse>(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

export async function checkHealth(): Promise<{ status: string; service: string; ocr_model: string; device: string }> {
  const response = await api.get('/health');
  return response.data;
}

