export function downloadText(text: string, originalFileName: string): void {
  // Extracts the filename without its extension
  const baseName = originalFileName.substring(0, originalFileName.lastIndexOf('.')) || originalFileName;
  const fileName = `${baseName}_ocr.txt`;
  
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  
  // Clean up references in DOM
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
