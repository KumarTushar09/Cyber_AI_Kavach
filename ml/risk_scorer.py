"""
NIST CIA-Based Risk Scoring Engine
Calculates risk scores based on Confidentiality, Integrity, and Availability
"""
from typing import Dict, List, Tuple
from enum import Enum
import numpy as np


class RiskLevel(Enum):
    """Risk level classifications"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CIAComponent(Enum):
    """CIA Triad components"""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"


class NISTRiskScorer:
    """
    Calculate risk scores based on NIST CIA framework
    """
    
    def __init__(self):
        # Define risky permissions for each CIA component
        self.confidentiality_permissions = {
            'READ_CONTACTS': 10,
            'READ_SMS': 10,
            'READ_CALL_LOG': 10,
            'ACCESS_FINE_LOCATION': 9,
            'ACCESS_COARSE_LOCATION': 8,
            'READ_PHONE_STATE': 8,
            'READ_EXTERNAL_STORAGE': 7,
            'CAMERA': 8,
            'RECORD_AUDIO': 9,
            'GET_ACCOUNTS': 7,
            'READ_CALENDAR': 6,
            'BODY_SENSORS': 7,
            'READ_SYNC_SETTINGS': 5,
        }
        
        self.integrity_permissions = {
            'WRITE_EXTERNAL_STORAGE': 8,
            'WRITE_SETTINGS': 7,
            'WRITE_CONTACTS': 7,
            'WRITE_SMS': 8,
            'WRITE_CALL_LOG': 8,
            'INSTALL_PACKAGES': 10,
            'DELETE_PACKAGES': 10,
            'MOUNT_UNMOUNT_FILESYSTEMS': 9,
            'WRITE_SECURE_SETTINGS': 9,
            'CHANGE_CONFIGURATION': 6,
            'MODIFY_PHONE_STATE': 8,
            'SYSTEM_ALERT_WINDOW': 7,
            'REQUEST_INSTALL_PACKAGES': 9,
        }
        
        self.availability_permissions = {
            'WAKE_LOCK': 6,
            'DISABLE_KEYGUARD': 7,
            'KILL_BACKGROUND_PROCESSES': 6,
            'REBOOT': 10,
            'SHUTDOWN': 10,
            'FOREGROUND_SERVICE': 5,
            'BATTERY_STATS': 5,
            'BIND_DEVICE_ADMIN': 9,
            'RECEIVE_BOOT_COMPLETED': 6,
        }
        
        # Define risky API calls
        self.confidentiality_apis = [
            'getDeviceId', 'getSubscriberId', 'getLine1Number',
            'getSimSerialNumber', 'getLastKnownLocation', 
            'getAccounts', 'query', 'execSQL'
        ]
        
        self.integrity_apis = [
            'Runtime.exec', 'ProcessBuilder', 'DexClassLoader',
            'PathClassLoader', 'createPackageContext', 'setComponentEnabledSetting',
            'Cipher.getInstance', 'sendTextMessage', 'sendDataMessage'
        ]
        
        self.availability_apis = [
            'acquireWakeLock', 'killBackgroundProcesses', 'System.exit',
            'Process.killProcess', 'setMobileDataEnabled', 'setWifiEnabled'
        ]
        
        # Risk thresholds
        self.thresholds = {
            RiskLevel.CRITICAL: 80,
            RiskLevel.HIGH: 60,
            RiskLevel.MEDIUM: 40,
            RiskLevel.LOW: 20,
            RiskLevel.SAFE: 0
        }
    
    def calculate_cia_scores(self, features: Dict) -> Dict[str, float]:
        """
        Calculate individual CIA component scores
        
        Args:
            features: Extracted APK features
            
        Returns:
            Dictionary with C, I, A scores (0-100)
        """
        # Extract permission and API call lists
        permissions = features.get('permissions', {}).get('list', [])
        api_calls = features.get('api_calls', {}).get('list', [])
        
        # Calculate Confidentiality score
        c_score = self._calculate_confidentiality(permissions, api_calls)
        
        # Calculate Integrity score
        i_score = self._calculate_integrity(permissions, api_calls)
        
        # Calculate Availability score
        a_score = self._calculate_availability(permissions, api_calls)
        
        return {
            'confidentiality': min(c_score, 100.0),
            'integrity': min(i_score, 100.0),
            'availability': min(a_score, 100.0)
        }
    
    def _calculate_confidentiality(self, permissions: List[str], api_calls: List[str]) -> float:
        """Calculate Confidentiality risk score"""
        score = 0.0
        
        # Check permissions
        for perm in permissions:
            perm_name = perm.split('.')[-1] if '.' in perm else perm
            if perm_name in self.confidentiality_permissions:
                score += self.confidentiality_permissions[perm_name]
        
        # Check API calls
        for api in api_calls:
            for risky_api in self.confidentiality_apis:
                if risky_api in api:
                    score += 5
                    break
        
        # Normalize (assume max 10 risky permissions + 10 risky APIs)
        max_score = 10 * 10 + 10 * 5  # 150
        normalized = (score / max_score) * 100
        
        return normalized
    
    def _calculate_integrity(self, permissions: List[str], api_calls: List[str]) -> float:
        """Calculate Integrity risk score"""
        score = 0.0
        
        # Check permissions
        for perm in permissions:
            perm_name = perm.split('.')[-1] if '.' in perm else perm
            if perm_name in self.integrity_permissions:
                score += self.integrity_permissions[perm_name]
        
        # Check API calls
        for api in api_calls:
            for risky_api in self.integrity_apis:
                if risky_api in api:
                    score += 5
                    break
        
        # Normalize
        max_score = 10 * 10 + 10 * 5  # 150
        normalized = (score / max_score) * 100
        
        return normalized
    
    def _calculate_availability(self, permissions: List[str], api_calls: List[str]) -> float:
        """Calculate Availability risk score"""
        score = 0.0
        
        # Check permissions
        for perm in permissions:
            perm_name = perm.split('.')[-1] if '.' in perm else perm
            if perm_name in self.availability_permissions:
                score += self.availability_permissions[perm_name]
        
        # Check API calls
        for api in api_calls:
            for risky_api in self.availability_apis:
                if risky_api in api:
                    score += 5
                    break
        
        # Normalize
        max_score = 10 * 10 + 10 * 5  # 150
        normalized = (score / max_score) * 100
        
        return normalized
    
    def calculate_overall_risk(self, cia_scores: Dict[str, float], 
                              ml_confidence: float) -> Tuple[float, RiskLevel]:
        """
        Calculate overall risk score combining CIA and ML confidence
        
        Args:
            cia_scores: Dictionary with C, I, A scores
            ml_confidence: ML model confidence (0-1)
            
        Returns:
            Tuple of (overall_score, risk_level)
        """
        # Weight the CIA components
        weights = {
            'confidentiality': 0.35,
            'integrity': 0.35,
            'availability': 0.30
        }
        
        # Calculate weighted CIA score
        cia_score = sum(cia_scores[key] * weights[key] for key in weights)
        
        # Combine with ML confidence (70% CIA, 30% ML)
        overall_score = (cia_score * 0.7) + (ml_confidence * 100 * 0.3)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        return overall_score, risk_level
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score >= self.thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif score >= self.thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif score >= self.thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif score >= self.thresholds[RiskLevel.LOW]:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    def generate_risk_report(self, features: Dict, ml_prediction: int, 
                           ml_confidence: float) -> Dict:
        """
        Generate a comprehensive risk report
        
        Args:
            features: Extracted APK features
            ml_prediction: ML model prediction (0=benign, 1=malware)
            ml_confidence: ML model confidence score (0-1)
            
        Returns:
            Comprehensive risk report dictionary
        """
        # Calculate CIA scores
        cia_scores = self.calculate_cia_scores(features)
        
        # Calculate overall risk
        overall_score, risk_level = self.calculate_overall_risk(cia_scores, ml_confidence)
        
        # Generate detailed analysis
        report = {
            'overall': {
                'risk_score': round(overall_score, 2),
                'risk_level': risk_level.value,
                'ml_prediction': 'Malware' if ml_prediction == 1 else 'Benign',
                'ml_confidence': round(ml_confidence * 100, 2)
            },
            'cia_analysis': {
                'confidentiality': {
                    'score': round(cia_scores['confidentiality'], 2),
                    'level': self._determine_risk_level(cia_scores['confidentiality']).value,
                    'description': self._get_cia_description('confidentiality', cia_scores['confidentiality'])
                },
                'integrity': {
                    'score': round(cia_scores['integrity'], 2),
                    'level': self._determine_risk_level(cia_scores['integrity']).value,
                    'description': self._get_cia_description('integrity', cia_scores['integrity'])
                },
                'availability': {
                    'score': round(cia_scores['availability'], 2),
                    'level': self._determine_risk_level(cia_scores['availability']).value,
                    'description': self._get_cia_description('availability', cia_scores['availability'])
                }
            },
            'recommendations': self._generate_recommendations(risk_level, cia_scores, ml_prediction),
            'threat_indicators': self._identify_threat_indicators(features, cia_scores)
        }
        
        return report
    
    def _get_cia_description(self, component: str, score: float) -> str:
        """Get description for CIA component score"""
        descriptions = {
            'confidentiality': {
                'critical': 'Severe data privacy concerns. App requests extensive access to sensitive data.',
                'high': 'Significant privacy risks. Multiple sensitive permissions detected.',
                'medium': 'Moderate privacy concerns. Some sensitive data access requested.',
                'low': 'Minor privacy considerations. Limited sensitive data access.',
                'safe': 'No significant privacy concerns detected.'
            },
            'integrity': {
                'critical': 'Critical system integrity threats. App can modify system and data.',
                'high': 'High integrity risks. Significant modification capabilities detected.',
                'medium': 'Moderate integrity concerns. Some modification permissions present.',
                'low': 'Minimal integrity risks. Limited modification capabilities.',
                'safe': 'No significant integrity threats detected.'
            },
            'availability': {
                'critical': 'Severe availability threats. App can disrupt device functionality.',
                'high': 'High availability risks. Can significantly impact device performance.',
                'medium': 'Moderate availability concerns. Some resource control detected.',
                'low': 'Minor availability considerations. Limited resource impact.',
                'safe': 'No significant availability threats detected.'
            }
        }
        
        level = self._determine_risk_level(score).value
        return descriptions.get(component, {}).get(level, 'Unknown risk level')
    
    def _generate_recommendations(self, risk_level: RiskLevel, 
                                 cia_scores: Dict[str, float], 
                                 ml_prediction: int) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("⛔ DO NOT INSTALL - Critical security threat detected")
            recommendations.append("Block this application immediately")
            recommendations.append("Report to security team for analysis")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("⚠️ High risk - Installation not recommended")
            recommendations.append("Detailed security review required before installation")
            recommendations.append("Consider alternative applications")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("⚡ Moderate risk - Proceed with caution")
            recommendations.append("Review requested permissions carefully")
            recommendations.append("Monitor app behavior after installation")
        elif risk_level == RiskLevel.LOW:
            recommendations.append("ℹ️ Low risk - Generally safe")
            recommendations.append("Standard security precautions apply")
        else:
            recommendations.append("✅ Safe - No significant threats detected")
        
        # Add CIA-specific recommendations
        if cia_scores['confidentiality'] > 60:
            recommendations.append("📱 Limit access to sensitive personal data")
        if cia_scores['integrity'] > 60:
            recommendations.append("🔒 Restrict system modification permissions")
        if cia_scores['availability'] > 60:
            recommendations.append("⚙️ Monitor resource consumption and background activity")
        
        return recommendations
    
    def _identify_threat_indicators(self, features: Dict, 
                                   cia_scores: Dict[str, float]) -> List[str]:
        """Identify specific threat indicators"""
        indicators = []
        
        permissions = features.get('permissions', {}).get('list', [])
        api_calls = features.get('api_calls', {}).get('list', [])
        
        # Check for dangerous permission combinations
        if any('LOCATION' in p for p in permissions) and any('SEND_SMS' in p for p in permissions):
            indicators.append("Suspicious: Location tracking + SMS sending capability")
        
        if any('CAMERA' in p for p in permissions) and any('INTERNET' in p for p in permissions):
            indicators.append("Suspicious: Camera access + Internet connectivity")
        
        if any('INSTALL_PACKAGES' in p for p in permissions):
            indicators.append("Critical: Can install additional packages")
        
        # Check for risky API calls
        if any('Runtime.exec' in api for api in api_calls):
            indicators.append("Critical: Can execute system commands")
        
        if any('DexClassLoader' in api for api in api_calls):
            indicators.append("Warning: Dynamic code loading detected")
        
        # Check excessive permissions
        if len(permissions) > 20:
            indicators.append(f"Warning: Excessive permissions requested ({len(permissions)} total)")
        
        return indicators


def test_risk_scoring():
    """Test the risk scoring system"""
    # Sample features
    sample_features = {
        'permissions': {
            'list': [
                'android.permission.INTERNET',
                'android.permission.READ_CONTACTS',
                'android.permission.ACCESS_FINE_LOCATION',
                'android.permission.SEND_SMS',
                'android.permission.WRITE_EXTERNAL_STORAGE'
            ],
            'count': 5
        },
        'api_calls': {
            'list': [
                'Landroid/telephony/TelephonyManager.getDeviceId()',
                'Ljava/lang/Runtime.exec()',
            ],
            'count': 2
        }
    }
    
    scorer = NISTRiskScorer()
    report = scorer.generate_risk_report(sample_features, ml_prediction=1, ml_confidence=0.85)
    
    print("Risk Assessment Report:")
    print(f"Overall Risk: {report['overall']['risk_level'].upper()} ({report['overall']['risk_score']})")
    print(f"\nCIA Analysis:")
    print(f"  Confidentiality: {report['cia_analysis']['confidentiality']['score']} - {report['cia_analysis']['confidentiality']['level']}")
    print(f"  Integrity: {report['cia_analysis']['integrity']['score']} - {report['cia_analysis']['integrity']['level']}")
    print(f"  Availability: {report['cia_analysis']['availability']['score']} - {report['cia_analysis']['availability']['level']}")
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")


if __name__ == "__main__":
    test_risk_scoring()
