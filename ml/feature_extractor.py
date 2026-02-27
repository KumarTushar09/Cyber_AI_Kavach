"""
Feature Extraction Module for APK Files
Extracts permissions, API calls, and intents using Androguard
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

try:
    from androguard.core.bytecodes.apk import APK
    from androguard.core.bytecodes.dvm import DalvikVMFormat
    from androguard.core.analysis.analysis import Analysis
except ImportError:
    print("Warning: Androguard not installed. Feature extraction will be limited.")
    APK = None


class APKFeatureExtractor:
    """Extract features from APK files for malware detection"""
    
    def __init__(self, feature_list_path: Optional[str] = None):
        """
        Initialize the feature extractor
        
        Args:
            feature_list_path: Path to CSV file containing expected features
        """
        self.expected_features = []
        
        if feature_list_path:
            self.load_feature_list(feature_list_path)
    
    def load_feature_list(self, path: str):
        """Load the expected feature list from MH-100K"""
        try:
            df = pd.read_csv(path)
            self.expected_features = df['features'].tolist()
            print(f"Loaded {len(self.expected_features)} expected features")
        except Exception as e:
            print(f"Warning: Could not load feature list: {e}")
    
    def extract_from_file(self, apk_path: str) -> Dict:
        """
        Extract all features from an APK file
        
        Args:
            apk_path: Path to the APK file
            
        Returns:
            Dictionary containing extracted features
        """
        if APK is None:
            return self._extract_basic_features(apk_path)
        
        try:
            apk = APK(apk_path)
            
            features = {
                'metadata': self._extract_metadata(apk, apk_path),
                'permissions': self._extract_permissions(apk),
                'api_calls': self._extract_api_calls(apk),
                'intents': self._extract_intents(apk),
                'raw_feature_vector': {}
            }
            
            # Create feature vector matching MH-100K format
            features['raw_feature_vector'] = self._create_feature_vector(features)
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return self._extract_basic_features(apk_path)
    
    def _extract_metadata(self, apk: APK, apk_path: str) -> Dict:
        """Extract metadata from APK"""
        try:
            file_hash = self._calculate_sha256(apk_path)
            
            return {
                'SHA256': file_hash,
                'NOME': Path(apk_path).name,
                'PACOTE': apk.get_package(),
                'API_MIN': apk.get_min_sdk_version(),
                'API': apk.get_target_sdk_version(),
                'size': Path(apk_path).stat().st_size
            }
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
    
    def _extract_permissions(self, apk: APK) -> Dict:
        """Extract permissions from APK"""
        try:
            permissions = apk.get_permissions()
            
            # Create permission features
            permission_features = {}
            for perm in permissions:
                # Simplify permission name (e.g., android.permission.INTERNET -> INTERNET)
                if '.' in perm:
                    perm_name = perm.split('.')[-1]
                else:
                    perm_name = perm
                
                feature_key = f"Permission::{perm_name}"
                permission_features[feature_key] = 1
            
            return {
                'list': list(permissions),
                'count': len(permissions),
                'features': permission_features
            }
        except Exception as e:
            print(f"Error extracting permissions: {e}")
            return {'list': [], 'count': 0, 'features': {}}
    
    def _extract_api_calls(self, apk: APK) -> Dict:
        """Extract API calls from APK"""
        try:
            dex = apk.get_dex()
            if not dex:
                return {'list': [], 'count': 0, 'features': {}}
            
            # Analyze DEX
            dx = Analysis()
            api_calls = set()
            api_features = {}
            
            # Get all methods
            for dex_file in apk.get_all_dex():
                d = DalvikVMFormat(dex_file)
                
                for method in d.get_methods():
                    class_name = method.get_class_name()
                    method_name = method.get_name()
                    
                    # Focus on Android API calls
                    if class_name.startswith('Landroid/'):
                        api_call = f"{class_name}.{method_name}()"
                        api_calls.add(api_call)
                        
                        feature_key = f"APICall::{api_call}"
                        api_features[feature_key] = 1
            
            return {
                'list': list(api_calls),
                'count': len(api_calls),
                'features': api_features
            }
        except Exception as e:
            print(f"Error extracting API calls: {e}")
            return {'list': [], 'count': 0, 'features': {}}
    
    def _extract_intents(self, apk: APK) -> Dict:
        """Extract intents from APK"""
        try:
            activities = apk.get_activities()
            services = apk.get_services()
            receivers = apk.get_receivers()
            
            intent_features = {}
            intent_list = []
            
            # Extract intent filters from manifest
            manifest = apk.get_android_manifest_axml()
            if manifest:
                # Parse intent actions
                # This is simplified; full implementation would parse XML
                intent_actions = [
                    'MAIN', 'VIEW', 'SEND', 'BOOT_COMPLETED', 
                    'PACKAGE_ADDED', 'AUDIO_BECOMING_NOISY'
                ]
                
                for action in intent_actions:
                    feature_key = f"Intent::{action}"
                    # This is placeholder - real implementation would check manifest
                    intent_features[feature_key] = 0
            
            return {
                'activities': activities,
                'services': services,
                'receivers': receivers,
                'count': len(activities) + len(services) + len(receivers),
                'features': intent_features
            }
        except Exception as e:
            print(f"Error extracting intents: {e}")
            return {'activities': [], 'services': [], 'receivers': [], 'count': 0, 'features': {}}
    
    def _create_feature_vector(self, features: Dict) -> Dict:
        """
        Create a feature vector matching the MH-100K dataset format
        
        Args:
            features: Extracted features dictionary
            
        Returns:
            Feature vector dictionary with all expected features
        """
        feature_vector = {}
        
        # Combine all feature dictionaries
        all_features = {}
        if 'permissions' in features:
            all_features.update(features['permissions'].get('features', {}))
        if 'api_calls' in features:
            all_features.update(features['api_calls'].get('features', {}))
        if 'intents' in features:
            all_features.update(features['intents'].get('features', {}))
        
        # Create vector with expected features (0 if not present)
        if self.expected_features:
            for feature in self.expected_features:
                feature_vector[feature] = all_features.get(feature, 0)
        else:
            feature_vector = all_features
        
        return feature_vector
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_basic_features(self, apk_path: str) -> Dict:
        """Extract basic features when Androguard is not available"""
        file_hash = self._calculate_sha256(apk_path)
        file_size = Path(apk_path).stat().st_size
        
        return {
            'metadata': {
                'SHA256': file_hash,
                'NOME': Path(apk_path).name,
                'size': file_size
            },
            'permissions': {'list': [], 'count': 0, 'features': {}},
            'api_calls': {'list': [], 'count': 0, 'features': {}},
            'intents': {'activities': [], 'services': [], 'receivers': [], 'count': 0, 'features': {}},
            'raw_feature_vector': {}
        }
    
    def to_model_input(self, features: Dict) -> np.ndarray:
        """
        Convert extracted features to model input format
        
        Args:
            features: Extracted features dictionary
            
        Returns:
            NumPy array suitable for model prediction
        """
        if 'raw_feature_vector' not in features:
            return np.zeros((1, len(self.expected_features)))
        
        feature_vector = features['raw_feature_vector']
        
        if self.expected_features:
            # Ensure features are in the correct order
            vector = [feature_vector.get(feature, 0) for feature in self.expected_features]
            return np.array(vector).reshape(1, -1)
        else:
            # If no expected features, use what we have
            return np.array(list(feature_vector.values())).reshape(1, -1)


def test_extraction(apk_path: str):
    """Test feature extraction on an APK file"""
    print(f"Testing feature extraction on: {apk_path}")
    
    extractor = APKFeatureExtractor()
    features = extractor.extract_from_file(apk_path)
    
    print("\nExtracted Features:")
    print(f"  Metadata: {features['metadata']}")
    print(f"  Permissions: {features['permissions']['count']}")
    print(f"  API Calls: {features['api_calls']['count']}")
    print(f"  Intents: {features['intents']['count']}")
    print(f"  Feature Vector Size: {len(features['raw_feature_vector'])}")
    
    return features


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_extraction(sys.argv[1])
    else:
        print("Usage: python feature_extractor.py <path_to_apk>")
