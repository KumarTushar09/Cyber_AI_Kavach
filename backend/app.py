"""
FastAPI Backend Application
Main entry point for the APK Malware Detection API
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import sys
from typing import List
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config.config import settings
from backend.models.schemas import ScanResponse, UploadResponse, StatsResponse, ErrorResponse
from backend.services import db_service, analysis_service
from loguru import logger

# Configure logger
logger.add(
    settings.LOG_FILE,
    rotation="10 MB",
    retention="30 days",
    level=settings.LOG_LEVEL
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ML-based Android APK malware detection with NIST CIA risk scoring"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Model path: {settings.MODEL_PATH}")
    
    # Ensure directories exist
    settings.create_directories()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    html_file = frontend_path / "templates" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse(content="""
            <html>
                <head><title>APK Malware Detection</title></head>
                <body>
                    <h1>APK Malware Detection System</h1>
                    <p>API is running. Frontend not found.</p>
                    <p>API Documentation: <a href="/docs">/docs</a></p>
                </body>
            </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "model_loaded": analysis_service.model is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/upload", response_model=UploadResponse)
async def upload_apk(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(db_service.get_db)
):
    """
    Upload an APK file for analysis
    
    - **file**: APK file to analyze (max 100MB)
    """
    try:
        # Log upload
        logger.info(f"Upload request from {request.client.host}: {file.filename}")
        
        # Validate file extension
        allowed_extensions = [settings.ALLOWED_EXTENSIONS] if isinstance(settings.ALLOWED_EXTENSIONS, str) else settings.ALLOWED_EXTENSIONS
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"Only {', '.join(allowed_extensions)} files are allowed")
        
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
            )
        
        # Save file temporarily
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved: {file_path}")
        
        # Create initial scan record
        scan_id = analysis_service.generate_scan_id(str(file_path))
        scan_data = {
            'scan_id': scan_id,
            'apk_name': file.filename,
            'file_size': len(file_content),
            'status': 'processing'
        }
        scan_record = db_service.create_scan_result(db, scan_data)
        
        # Create audit log
        db_service.create_audit_log(
            db,
            event_type='upload',
            scan_id=scan_id,
            user_ip=request.client.host,
            user_agent=request.headers.get('user-agent'),
            details={'filename': file.filename, 'size': len(file_content)}
        )
        
        # Perform analysis
        logger.info(f"Starting analysis for scan_id: {scan_id}")
        results = analysis_service.analyze_apk(str(file_path))
        
        # Update scan record with results
        db_service.update_scan_result(db, scan_id, results)
        
        # Update system stats
        updated_scan = db_service.get_scan_result(db, scan_id)
        db_service.update_stats(db, updated_scan)
        
        # Create audit log for completion
        db_service.create_audit_log(
            db,
            event_type='scan_completed',
            scan_id=scan_id,
            details={
                'prediction': results.get('prediction'),
                'risk_level': results.get('risk_level')
            }
        )
        
        logger.info(f"Analysis completed for scan_id: {scan_id}")
        
        # Clean up uploaded file (optional - uncomment to delete)
        # file_path.unlink()
        
        return UploadResponse(
            message="APK analyzed successfully",
            scan_id=scan_id,
            status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/api/report/{scan_id}", response_model=ScanResponse)
async def get_report(scan_id: str, db: Session = Depends(db_service.get_db)):
    """
    Get analysis report by scan ID
    
    - **scan_id**: Unique scan identifier
    """
    try:
        scan = db_service.get_scan_result(db, scan_id)
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if scan.status == 'failed':
            raise HTTPException(status_code=500, detail=f"Scan failed: {scan.error_message}")
        
        # Convert to response format
        response = {
            'scan_id': scan.scan_id,
            'apk_name': scan.apk_name,
            'package_name': scan.package_name,
            'overall': {
                'risk_score': scan.overall_risk_score,
                'risk_level': scan.risk_level,
                'ml_prediction': 'Malware' if scan.prediction == 1 else 'Benign',
                'ml_confidence': scan.confidence * 100 if scan.confidence else 0
            },
            'cia_analysis': scan.full_report.get('cia_analysis', {}) if scan.full_report else {},
            'feature_counts': {
                'permissions': scan.permission_count,
                'api_calls': scan.api_call_count,
                'intents': scan.intent_count
            },
            'threat_indicators': scan.threat_indicators or [],
            'recommendations': scan.recommendations or [],
            'scan_date': scan.scan_date,
            'processing_time': scan.processing_time
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(skip: int = 0, limit: int = 20, db: Session = Depends(db_service.get_db)):
    """
    Get scan history with pagination
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 20, max: 100)
    """
    try:
        if limit > 100:
            limit = 100
        
        scans = db_service.get_all_scans(db, skip=skip, limit=limit)
        
        history = []
        for scan in scans:
            history.append({
                'scan_id': scan.scan_id,
                'apk_name': scan.apk_name,
                'package_name': scan.package_name,
                'prediction': 'Malware' if scan.prediction == 1 else 'Benign',
                'risk_level': scan.risk_level,
                'risk_score': scan.overall_risk_score,
                'scan_date': scan.scan_date.isoformat() if scan.scan_date else None,
                'status': scan.status
            })
        
        return {
            'total': len(history),
            'skip': skip,
            'limit': limit,
            'results': history
        }
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(db_service.get_db)):
    """
    Get system statistics
    
    Returns overall statistics about scanned APKs
    """
    try:
        stats = db_service.get_stats(db)
        
        if not stats:
            return StatsResponse(
                total_scans=0,
                malware_detected=0,
                benign_detected=0,
                malware_rate=0.0,
                avg_processing_time=0.0,
                avg_risk_score=0.0,
                risk_distribution={'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'safe': 0}
            )
        
        return stats.to_dict()
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{scan_id}")
async def export_report(scan_id: str, db: Session = Depends(db_service.get_db)):
    """
    Export detailed report as JSON
    
    - **scan_id**: Unique scan identifier
    """
    try:
        scan = db_service.get_scan_result(db, scan_id)
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return JSONResponse(content=scan.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
