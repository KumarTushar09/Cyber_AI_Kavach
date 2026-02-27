"""
ML Model Training Script for APK Malware Detection
Trains on MH-100K Dataset with multiple classifiers
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import argparse
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedShuffleSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    accuracy_score, precision_score, recall_score, f1_score
)
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config.config import settings


class MalwareModelTrainer:
    """Train and evaluate malware detection models"""
    
    def __init__(self, subset_fraction=None, metrics_path=None, baseline_metrics_path=None, use_smote=True):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.results = {}
        self.sample_count = 0
        self.feature_count = 0
        self.label_distribution = {}
        self.use_smote = use_smote
        if subset_fraction is None:
            subset_fraction = float(os.getenv("TRAIN_SUBSET_FRACTION", "1.0"))
        self.subset_fraction = subset_fraction
        self.metrics_path = metrics_path
        self.baseline_metrics_path = baseline_metrics_path
        
    def load_data(self):
        """Load and preprocess the MH-100K dataset"""
        print("Loading dataset...")
        
        try:
            # The actual feature data is in mh_100k_dataset.csv
            # (mh_100k_features_all.csv is just a list of feature names, not data)
            features_path = Path(os.getenv('DATASET_PATH', settings.DATASET_PATH))
            labels_path = Path(os.getenv('LABELS_PATH', settings.LABELS_PATH))
            
            print(f"Features path: {features_path}")
            print(f"Labels path: {labels_path}")
            
            # Read header to get column info
            header_df = pd.read_csv(features_path, nrows=0)
            columns = header_df.columns.tolist()
            print(f"Detected {len(columns)} feature columns")

            # All columns are features in mh_100k_dataset.csv
            # (it doesn't have a CLASS column - that's in the labels file)
            feature_cols = columns
            self.feature_names = feature_cols
            
            dtype_map = {col: np.float32 for col in feature_cols}

            if 0 < self.subset_fraction < 1.0:
                X, y = self._load_stratified_subset_chunked(
                    features_path,
                    labels_path,
                    feature_cols,
                    dtype_map
                )
                print(f"Dataset loaded (subset): {X.shape[0]} samples, {X.shape[1]} features")
            else:
                # Load features
                print("Loading features...")
                X_df = pd.read_csv(
                    features_path,
                    usecols=feature_cols,
                    dtype=dtype_map,
                    low_memory=False
                )
                X = X_df.to_numpy(copy=False)
                np.nan_to_num(X, copy=False)
                
                # Load labels separately
                print("Loading labels...")
                labels_df = pd.read_csv(labels_path)
                # The labels file has 'class' or 'CLASS' column
                label_col = 'class' if 'class' in labels_df.columns else 'CLASS'
                label_values = labels_df[label_col].to_numpy(copy=False)
                np.nan_to_num(label_values, copy=False)
                y = label_values.astype(np.int8, copy=False)
                
                print(f"Dataset loaded: {X.shape[0]} samples, {X.shape[1]} features")

            print(f"Features shape: {X.shape}")
            label_counts = pd.Series(y).value_counts()
            print(f"Labels distribution:")
            print(label_counts)
            print(f"Malware ratio: {(y.sum() / len(y) * 100):.2f}%")

            self.sample_count = X.shape[0]
            self.feature_count = X.shape[1]
            self.label_distribution = label_counts.to_dict()
            
            return X, y
            
        except FileNotFoundError as e:
            print(f"Error: Dataset file not found - {e}")
            print("Please ensure the MH-100K dataset is extracted at:")
            print(f"  {settings.DATASET_PATH}")
            raise
        except Exception as e:
            print(f"Error loading dataset: {e}")
            raise
    
    def preprocess_data(self, X, y):
        """Split and scale the data"""
        print("\nPreprocessing data...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # Handle class imbalance with SMOTE (optional)
        if self.use_smote:
            print("Applying SMOTE for class balancing...")
            smote = SMOTE(random_state=42)
            X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

            print(f"After SMOTE: {X_train_balanced.shape[0]} samples")
            print(f"Balanced class distribution:")
            print(pd.Series(y_train_balanced).value_counts())
        else:
            print("Skipping SMOTE; using class_weight in models")
            X_train_balanced, y_train_balanced = X_train, y_train
        
        # Scale features
        print("Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train_balanced)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train_balanced, y_test

    def _apply_stratified_subset(self, X, y):
        """Reduce dataset size with stratified sampling"""
        fraction = self.subset_fraction
        print(f"Applying stratified subset: {fraction:.2f} of data")
        splitter = StratifiedShuffleSplit(n_splits=1, train_size=fraction, random_state=42)
        indices, _ = next(splitter.split(X, y))
        X_subset = X[indices]
        y_subset = y[indices]
        print(f"Subset size: {X_subset.shape[0]} samples")
        return X_subset, y_subset

    def _load_stratified_subset_chunked(self, features_path, labels_path, feature_cols, dtype_map):
        """Load a stratified subset without reading the full dataset into memory"""
        fraction = self.subset_fraction
        print(f"Applying stratified subset: {fraction:.2f} of data")

        chunk_size = 20000
        if os.getenv("RAM_GB") == "16":
            chunk_size = 10000
            print("Using tuned chunk size for 16 GB RAM: 10000")

        # First pass: count labels from labels file
        total_counts = {0: 0, 1: 0}
        
        # Detect label column name
        labels_header = pd.read_csv(labels_path, nrows=0)
        label_col = 'class' if 'class' in labels_header.columns else 'CLASS'
        
        print(f"Reading labels from column: {label_col}")
        label_reader = pd.read_csv(
            labels_path,
            usecols=[label_col],
            dtype={label_col: np.float32},
            chunksize=chunk_size,
            low_memory=True
        )
        for chunk in label_reader:
            label_values = chunk[label_col].to_numpy(copy=False)
            np.nan_to_num(label_values, copy=False)
            labels = label_values.astype(np.int8, copy=False)
            total_counts[0] += int((labels == 0).sum())
            total_counts[1] += int((labels == 1).sum())

        target_counts = {
            0: int(total_counts[0] * fraction),
            1: int(total_counts[1] * fraction)
        }
        print(f"Target subset counts: {target_counts}")

        # Second pass: sample per class
        rng = np.random.default_rng(42)
        X_parts = []
        y_parts = []
        remaining = target_counts.copy()

        # Read features and labels in parallel chunks
        features_reader = pd.read_csv(
            features_path,
            usecols=feature_cols,
            dtype=dtype_map,
            chunksize=chunk_size,
            low_memory=True
        )
        
        labels_reader = pd.read_csv(
            labels_path,
            usecols=[label_col],
            dtype={label_col: np.float32},
            chunksize=chunk_size,
            low_memory=True
        )
        
        for features_chunk, labels_chunk in zip(features_reader, labels_reader):
            if remaining[0] <= 0 and remaining[1] <= 0:
                break

            label_values = labels_chunk[label_col].to_numpy(copy=False)
            np.nan_to_num(label_values, copy=False)
            labels = label_values.astype(np.int8, copy=False)

            for cls in (0, 1):
                need = remaining[cls]
                if need <= 0:
                    continue
                idx = np.flatnonzero(labels == cls)
                if idx.size == 0:
                    continue
                take = min(need, idx.size)
                chosen = rng.choice(idx, size=take, replace=False)
                X_parts.append(features_chunk.iloc[chosen][feature_cols].to_numpy(copy=False))
                y_parts.append(labels[chosen])
                remaining[cls] -= take

        if not X_parts:
            raise RuntimeError("No data sampled from dataset. Check label column or subset fraction.")

        X = np.vstack(X_parts)
        y = np.concatenate(y_parts)
        np.nan_to_num(X, copy=False)
        print(f"Subset size: {X.shape[0]} samples")
        return X, y
    
    def train_models(self, X_train, y_train):
        """Train multiple models and select the best"""
        print("\n" + "="*60)
        print("Training ML Models")
        print("="*60)
        
        models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=10,
                random_state=42
            ),
            'XGBoost': xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=10,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        }
        
        best_score = 0
        best_model_name = None
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1', n_jobs=-1)
            mean_cv_score = cv_scores.mean()
            
            print(f"  Cross-validation F1 Score: {mean_cv_score:.4f} (+/- {cv_scores.std():.4f})")
            
            # Track best model
            if mean_cv_score > best_score:
                best_score = mean_cv_score
                best_model_name = name
                self.model = model
        
        print(f"\n{'='*60}")
        print(f"Best Model: {best_model_name} (F1: {best_score:.4f})")
        print(f"{'='*60}")
        
        return best_model_name
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate the trained model"""
        print("\n" + "="*60)
        print("Model Evaluation")
        print("="*60)
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\nAccuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print(f"ROC AUC:   {roc_auc:.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Benign', 'Malware']))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Store results
        self.results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc
        }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.analyze_feature_importance()
    
    def analyze_feature_importance(self, top_n=20):
        """Analyze and display top important features"""
        print("\n" + "="*60)
        print(f"Top {top_n} Important Features")
        print("="*60)
        
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        for i, idx in enumerate(indices, 1):
            feature_name = self.feature_names[idx] if idx < len(self.feature_names) else f"Feature_{idx}"
            print(f"{i:2d}. {feature_name:60s} {importances[idx]:.6f}")
    
    def save_model(self):
        """Save the trained model and scaler"""
        print("\n" + "="*60)
        print("Saving Model")
        print("="*60)
        
        # Ensure model directory exists
        settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump(self.model, settings.MODEL_PATH)
        print(f"Model saved to: {settings.MODEL_PATH}")
        
        # Save scaler
        joblib.dump(self.scaler, settings.SCALER_PATH)
        print(f"Scaler saved to: {settings.SCALER_PATH}")
        
        # Save feature names
        feature_info = {
            'feature_names': self.feature_names,
            'metrics': self.results
        }
        joblib.dump(feature_info, settings.FEATURE_EXTRACTOR_PATH)
        print(f"Feature info saved to: {settings.FEATURE_EXTRACTOR_PATH}")
        
        print("\nModel training completed successfully!")
    
    def run(self):
        """Execute the complete training pipeline"""
        try:
            # Load data
            X, y = self.load_data()
            
            # Preprocess
            X_train, X_test, y_train, y_test = self.preprocess_data(X, y)
            
            # Train models
            best_model = self.train_models(X_train, y_train)
            
            # Evaluate
            self.evaluate_model(X_test, y_test)

            # Save metrics
            self.save_metrics()
            
            # Save
            self.save_model()
            
            return True
            
        except Exception as e:
            print(f"\nError during training: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_metrics(self):
        """Save evaluation metrics and optionally compare to baseline"""
        if not self.results:
            return

        metrics = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'subset_fraction': self.subset_fraction,
            'samples': self.sample_count,
            'features': self.feature_count,
            'label_distribution': self.label_distribution,
            'metrics': self.results
        }

        if self.metrics_path is None:
            if self.subset_fraction >= 1.0:
                self.metrics_path = settings.MODEL_DIR / "metrics_full.json"
            else:
                subset_pct = int(self.subset_fraction * 100)
                self.metrics_path = settings.MODEL_DIR / f"metrics_subset_{subset_pct}.json"

        metrics_path = Path(self.metrics_path)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics saved to: {metrics_path}")

        baseline_path = self.baseline_metrics_path
        if baseline_path is None and self.subset_fraction < 1.0:
            baseline_path = settings.MODEL_DIR / "metrics_full.json"

        if baseline_path and Path(baseline_path).exists():
            try:
                with open(baseline_path, 'r', encoding='utf-8') as f:
                    baseline = json.load(f)
                self._print_metrics_diff(baseline.get('metrics', {}), self.results)
            except Exception as e:
                print(f"Warning: Failed to load baseline metrics: {e}")

    def _print_metrics_diff(self, baseline_metrics, current_metrics):
        """Print metric deltas versus baseline"""
        if not baseline_metrics:
            return
        print("\nMetric deltas vs baseline:")
        for key in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']:
            if key in baseline_metrics and key in current_metrics:
                delta = current_metrics[key] - baseline_metrics[key]
                print(f"  {key}: {delta:+.4f}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="APK Malware Detection - Model Training")
    parser.add_argument("--subset-fraction", type=float, default=None, help="Stratified subset fraction (0-1]")
    parser.add_argument("--metrics-path", type=str, default=None, help="Path to save metrics JSON")
    parser.add_argument("--baseline-metrics", type=str, default=None, help="Path to baseline metrics JSON")
    parser.add_argument("--no-smote", action="store_true", help="Disable SMOTE balancing")
    args = parser.parse_args()

    print("="*60)
    print("APK Malware Detection - Model Training")
    print("="*60)
    print(f"Dataset: MH-100K")
    print(f"Features: 166 permissions + 24,417 API calls + 250 intents")
    print("="*60)
    
    trainer = MalwareModelTrainer(
        subset_fraction=args.subset_fraction,
        metrics_path=args.metrics_path,
        baseline_metrics_path=args.baseline_metrics,
        use_smote=not args.no_smote
    )
    success = trainer.run()
    
    if success:
        print("\n" + "="*60)
        print("✓ Training completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("✗ Training failed!")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit(main())
