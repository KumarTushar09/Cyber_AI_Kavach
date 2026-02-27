# APK Malware Detection System - Setup Script
# Run this script to set up the project

Write-Host "=" * 60
Write-Host "APK Malware Detection System - Setup" -ForegroundColor Cyan
Write-Host "=" * 60

# Check Python version
Write-Host "`nChecking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Gray
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Virtual environment created successfully!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
Write-Host "`nSetting up configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file from template" -ForegroundColor Green
    Write-Host "You can edit .env to customize settings (optional)" -ForegroundColor Gray
} else {
    Write-Host ".env file already exists. Skipping..." -ForegroundColor Gray
}

# Create necessary directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
$directories = @("data", "data\models", "data\uploads", "data\logs")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

# Check for dataset
Write-Host "`nChecking for dataset..." -ForegroundColor Yellow
$datasetPath = "C:\Users\Admin\Downloads\MH-100K-dataset\Malware-Hunter-MH-100K-dataset-1de7ca0\mh_100k_dataset.csv.part001\mh_100k_dataset.csv"
if (Test-Path $datasetPath) {
    Write-Host "Dataset found at: $datasetPath" -ForegroundColor Green
    $trainNow = Read-Host "`nDo you want to train the model now? This will take 10-30 minutes (y/n)"
    if ($trainNow -eq 'y' -or $trainNow -eq 'Y') {
        Write-Host "`nStarting model training..." -ForegroundColor Yellow
        python ml\train_model.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nModel trained successfully!" -ForegroundColor Green
        } else {
            Write-Host "`nWARNING: Model training failed or was incomplete" -ForegroundColor Red
        }
    } else {
        Write-Host "`nSkipping model training. You can train later with: python ml\train_model.py" -ForegroundColor Gray
    }
} else {
    Write-Host "Dataset not found at expected location" -ForegroundColor Red
    Write-Host "Please extract the MH-100K dataset and ensure the path is correct" -ForegroundColor Yellow
    Write-Host "Expected path: $datasetPath" -ForegroundColor Gray
}

# Setup complete
Write-Host "`n" + ("=" * 60)
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 60)

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Ensure the ML model is trained (if not done above):" -ForegroundColor White
Write-Host "   python ml\train_model.py" -ForegroundColor Gray
Write-Host "`n2. Start the application:" -ForegroundColor White
Write-Host "   python backend\app.py" -ForegroundColor Gray
Write-Host "`n3. Open your browser:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Gray
Write-Host "`n4. API Documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray

Write-Host "`nFor detailed information, see SETUP.md" -ForegroundColor Yellow
Write-Host ""
