"""
Database models for APK analysis system
Compatible with ShaktiDB structure
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ScanResult(Base):
    """Store APK scan results"""
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(64), unique=True, index=True, nullable=False)
    
    # APK metadata
    sha256 = Column(String(64), index=True)
    apk_name = Column(String(255))
    package_name = Column(String(255))
    file_size = Column(Integer)
    
    # ML prediction
    prediction = Column(Integer)  # 0=benign, 1=malware
    confidence = Column(Float)
    
    # Risk scores
    overall_risk_score = Column(Float)
    risk_level = Column(String(20))
    
    confidentiality_score = Column(Float)
    integrity_score = Column(Float)
    availability_score = Column(Float)
    
    # Feature counts
    permission_count = Column(Integer, default=0)
    api_call_count = Column(Integer, default=0)
    intent_count = Column(Integer, default=0)
    
    # Detailed data (stored as JSON for flexibility)
    permissions = Column(JSON)
    api_calls = Column(JSON)
    threat_indicators = Column(JSON)
    recommendations = Column(JSON)
    
    # Full report
    full_report = Column(JSON)
    
    # Metadata
    scan_date = Column(DateTime, default=func.now(), nullable=False)
    processing_time = Column(Float)  # seconds
    
    # Status
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ScanResult(scan_id='{self.scan_id}', risk_level='{self.risk_level}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'apk_name': self.apk_name,
            'package_name': self.package_name,
            'prediction': 'Malware' if self.prediction == 1 else 'Benign',
            'confidence': self.confidence,
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level,
            'cia_scores': {
                'confidentiality': self.confidentiality_score,
                'integrity': self.integrity_score,
                'availability': self.availability_score
            },
            'feature_counts': {
                'permissions': self.permission_count,
                'api_calls': self.api_call_count,
                'intents': self.intent_count
            },
            'threat_indicators': self.threat_indicators,
            'recommendations': self.recommendations,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            'processing_time': self.processing_time,
            'status': self.status
        }


class SystemStats(Base):
    """Store system statistics"""
    __tablename__ = 'system_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    
    total_scans = Column(Integer, default=0)
    malware_detected = Column(Integer, default=0)
    benign_detected = Column(Integer, default=0)
    
    avg_processing_time = Column(Float, default=0.0)
    avg_risk_score = Column(Float, default=0.0)
    
    # Risk level counts
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    safe_count = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'total_scans': self.total_scans,
            'malware_detected': self.malware_detected,
            'benign_detected': self.benign_detected,
            'malware_rate': round((self.malware_detected / self.total_scans * 100), 2) if self.total_scans > 0 else 0,
            'avg_processing_time': round(self.avg_processing_time, 2),
            'avg_risk_score': round(self.avg_risk_score, 2),
            'risk_distribution': {
                'critical': self.critical_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count,
                'safe': self.safe_count
            },
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class AuditLog(Base):
    """Audit log for tracking all activities"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    event_type = Column(String(50), index=True)  # upload, scan, download, error
    scan_id = Column(String(64), index=True, nullable=True)
    
    user_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    details = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', timestamp='{self.timestamp}')>"
