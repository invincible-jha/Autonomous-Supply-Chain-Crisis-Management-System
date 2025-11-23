"""
Machine Learning models for disruption prediction.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
import joblib
import logging
from datetime import datetime
from pathlib import Path

from .feature_engineering import FeatureExtractor
from .training_data import TrainingDataGenerator

logger = logging.getLogger(__name__)


class DisruptionPredictor:
    """
    ML model for predicting supply chain disruptions.

    Supports multiple model types:
    - Logistic Regression (baseline)
    - Random Forest (baseline)
    - XGBoost (production)
    - LightGBM (production)
    """

    def __init__(self, model_type: str = 'xgboost', random_state: int = 42):
        """
        Initialize disruption predictor.

        Args:
            model_type: Type of model ('logistic', 'random_forest', 'xgboost', 'lightgbm')
            random_state: Random seed for reproducibility
        """
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_extractor = FeatureExtractor()
        self.feature_names = []
        self.training_history = []
        self.best_score = 0.0

        # Initialize model based on type
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the underlying ML model."""
        if self.model_type == 'logistic':
            self.model = LogisticRegression(
                random_state=self.random_state,
                max_iter=1000,
                class_weight='balanced'
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=self.random_state,
                class_weight='balanced',
                n_jobs=-1
            )
        elif self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='logloss',
                scale_pos_weight=2.0  # Handle class imbalance
            )
        elif self.model_type == 'lightgbm':
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=self.random_state,
                class_weight='balanced',
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        logger.info(f"Initialized {self.model_type} model")

    def train(self,
             X: np.ndarray,
             y: np.ndarray,
             validation_split: float = 0.2,
             verbose: bool = True) -> Dict[str, float]:
        """
        Train the disruption prediction model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,)
            validation_split: Fraction of data to use for validation
            verbose: Whether to print training progress

        Returns:
            Dictionary of evaluation metrics
        """
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=self.random_state, stratify=y
        )

        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Validation set: {X_val.shape[0]} samples")
        logger.info(f"Positive class ratio: {np.mean(y_train):.2%}")

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train model
        logger.info(f"Training {self.model_type} model...")
        start_time = datetime.now()

        if self.model_type in ['xgboost', 'lightgbm']:
            # Use early stopping for gradient boosting models
            self.model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_val_scaled, y_val)],
                verbose=verbose
            )
        else:
            self.model.fit(X_train_scaled, y_train)

        training_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Training completed in {training_time:.2f} seconds")

        # Evaluate on validation set
        metrics = self.evaluate(X_val_scaled, y_val)

        # Store training info
        self.training_history.append({
            'timestamp': datetime.now(),
            'model_type': self.model_type,
            'n_train_samples': X_train.shape[0],
            'n_val_samples': X_val.shape[0],
            'training_time': training_time,
            'metrics': metrics
        })

        # Update best score
        if metrics['f1_score'] > self.best_score:
            self.best_score = metrics['f1_score']
            logger.info(f"New best F1 score: {self.best_score:.4f}")

        return metrics

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            X: Feature matrix
            y: True labels

        Returns:
            Dictionary of metrics
        """
        y_pred = self.model.predict(X)
        y_pred_proba = self.model.predict_proba(X)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_pred_proba) if len(np.unique(y)) > 1 else 0.0
        }

        logger.info(f"Evaluation metrics:")
        for metric_name, value in metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")

        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict disruption labels.

        Args:
            X: Feature matrix

        Returns:
            Predicted labels (0 or 1)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict disruption probabilities.

        Args:
            X: Feature matrix

        Returns:
            Predicted probabilities (n_samples, 2)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")

        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def predict_from_event(self,
                          event: Dict[str, Any],
                          supplier: Optional[Dict[str, Any]] = None,
                          route: Optional[Dict[str, Any]] = None,
                          historical_disruptions: Optional[List[Dict[str, Any]]] = None,
                          network_stats: Optional[Dict[str, int]] = None) -> Tuple[int, float]:
        """
        Predict disruption from event data.

        Args:
            event: Event dictionary
            supplier: Optional supplier context
            route: Optional route context
            historical_disruptions: Optional historical disruptions
            network_stats: Optional network statistics

        Returns:
            Tuple of (prediction, probability)
        """
        # Extract features
        feature_vector = self.feature_extractor.create_feature_vector(
            event=event,
            supplier=supplier,
            route=route,
            historical_disruptions=historical_disruptions,
            network_stats=network_stats
        )

        # Reshape for prediction
        X = feature_vector.reshape(1, -1)

        # Predict
        prediction = self.predict(X)[0]
        probabilities = self.predict_proba(X)[0]
        probability = probabilities[1]  # Probability of disruption

        return int(prediction), float(probability)

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance from the model.

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")

        # Get feature importance based on model type
        if self.model_type == 'logistic':
            importance = np.abs(self.model.coef_[0])
        elif self.model_type in ['random_forest', 'xgboost', 'lightgbm']:
            importance = self.model.feature_importances_
        else:
            raise ValueError(f"Feature importance not supported for {self.model_type}")

        # Create DataFrame
        feature_names = self.feature_extractor.get_feature_names()
        if not feature_names:
            feature_names = [f"feature_{i}" for i in range(len(importance))]

        df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        })

        # Sort by importance
        df = df.sort_values('importance', ascending=False).head(top_n)

        return df

    def save_model(self, filepath: str):
        """
        Save model to disk.

        Args:
            filepath: Path to save model
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'feature_names': self.feature_extractor.get_feature_names(),
            'training_history': self.training_history,
            'best_score': self.best_score,
            'timestamp': datetime.now()
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """
        Load model from disk.

        Args:
            filepath: Path to load model from
        """
        model_data = joblib.load(filepath)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.feature_extractor.feature_names = model_data.get('feature_names', [])
        self.training_history = model_data.get('training_history', [])
        self.best_score = model_data.get('best_score', 0.0)

        logger.info(f"Model loaded from {filepath}")
        logger.info(f"Model type: {self.model_type}")
        logger.info(f"Best F1 score: {self.best_score:.4f}")

    def cross_validate(self,
                      X: np.ndarray,
                      y: np.ndarray,
                      cv: int = 5) -> Dict[str, List[float]]:
        """
        Perform cross-validation.

        Args:
            X: Feature matrix
            y: Labels
            cv: Number of folds

        Returns:
            Dictionary of cross-validation scores
        """
        logger.info(f"Performing {cv}-fold cross-validation...")

        X_scaled = self.scaler.fit_transform(X)

        scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        results = {}

        for score_name in scoring:
            scores = cross_val_score(
                self.model, X_scaled, y,
                cv=cv, scoring=score_name, n_jobs=-1
            )
            results[score_name] = scores.tolist()
            logger.info(f"{score_name}: {scores.mean():.4f} (+/- {scores.std():.4f})")

        return results


