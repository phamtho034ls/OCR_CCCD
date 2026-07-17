export interface OCRLine {
  index: number;
  text: string;
  confidence: number;
  box: number[][];
}

export interface CCCDInfo {
  card_number: string;
  full_name: string;
  dob: string;
  gender: string;
  nationality: string;
  place_of_origin: string;
  place_of_residence: string;
}

export interface CCCDBoxes {
  card_number?: number[][];
  full_name?: number[][];
  dob?: number[][];
  gender?: number[][];
  nationality?: number[][];
  place_of_origin?: number[][];
  place_of_residence?: number[][];
}

export interface OCRResponse {
  success: boolean;
  file_name: string;
  processing_time_ms: number;
  full_text: string;
  line_count: number;
  average_confidence: number;
  lines: OCRLine[];
  processed_image?: string;
  cccd_info?: CCCDInfo;
  cccd_boxes?: CCCDBoxes;
}

export interface APIErrorResponse {
  success: false;
  error_code: string;
  message: string;
}

export interface UploadResponse {
  success: boolean;
  file_token: string;
  file_name: string;
  processed_image?: string;
  warped_successfully: boolean;
}

