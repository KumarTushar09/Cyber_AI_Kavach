"""
Analysis service for coordinating APK analysis
"""
import joblib
import hashlib
import time
from pathlib import Path
from typing import Dict, Tuple
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import settings
from ml.feature_extractor import APKFeatureExtractor
from ml.risk_scorer import NISTRiskScorer


class AnalysisService:
    """Coordinate APK analysis using ML model and risk scoring"""
    
    def __init__(self):
        """Initialize the analysis service"""
        self.model = None
        self.scaler = None
        self.feature_extractor = None
        self.risk_scorer = NISTRiskScorer()
        self.load_model()
    
    def load_model(self):
        """Load trained ML model and components"""
        try:
            # Load model
            if settings.MODEL_PATH.exists():
                self.model = joblib.load(settings.MODEL_PATH)
                print(f"Model loaded from {settings.MODEL_PATH}")
            else:
                print(f"Warning: Model not found at {settings.MODEL_PATH}")
                print("Please train the model first using: python ml/train_model.py")
            
            # Load scaler
            if settings.SCALER_PATH.exists():
                self.scaler = joblib.load(settings.SCALER_PATH)
                print(f"Scaler loaded from {settings.SCALER_PATH}")
            
            # Load feature info
            if settings.FEATURE_EXTRACTOR_PATH.exists():
                feature_info = joblib.load(settings.FEATURE_EXTRACTOR_PATH)
                feature_names = feature_info.get('feature_names', [])
                
                # Initialize feature extractor with expected features
                features_path = str(settings.FEATURES_ALL_PATH)
                self.feature_extractor = APKFeatureExtractor(features_path)
                print(f"Feature extractor initialized with {len(feature_names)} features")
            else:
                self.feature_extractor = APKFeatureExtractor()
                print("Feature extractor initialized (without feature list)")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            self.feature_extractor = APKFeatureExtractor()
    
    def generate_scan_id(self, apk_path: str) -> str:
        """Generate unique scan ID based on file hash and timestamp"""
        with open(apk_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        timestamp = str(int(time.time()))
        scan_id = hashlib.sha256(f"{file_hash}{timestamp}".encode()).hexdigest()[:16]
        return scan_id
    
    def analyze_apk(self, apk_path: str) -> Dict:
        """
        Perform complete analysis of an APK file
        
        Args:
            apk_path: Path to the APK file
            
        Returns:
            Dictionary containing complete analysis results
        """
        start_time = time.time()
        
        try:
            # Generate scan ID
            scan_id = self.generate_scan_id(apk_path)
            
            # Extract features
            print(f"Extracting features from {apk_path}...")
            features = self.feature_extractor.extract_from_file(apk_path)
            
            # Make ML prediction
            print("Making ML prediction...")
            prediction, confidence = self._predict(features)
            
            # Calculate risk scores
            print("Calculating risk scores...")
            risk_report = self.risk_scorer.generate_risk_report(
                features, 
                prediction, 
                confidence
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Compile results
            results = {
                'scan_id': scan_id,
                'apk_name': Path(apk_path).name,
                'sha256': features['metadata'].get('SHA256'),
                'package_name': features['metadata'].get('PACOTE'),
                'file_size': features['metadata'].get('size'),
                'prediction': prediction,
                'confidence': confidence,
                'overall_risk_score': risk_report['overall']['risk_score'],
                'risk_level': risk_report['overall']['risk_level'],
                'confidentiality_score': risk_report['cia_analysis']['confidentiality']['score'],
                'integrity_score': risk_report['cia_analysis']['integrity']['score'],
                'availability_score': risk_report['cia_analysis']['availability']['score'],
                'permission_count': features['permissions']['count'],
                'api_call_count': features['api_calls']['count'],
                'intent_count': features['intents']['count'],
                'permissions': features['permissions']['list'][:50],  # Limit to 50 for storage
                'api_calls': features['api_calls']['list'][:100],  # Limit to 100
                'threat_indicators': risk_report['threat_indicators'],
                'recommendations': risk_report['recommendations'],
                'full_report': risk_report,
                'processing_time': processing_time,
                'status': 'completed'
            }
            
            print(f"Analysis completed in {processing_time:.2f} seconds")
            return results
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'scan_id': self.generate_scan_id(apk_path),
                'apk_name': Path(apk_path).name,
                'status': 'failed',
                'error_message': str(e)
            }
    
    def _predict(self, features: Dict) -> Tuple[int, float]:
        """
        Make prediction using ML model
        
        Args:
            features: Extracted features
            
        Returns:
            Tuple of (prediction, confidence)
        """
        if self.model is None:
            # Fallback: use simple heuristics
            return self._heuristic_prediction(features)
        
        try:
            # Convert features to model input
            X = self.feature_extractor.to_model_input(features)
            
            # Scale features
            if self.scaler:
                X = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X)[0]
            
            # Get confidence (probability)
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                confidence = float(proba[prediction])
            else:
                # For models without predict_proba, use distance-based confidence
                confidence = 0.75  # Default confidence
            
            return int(prediction), confidence
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            return self._heuristic_prediction(features)
    
    def _heuristic_prediction(self, features: Dict) -> Tuple[int, float]:
        """
        Fallback heuristic prediction when ML model is not available
        
        Args:
            features: Extracted features
            
        Returns:
            Tuple of (prediction, confidence)
        """
        score = 0
        
        # Check permission count
        perm_count = features['permissions']['count']
        if perm_count > 20:
            score += 30
        elif perm_count > 10:
            score += 15
        
        # Check for dangerous permissions
        dangerous_perms = [
            'SEND_SMS', 'READ_SMS', 'CALL_PHONE', 'INSTALL_PACKAGES',
            'DELETE_PACKAGES', 'MOUNT_UNMOUNT_FILESYSTEMS'
        ]
        perms = features['permissions']['list']
        for perm in perms:
            if any(dp in perm for dp in dangerous_perms):
                score += 20
        
        # Check API call count
        api_count = features['api_calls']['count']
        if api_count > 100:
            score += 20
        
        # Determine prediction
        if score >= 50:
            prediction = 1  # Malware
            confidence = min(score / 100, 0.95)
        else:
            prediction = 0  # Benign
            confidence = min((100 - score) / 100, 0.95)
        
        return prediction, confidence


# Global analysis service instance
analysis_service = AnalysisService()
