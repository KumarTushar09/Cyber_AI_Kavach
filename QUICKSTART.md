# Quick Start Guide

## Installation (5 minutes)

```powershell
# 1. Navigate to project
cd D:\Apk_analyzer

# 2. Run setup script
.\setup.ps1

# 3. Follow the prompts
```

## Or Manual Setup

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env
```

## Train Model (15-30 minutes)

```powershell
python ml\train_model.py
```

## Run Application

```powershell
python backend\app.py
```

Then open: http://localhost:8000

## Test the System

1. Download a sample APK or use any APK file
2. Upload through the web interface
3. View the analysis results
4. Check CIA risk scores
5. Review recommendations

## API Usage

```bash
# Upload APK
curl -X POST "http://localhost:8000/api/upload" -F "file=@test.apk"

# Get results
curl "http://localhost:8000/api/report/{scan_id}"

# Get statistics
curl "http://localhost:8000/api/stats"
```

## Project Features

✅ ML-based malware detection (100K+ samples)
✅ NIST CIA framework risk scoring
✅ 166 permissions + 24K API calls analysis
✅ Real-time web interface
✅ RESTful API
✅ Database logging (SQLite/ShaktiDB)
✅ Comprehensive reporting
✅ Export functionality

## Architecture

```
Upload APK → Feature Extraction → ML Model → Risk Scoring → Results
                                                ↓
                                           Database + Logs
```

## Risk Levels

- **CRITICAL** (80-100): Block immediately
- **HIGH** (60-79): Detailed review required
- **MEDIUM** (40-59): Proceed with caution
- **LOW** (20-39): Generally safe
- **SAFE** (0-19): No threats detected

## Troubleshooting

**Port already in use?**
```powershell
# Change PORT in .env file
PORT=8001
```

**Model not found?**
```powershell
# Train the model first
python ml\train_model.py
```

**Dependencies error?**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Need Help?

1. Check `SETUP.md` for detailed guide
2. View logs in `data/logs/app.log`
3. API docs: http://localhost:8000/docs

## Production Deployment

For production use with ShaktiDB:

1. Update `.env`:
   ```env
   DATABASE_URL=shaktidb://user:pass@host:port/db
   DEBUG=False
   SECRET_KEY=your-secure-secret-key
   ```

2. Use production server:
   ```powershell
   pip install gunicorn
   gunicorn backend.app:app --workers 4 --bind 0.0.0.0:8000
   ```

## License

MH-100K Dataset: CC BY 4.0
