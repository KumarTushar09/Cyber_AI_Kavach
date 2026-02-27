# APK Malware Detection System

A comprehensive machine learning-based Android APK malware detection system with risk scoring based on NIST CIA framework.

## Architecture

```
[ User Interface ] 
        ↓ 
[ Backend API Server ] 
        ↓ 
[ Feature Extraction Module ] 
        ↓ 
[ ML Model Service ] 
        ↓ 
[ Risk Scoring Engine ] 
        ↓ 
[ Database + Logging ] 
```

## Features

- **ML-Based Detection**: Trained on MH-100K dataset with 100K+ samples
- **Feature Extraction**: Extracts 166 permissions, 24K+ API calls, 250 intents
- **Risk Scoring**: NIST-based CIA (Confidentiality, Integrity, Availability) scoring
- **Multi-Criteria Analysis**: 4-5 detection criteria with detailed metrics
- **Database Ready**: Compatible with ShaktiDB (using SQLite for development)

## Project Structure

```
apk_analyzer/
├── backend/
│   ├── api/              # FastAPI REST endpoints
│   ├── models/           # ML models and database models
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── ml/
│   ├── train_model.py    # Model training script
│   ├── feature_extractor.py  # APK feature extraction
│   └── risk_scorer.py    # NIST CIA risk scoring
├── frontend/
│   ├── static/           # CSS, JS files
│   └── templates/        # HTML templates
├── data/
│   ├── models/           # Trained ML models
│   └── logs/             # Application logs
├── config/
│   └── config.py         # Configuration settings
└── requirements.txt
```

## Installation

1. **Clone the repository**
```bash
cd D:\Apk_analyzer
```

2. **Create virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Prepare the dataset**
- Extract `mh_100k_dataset.csv` from the provided archives
- Place in `data/` directory

5. **Train the model**
```powershell
python ml/train_model.py
```

6. **Run the application**
```powershell
python backend/app.py
```

7. **Access the application**
Open browser: `http://localhost:8000`

## Usage

1. Upload an APK file through the web interface
2. System extracts features automatically
3. ML model analyzes the APK
4. Risk score calculated based on NIST CIA framework
5. Results displayed with detailed metrics

## Risk Scoring (NIST CIA Framework)

### Confidentiality (C)
- Data leakage permissions
- Network access patterns
- Encryption usage

### Integrity (I)
- System modification capabilities
- Code injection patterns
- Package tampering indicators

### Availability (A)
- Resource consumption patterns
- DoS potential
- Service disruption capabilities

### Overall Risk Levels
- **Critical** (80-100): Immediate threat, block recommended
- **High** (60-79): Significant risk, detailed review needed
- **Medium** (40-59): Moderate risk, monitor carefully
- **Low** (20-39): Minor concerns, generally safe
- **Safe** (0-19): No significant threats detected

## Database

- **Development**: SQLite
- **Production**: ShaktiDB (structure compatible)

## Technologies

- **Backend**: FastAPI (Python 3.8+)
- **ML**: scikit-learn, XGBoost
- **APK Analysis**: Androguard
- **Frontend**: HTML5, JavaScript, Bootstrap
- **Database**: SQLite/ShaktiDB

## API Endpoints

- `POST /api/upload` - Upload APK for analysis
- `GET /api/report/{scan_id}` - Get analysis report
- `GET /api/history` - Get scan history
- `GET /api/stats` - Get system statistics

## License

CC BY 4.0 - Dataset from MH-100K

## Credits

Dataset: MH-100K by Malware Hunter Research Team