class ModelEvaluator:
    """
    Evaluate and compare multiple models.
    """

    def __init__(self):
        """Initialize model evaluator."""
        self.models = {}
        self.results = {}

    def add_model(self, name: str, model: DisruptionPredictor):
        """
        Add a model for comparison.

        Args:
            name: Model name
            model: Trained DisruptionPredictor
        """
        self.models[name] = model
        logger.info(f"Added model: {name}")

    def compare_models(self,
                      X_test: np.ndarray,
                      y_test: np.ndarray) -> pd.DataFrame:
        """
        Compare all models on test data.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            DataFrame with comparison results
        """
        results = []

        for name, model in self.models.items():
            logger.info(f"Evaluating {name}...")

            # Get predictions
            X_test_scaled = model.scaler.transform(X_test)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

            # Calculate metrics
            metrics = {
                'model': name,
                'model_type': model.model_type,
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0),
                'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0
            }

            results.append(metrics)

        # Create DataFrame
        df = pd.DataFrame(results)
        df = df.sort_values('f1_score', ascending=False)

        logger.info("\nModel Comparison Results:")
        logger.info(f"\n{df.to_string()}")

        self.results = df
        return df

    def get_best_model(self, metric: str = 'f1_score') -> Tuple[str, DisruptionPredictor]:
        """
        Get the best performing model.

        Args:
            metric: Metric to use for comparison

        Returns:
            Tuple of (model_name, model)
        """
        if self.results.empty:
            raise ValueError("No models have been evaluated yet")

        best_model_name = self.results.loc[self.results[metric].idxmax(), 'model']
        best_model = self.models[best_model_name]

        logger.info(f"Best model: {best_model_name} ({metric}={self.results[metric].max():.4f})")

        return best_model_name, best_model


def train_multiple_models(X: np.ndarray,
                         y: np.ndarray,
                         validation_split: float = 0.2) -> ModelEvaluator:
    """
    Train and compare multiple model types.

    Args:
        X: Feature matrix
        y: Labels
        validation_split: Fraction for validation

    Returns:
        ModelEvaluator with trained models
    """
    model_types = ['logistic', 'random_forest', 'xgboost', 'lightgbm']
    evaluator = ModelEvaluator()

    for model_type in model_types:
        logger.info(f"\n{'='*60}")
        logger.info(f"Training {model_type} model")
        logger.info(f"{'='*60}")

        try:
            model = DisruptionPredictor(model_type=model_type)
            model.train(X, y, validation_split=validation_split, verbose=False)
            evaluator.add_model(model_type, model)
        except Exception as e:
            logger.error(f"Error training {model_type}: {e}")
            continue

    return evaluator
