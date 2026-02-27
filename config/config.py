"""
Configuration settings for APK Malware Detection System
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    APP_NAME: str = "APK Malware Detection System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    MODEL_DIR: Path = DATA_DIR / "models"
    LOG_DIR: Path = DATA_DIR / "logs"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./data/apk_analyzer.db"
    
    # ML Model Settings
    MODEL_PATH: Path = MODEL_DIR / "malware_detector.pkl"
    FEATURE_EXTRACTOR_PATH: Path = MODEL_DIR / "feature_extractor.pkl"
    SCALER_PATH: Path = MODEL_DIR / "scaler.pkl"
    
    # Upload Settings
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: str = ".apk"  # Changed to string for simpler config
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = LOG_DIR / "app.log"
    
    # Risk Scoring Thresholds (NIST CIA)
    RISK_CRITICAL_THRESHOLD: int = 80
    RISK_HIGH_THRESHOLD: int = 60
    RISK_MEDIUM_THRESHOLD: int = 40
    RISK_LOW_THRESHOLD: int = 20
    
    # Security
    SECRET_KEY: str = "changeme-in-production"
    API_KEY_ENABLED: bool = False
    
    # VirusTotal API (Optional)
    VT_API_KEY: Optional[str] = None
    
    # Dataset paths (for training)
    DATASET_PATH: Path = Path("C:/Users/Admin/Downloads/MH-100K-dataset/Malware-Hunter-MH-100K-dataset-1de7ca0/mh_100k_dataset.csv.part001/mh_100k_dataset.csv")
    FEATURES_ALL_PATH: Path = Path("C:/Users/Admin/Downloads/MH-100K-dataset/Malware-Hunter-MH-100K-dataset-1de7ca0/mh_100k_features_all.csv")
    FEATURES_CLASSES_PATH: Path = Path("C:/Users/Admin/Downloads/MH-100K-dataset/Malware-Hunter-MH-100K-dataset-1de7ca0/mh_100k_features_classes.csv")
    LABELS_PATH: Path = Path("C:/Users/Admin/Downloads/MH-100K-dataset/Malware-Hunter-MH-100K-dataset-1de7ca0/mh_100k_labels.csv")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.DATA_DIR, self.UPLOAD_DIR, self.MODEL_DIR, self.LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.create_directories()
