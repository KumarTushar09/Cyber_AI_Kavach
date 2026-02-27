# APK Malware Detection System - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### 2. Installation Steps

```powershell
# Navigate to project directory
cd D:\Apk_analyzer

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```powershell
# Copy environment template
copy .env.example .env

# Edit .env file with your settings (optional for basic usage)
notepad .env
```

### 4. Prepare Dataset

Extract the MH-100K dataset CSV file:
```powershell
# If you have the compressed parts
cd "C:\Users\Admin\Downloads\MH-100K-dataset\Malware-Hunter-MH-100K-dataset-1de7ca0"

# Extract using 7-Zip or WinRAR
# The file should be at: mh_100k_dataset.csv.part001\mh_100k_dataset.csv
```

### 5. Train the Model

```powershell
# From project root
python ml\train_model.py
```

Expected output:
- Training progress with cross-validation scores
- Model evaluation metrics
- Saved model files in `data/models/`

Training time: ~10-30 minutes depending on your system

### 6. Run the Application

```powershell
# Start the backend server
python backend\app.py
```

The application will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Directory Structure

```
Apk_analyzer/
├── backend/                 # Backend API server
│   ├── api/                # (Future: API route modules)
│   ├── models/             # Database and Pydantic models
│   ├── services/           # Business logic services
│   └── app.py              # Main FastAPI application
├── ml/                      # Machine Learning components
│   ├── train_model.py      # Model training script
│   ├── feature_extractor.py # APK feature extraction
│   └── risk_scorer.py      # NIST CIA risk scoring
├── frontend/                # Web interface
│   ├── static/             # CSS and JavaScript
│   └── templates/          # HTML templates
├── config/                  # Configuration
│   └── config.py           # Settings management
├── data/                    # Data directory (created at runtime)
│   ├── models/             # Trained ML models
│   ├── uploads/            # Uploaded APK files
│   └── logs/               # Application logs
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
└── README.md               # Main documentation
```

## Usage Guide

### Web Interface

1. **Open Browser**: Navigate to `http://localhost:8000`

2. **Upload APK**: 
   - Drag and drop an APK file
   - Or click "Choose File" to browse

3. **View Results**:
   - Overall risk assessment
   - NIST CIA framework analysis
   - Threat indicators
   - Security recommendations

4. **Export Report**: Download detailed JSON report

### API Endpoints

#### Upload APK for Analysis
```bash
POST /api/upload
Content-Type: multipart/form-data

Response:
{
  "message": "APK analyzed successfully",
  "scan_id": "abc123...",
  "status": "completed"
}
```

#### Get Analysis Report
```bash
GET /api/report/{scan_id}

Response:
{
  "scan_id": "abc123...",
  "apk_name": "example.apk",
  "overall": {
    "risk_score": 75.5,
    "risk_level": "high",
    "ml_prediction": "Malware",
    "ml_confidence": 85.2
  },
  "cia_analysis": { ... },
  "recommendations": [ ... ]
}
```

#### Get System Statistics
```bash
GET /api/stats

Response:
{
  "total_scans": 100,
  "malware_detected": 25,
  "malware_rate": 25.0,
  "avg_risk_score": 45.3
}
```

#### Get Scan History
```bash
GET /api/history?skip=0&limit=20

Response:
{
  "total": 20,
  "results": [ ... ]
}
```

## NIST CIA Risk Framework

### Confidentiality (C)
Measures potential for data privacy breaches:
- Permission analysis (contacts, location, SMS, etc.)
- Data access patterns
- Network communication capabilities

### Integrity (I)
Measures potential for system/data modification:
- File system access
- Package installation capabilities
- System settings modification
- Code injection patterns

### Availability (A)
Measures potential for service disruption:
- Resource consumption (wake locks, etc.)
- Background process control
- System reboot/shutdown capabilities

### Risk Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| SAFE | 0-19 | No significant threats detected |
| LOW | 20-39 | Minor concerns, generally safe |
| MEDIUM | 40-59 | Moderate risk, monitor carefully |
| HIGH | 60-79 | Significant risk, detailed review needed |
| CRITICAL | 80-100 | Immediate threat, block recommended |

## Troubleshooting

### Model Training Issues

**Problem**: Dataset file not found
```
Solution: Ensure the CSV file is extracted and the path in config.py is correct
```

**Problem**: Out of memory error
```
Solution: Reduce training data size or increase system RAM
```

### Runtime Issues

**Problem**: Androguard import error
```
Solution: pip install androguard==3.4.0a1
```

**Problem**: Port 8000 already in use
```
Solution: Change PORT in .env file or kill the process using port 8000
```

### Database Issues

**Problem**: Database locked error
```
Solution: Close any other connections to the database or delete the .db file and restart
```

## Production Deployment

### Using ShaktiDB

1. Update `.env` file:
```env
DATABASE_URL=shaktidb://username:password@host:port/database
```

2. Update `config\config.py` if needed for ShaktiDB-specific settings

3. Run database migrations (if using Alembic):
```powershell
alembic upgrade head
```

### Security Considerations

1. **Change SECRET_KEY** in production
2. **Enable API_KEY_ENABLED** for authentication
3. **Set DEBUG=False** in production
4. **Use HTTPS** for production deployment
5. **Implement rate limiting** for API endpoints
6. **Regular backup** of database

### Performance Optimization

1. **Use production WSGI server** (Gunicorn/uWSGI)
2. **Enable caching** for frequent queries
3. **Optimize model** (pruning, quantization)
4. **Use CDN** for static files
5. **Implement async processing** for large APKs

## Testing

### Manual Testing
```powershell
# Download a test APK
# Upload through web interface
# Verify results and metrics
```

### API Testing
```powershell
# Using curl or Postman
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@path/to/test.apk"
```

## Support

For issues or questions:
1. Check the logs in `data/logs/app.log`
2. Review API documentation at `/docs`
3. Consult the main README.md

## License

This project uses the MH-100K dataset under CC BY 4.0 license.
