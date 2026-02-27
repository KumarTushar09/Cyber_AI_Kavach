// Global variables
let currentScanId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeUpload();
    loadStatistics();
    
    // Refresh stats every 30 seconds
    setInterval(loadStatistics, 30000);
});

// Initialize upload functionality
function initializeUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    // Drag and drop handlers
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // File input handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

// Handle file selection
function handleFile(file) {
    // Validate file
    if (!file.name.endsWith('.apk')) {
        showStatus('Only .apk files are allowed', 'error');
        return;
    }
    
    // Check file size (100MB max)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showStatus('File too large. Maximum size is 100MB', 'error');
        return;
    }
    
    // Display file info
    const fileInfo = document.getElementById('fileInfo');
    fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    
    // Upload file
    uploadFile(file);
}

// Upload file to server
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress bar
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    
    showStatus('Uploading and analyzing APK...', 'processing');
    
    try {
        // Simulate progress (since we can't track actual upload progress easily)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
                progressFill.textContent = progress + '%';
            }
        }, 200);
        
        // Upload
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressFill.textContent = '100%';
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        currentScanId = result.scan_id;
        
        showStatus('Analysis complete!', 'success');
        
        // Hide progress bar after a moment
        setTimeout(() => {
            progressBar.style.display = 'none';
        }, 1000);
        
        // Load and display results
        await loadResults(currentScanId);
        
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('Error: ' + error.message, 'error');
        progressBar.style.display = 'none';
    }
}

// Load analysis results
async function loadResults(scanId) {
    try {
        const response = await fetch(`/api/report/${scanId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load results');
        }
        
        const data = await response.json();
        displayResults(data);
        
        // Reload statistics
        loadStatistics();
        
    } catch (error) {
        console.error('Load results error:', error);
        showStatus('Error loading results: ' + error.message, 'error');
    }
}

// Display results
function displayResults(data) {
    // Show results section
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Overall risk
    document.getElementById('apkName').textContent = data.apk_name;
    document.getElementById('packageName').textContent = data.package_name || 'N/A';
    document.getElementById('scanId').textContent = data.scan_id;
    
    const riskScore = Math.round(data.overall.risk_score);
    const riskLevel = data.overall.risk_level;
    
    document.getElementById('riskScore').textContent = riskScore;
    document.getElementById('riskLevel').textContent = riskLevel.toUpperCase();
    document.getElementById('riskLevel').className = `risk-level risk-${riskLevel}`;
    document.getElementById('riskScore').className = `risk-score risk-${riskLevel}`;
    
    // ML Prediction
    const prediction = data.overall.ml_prediction;
    const predictionBadge = document.getElementById('mlPrediction');
    predictionBadge.textContent = prediction;
    predictionBadge.className = `badge ${prediction === 'Malware' ? 'badge-malware' : 'badge-benign'}`;
    
    document.getElementById('mlConfidence').textContent = 
        Math.round(data.overall.ml_confidence) + '%';
    
    // CIA Analysis
    displayCIAAnalysis(data.cia_analysis);
    
    // Feature counts
    document.getElementById('permCount').textContent = data.feature_counts.permissions;
    document.getElementById('apiCount').textContent = data.feature_counts.api_calls;
    document.getElementById('intentCount').textContent = data.feature_counts.intents;
    
    // Threat indicators
    displayThreats(data.threat_indicators);
    
    // Recommendations
    displayRecommendations(data.recommendations);
}

// Display CIA analysis
function displayCIAAnalysis(cia) {
    // Confidentiality
    updateCIAComponent('c', cia.confidentiality);
    
    // Integrity
    updateCIAComponent('i', cia.integrity);
    
    // Availability
    updateCIAComponent('a', cia.availability);
}

function updateCIAComponent(prefix, data) {
    const score = Math.round(data.score);
    const level = data.level;
    
    document.getElementById(`${prefix}Score`).textContent = score;
    document.getElementById(`${prefix}Level`).textContent = level.toUpperCase();
    document.getElementById(`${prefix}Level`).className = `cia-level risk-${level}`;
    document.getElementById(`${prefix}Desc`).textContent = data.description;
    
    const fill = document.getElementById(`cia${prefix === 'c' ? 'Confidentiality' : prefix === 'i' ? 'Integrity' : 'Availability'}`);
    fill.style.width = score + '%';
    fill.className = `cia-fill risk-${level}`;
    fill.style.backgroundColor = getRiskColor(level);
}

// Display threat indicators
function displayThreats(threats) {
    const threatList = document.getElementById('threatList');
    const threatsSection = document.getElementById('threatsSection');
    
    if (threats && threats.length > 0) {
        threatsSection.style.display = 'block';
        threatList.innerHTML = threats.map(threat => `<li>⚠️ ${threat}</li>`).join('');
    } else {
        threatsSection.style.display = 'none';
    }
}

// Display recommendations
function displayRecommendations(recommendations) {
    const recList = document.getElementById('recommendationList');
    
    if (recommendations && recommendations.length > 0) {
        recList.innerHTML = recommendations.map(rec => `<li>${rec}</li>`).join('');
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error('Failed to load statistics');
        }
        
        const stats = await response.json();
        displayStatistics(stats);
        
    } catch (error) {
        console.error('Load statistics error:', error);
    }
}

// Display statistics
function displayStatistics(stats) {
    document.getElementById('totalScans').textContent = stats.total_scans || 0;
    document.getElementById('malwareRate').textContent = 
        (stats.malware_rate || 0).toFixed(1) + '%';
    document.getElementById('avgRisk').textContent = 
        (stats.avg_risk_score || 0).toFixed(1);
    document.getElementById('avgTime').textContent = 
        (stats.avg_processing_time || 0).toFixed(1) + 's';
}

// Export report
async function exportReport() {
    if (!currentScanId) {
        alert('No scan results to export');
        return;
    }
    
    try {
        const response = await fetch(`/api/export/${currentScanId}`);
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const data = await response.json();
        const dataStr = JSON.stringify(data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `apk_analysis_${currentScanId}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showStatus('Report exported successfully', 'success');
        
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export report: ' + error.message);
    }
}

// Reset analysis
function resetAnalysis() {
    currentScanId = null;
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('fileInfo').textContent = '';
    document.getElementById('statusMessage').textContent = '';
    document.getElementById('fileInput').value = '';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Helper functions
function showStatus(message, type) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function getRiskColor(level) {
    const colors = {
        'safe': '#10b981',
        'low': '#3b82f6',
        'medium': '#f59e0b',
        'high': '#f97316',
        'critical': '#dc2626'
    };
    return colors[level] || '#64748b';
}
