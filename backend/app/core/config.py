from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Local OCR API"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    OCR_DEVICE: str = "cuda"
    OCR_ENGINE: str = "deepseek"
    OCR_MODEL_ID: str = "deepseek-ai/DeepSeek-OCR"
    OCR_PROMPT: str = "<image>\n<|grounding|>Convert the document to markdown."
    OCR_BASE_SIZE: int = 1024
    OCR_IMAGE_SIZE: int = 640
    OCR_CROP_MODE: bool = True
    ENABLE_IMAGE_PREPROCESSING: bool = True
    MAX_FILE_SIZE_MB: int = 100
    MAX_PDF_PAGES: int = 100
    MAX_IMAGE_WIDTH: int = 4000
    MAX_IMAGE_HEIGHT: int = 4000
    
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
