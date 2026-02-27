"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class RiskLevelEnum(str, Enum):
    """Risk level enumeration"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CIAScores(BaseModel):
    """CIA Triad scores"""
    confidentiality: float = Field(..., ge=0, le=100)
    integrity: float = Field(..., ge=0, le=100)
    availability: float = Field(..., ge=0, le=100)


class CIAComponent(BaseModel):
    """Detailed CIA component analysis"""
    score: float
    level: RiskLevelEnum
    description: str


class CIAAnalysis(BaseModel):
    """Complete CIA analysis"""
    confidentiality: CIAComponent
    integrity: CIAComponent
    availability: CIAComponent


class OverallRisk(BaseModel):
    """Overall risk assessment"""
    risk_score: float
    risk_level: RiskLevelEnum
    ml_prediction: str
    ml_confidence: float


class FeatureCounts(BaseModel):
    """Feature count summary"""
    permissions: int
    api_calls: int
    intents: int


class ScanResponse(BaseModel):
    """Scan result response"""
    scan_id: str
    apk_name: str
    package_name: Optional[str]
    overall: OverallRisk
    cia_analysis: CIAAnalysis
    feature_counts: FeatureCounts
    threat_indicators: List[str]
    recommendations: List[str]
    scan_date: datetime
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "abc123...",
                "apk_name": "example.apk",
                "package_name": "com.example.app",
                "overall": {
                    "risk_score": 75.5,
                    "risk_level": "high",
                    "ml_prediction": "Malware",
                    "ml_confidence": 0.85
                },
                "cia_analysis": {
                    "confidentiality": {
                        "score": 80.0,
                        "level": "high",
                        "description": "Significant privacy risks detected"
                    }
                },
                "feature_counts": {
                    "permissions": 15,
                    "api_calls": 200,
                    "intents": 5
                },
                "threat_indicators": ["Suspicious permission combination"],
                "recommendations": ["Do not install"],
                "scan_date": "2024-01-01T12:00:00",
                "processing_time": 5.2
            }
        }


class UploadResponse(BaseModel):
    """Upload response"""
    message: str
    scan_id: str
    status: str


class StatsResponse(BaseModel):
    """System statistics response"""
    total_scans: int
    malware_detected: int
    benign_detected: int
    malware_rate: float
    avg_processing_time: float
    avg_risk_score: float
    risk_distribution: Dict[str, int]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
