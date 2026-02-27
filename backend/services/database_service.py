"""
Database service for managing database connections and operations
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import settings
from backend.models.database import Base, ScanResult, SystemStats, AuditLog


class DatabaseService:
    """Manage database connections and operations"""
    
    def __init__(self):
        """Initialize database connection"""
        # Create engine
        # For SQLite, use check_same_thread=False and StaticPool
        # For ShaktiDB in production, adjust connection parameters
        if settings.DATABASE_URL.startswith('sqlite'):
            self.engine = create_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.DEBUG
            )
        else:
            # For ShaktiDB or other databases
            self.engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        self.create_tables()
        
        # Initialize system stats
        self.initialize_stats()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created successfully")
    
    def initialize_stats(self):
        """Initialize system statistics if not exists"""
        with self.get_session() as db:
            stats = db.query(SystemStats).first()
            if not stats:
                stats = SystemStats()
                db.add(stats)
                db.commit()
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_db(self):
        """Dependency for FastAPI"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # ScanResult operations
    def create_scan_result(self, db: Session, scan_data: dict) -> ScanResult:
        """Create a new scan result"""
        scan = ScanResult(**scan_data)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan
    
    def get_scan_result(self, db: Session, scan_id: str) -> ScanResult:
        """Get scan result by scan_id"""
        return db.query(ScanResult).filter(ScanResult.scan_id == scan_id).first()
    
    def get_all_scans(self, db: Session, skip: int = 0, limit: int = 100):
        """Get all scan results with pagination"""
        return db.query(ScanResult).order_by(ScanResult.scan_date.desc()).offset(skip).limit(limit).all()
    
    def update_scan_result(self, db: Session, scan_id: str, update_data: dict):
        """Update scan result"""
        scan = self.get_scan_result(db, scan_id)
        if scan:
            for key, value in update_data.items():
                setattr(scan, key, value)
            db.commit()
            db.refresh(scan)
        return scan
    
    # SystemStats operations
    def get_stats(self, db: Session) -> SystemStats:
        """Get system statistics"""
        return db.query(SystemStats).first()
    
    def update_stats(self, db: Session, scan_result: ScanResult):
        """Update system statistics after a scan"""
        stats = self.get_stats(db)
        if not stats:
            stats = SystemStats()
            db.add(stats)
        
        # Update counts
        stats.total_scans += 1
        if scan_result.prediction == 1:
            stats.malware_detected += 1
        else:
            stats.benign_detected += 1
        
        # Update risk level counts
        risk_level = scan_result.risk_level
        if risk_level == 'critical':
            stats.critical_count += 1
        elif risk_level == 'high':
            stats.high_count += 1
        elif risk_level == 'medium':
            stats.medium_count += 1
        elif risk_level == 'low':
            stats.low_count += 1
        else:
            stats.safe_count += 1
        
        # Update averages
        if stats.total_scans > 0:
            # Rolling average for processing time
            stats.avg_processing_time = (
                (stats.avg_processing_time * (stats.total_scans - 1) + scan_result.processing_time) 
                / stats.total_scans
            )
            # Rolling average for risk score
            stats.avg_risk_score = (
                (stats.avg_risk_score * (stats.total_scans - 1) + scan_result.overall_risk_score) 
                / stats.total_scans
            )
        
        db.commit()
        db.refresh(stats)
        return stats
    
    # AuditLog operations
    def create_audit_log(self, db: Session, event_type: str, scan_id: str = None, 
                        user_ip: str = None, user_agent: str = None, details: dict = None):
        """Create an audit log entry"""
        log = AuditLog(
            event_type=event_type,
            scan_id=scan_id,
            user_ip=user_ip,
            user_agent=user_agent,
            details=details
        )
        db.add(log)
        db.commit()
        return log


# Global database service instance
db_service = DatabaseService()
