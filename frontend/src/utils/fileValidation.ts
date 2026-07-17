const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'pdf'];
const MAX_FILE_SIZE_MB = 100;

export function validateFile(file: File): string | null {
  if (!file) {
    return 'Vui lòng chọn một file ảnh hoặc tài liệu PDF.';
  }

  const extension = file.name.split('.').pop()?.toLowerCase();
  if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
    return `Định dạng file không được hỗ trợ. Chỉ nhận các định dạng: ${ALLOWED_EXTENSIONS.join(', ').toUpperCase()}.`;
  }

  const fileSizeMB = file.size / (1024 * 1024);
  if (fileSizeMB > MAX_FILE_SIZE_MB) {
    return `Dung lượng file vượt quá giới hạn cho phép (${MAX_FILE_SIZE_MB}MB). Vui lòng chọn tệp khác.`;
  }

  return null;
}
