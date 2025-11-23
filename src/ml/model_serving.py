"""
Model serving infrastructure for real-time predictions.
"""
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import threading
from collections import deque
import numpy as np

from .models import DisruptionPredictor
from .feature_engineering import FeatureExtractor

logger = logging.getLogger(__name__)


class ModelServer:
    """
    Serve ML models for real-time predictions with caching and monitoring.
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 cache_size: int = 1000,
                 enable_monitoring: bool = True):
        """
        Initialize model server.

        Args:
            model_path: Path to load model from (if None, must call load_model later)
            cache_size: Maximum number of cached predictions
            enable_monitoring: Enable performance monitoring
        """
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.cache_size = cache_size
        self.enable_monitoring = enable_monitoring

        # Prediction cache (event_id -> (prediction, probability, timestamp))
        self.prediction_cache = {}
        self.cache_queue = deque(maxlen=cache_size)

        # Performance monitoring
        self.prediction_count = 0
        self.total_inference_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        # Thread safety
        self.lock = threading.Lock()

        # Load model if path provided
        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str):
        """
        Load ML model from disk.

        Args:
            model_path: Path to model file
        """
        logger.info(f"Loading model from {model_path}")
        self.model = DisruptionPredictor()
        self.model.load_model(model_path)
        logger.info("Model loaded successfully")

    def predict(self,
               event: Dict[str, Any],
               supplier: Optional[Dict[str, Any]] = None,
               route: Optional[Dict[str, Any]] = None,
               historical_disruptions: Optional[List[Dict[str, Any]]] = None,
               network_stats: Optional[Dict[str, int]] = None,
               use_cache: bool = True) -> Dict[str, Any]:
        """
        Predict disruption for an event.

        Args:
            event: Event dictionary
            supplier: Optional supplier context
            route: Optional route context
            historical_disruptions: Optional historical disruptions
            network_stats: Optional network statistics
            use_cache: Whether to use cached predictions

        Returns:
            Dictionary with prediction results
        """
        if self.model is None:
            raise ValueError("No model loaded. Call load_model() first.")

        event_id = event.get('event_id', event.get('id'))

        # Check cache
        if use_cache and event_id and event_id in self.prediction_cache:
            with self.lock:
                self.cache_hits += 1
            cached_result = self.prediction_cache[event_id]
            logger.debug(f"Cache hit for event {event_id}")
            return {
                'event_id': event_id,
                'prediction': cached_result[0],
                'probability': cached_result[1],
                'will_disrupt': bool(cached_result[0]),
                'confidence': cached_result[1],
                'cached': True,
                'timestamp': cached_result[2]
            }

        # Make prediction
        start_time = time.time()

        prediction, probability = self.model.predict_from_event(
            event=event,
            supplier=supplier,
            route=route,
            historical_disruptions=historical_disruptions,
            network_stats=network_stats
        )

        inference_time = time.time() - start_time

        # Update monitoring stats
        with self.lock:
            self.prediction_count += 1
            self.total_inference_time += inference_time
            if use_cache:
                self.cache_misses += 1

        # Cache result
        if use_cache and event_id:
            self._update_cache(event_id, prediction, probability)

        result = {
            'event_id': event_id,
            'prediction': int(prediction),
            'probability': float(probability),
            'will_disrupt': bool(prediction),
            'confidence': float(probability),
            'inference_time_ms': inference_time * 1000,
            'cached': False,
            'timestamp': datetime.now().isoformat()
        }

        logger.debug(f"Prediction for {event_id}: {prediction} (prob={probability:.3f}, time={inference_time*1000:.1f}ms)")

        return result

    def batch_predict(self,
                     events: List[Dict[str, Any]],
                     suppliers_map: Optional[Dict[str, Dict]] = None,
                     routes_map: Optional[Dict[str, Dict]] = None,
                     historical_disruptions: Optional[List[Dict[str, Any]]] = None,
                     network_stats: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        """
        Make predictions for multiple events in batch.

        Args:
            events: List of event dictionaries
            suppliers_map: Map of supplier_id -> supplier dict
            routes_map: Map of route_id -> route dict
            historical_disruptions: Historical disruptions
            network_stats: Network statistics

        Returns:
            List of prediction results
        """
        if self.model is None:
            raise ValueError("No model loaded. Call load_model() first.")

        logger.info(f"Making batch predictions for {len(events)} events")
        start_time = time.time()

        results = []

        # Extract features for all events
        feature_vectors = []
        event_ids = []

        for event in events:
            supplier = None
            route = None

            if suppliers_map:
                affected_suppliers = event.get('affected_suppliers', [])
                if affected_suppliers:
                    supplier = suppliers_map.get(affected_suppliers[0])

            if routes_map:
                affected_routes = event.get('affected_routes', [])
                if affected_routes:
                    route = routes_map.get(affected_routes[0])

            feature_vector = self.feature_extractor.create_feature_vector(
                event=event,
                supplier=supplier,
                route=route,
                historical_disruptions=historical_disruptions,
                network_stats=network_stats
            )

            feature_vectors.append(feature_vector)
            event_ids.append(event.get('event_id', event.get('id')))

        # Stack features and predict
        X = np.vstack(feature_vectors)
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)[:, 1]

        # Create results
        for i, event_id in enumerate(event_ids):
            result = {
                'event_id': event_id,
                'prediction': int(predictions[i]),
                'probability': float(probabilities[i]),
                'will_disrupt': bool(predictions[i]),
                'confidence': float(probabilities[i])
            }
            results.append(result)

            # Cache result
            if event_id:
                self._update_cache(event_id, predictions[i], probabilities[i])

        batch_time = time.time() - start_time
        avg_time = batch_time / len(events)

        logger.info(f"Batch prediction completed in {batch_time:.2f}s (avg {avg_time*1000:.1f}ms per event)")

        with self.lock:
            self.prediction_count += len(events)
            self.total_inference_time += batch_time

        return results

    def _update_cache(self, event_id: str, prediction: int, probability: float):
        """Update prediction cache."""
        with self.lock:
            # Remove oldest entry if cache is full
            if len(self.prediction_cache) >= self.cache_size:
                if self.cache_queue:
                    oldest_id = self.cache_queue.popleft()
                    self.prediction_cache.pop(oldest_id, None)

            # Add new entry
            self.prediction_cache[event_id] = (prediction, probability, datetime.now().isoformat())
            self.cache_queue.append(event_id)

    def clear_cache(self):
        """Clear prediction cache."""
        with self.lock:
            self.prediction_cache.clear()
            self.cache_queue.clear()
            logger.info("Prediction cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get server performance statistics.

        Returns:
            Dictionary of statistics
        """
        with self.lock:
            total_requests = self.cache_hits + self.cache_misses

            stats = {
                'model_type': self.model.model_type if self.model else None,
                'model_loaded': self.model is not None,
                'total_predictions': self.prediction_count,
                'total_inference_time_sec': self.total_inference_time,
                'avg_inference_time_ms': (
                    (self.total_inference_time / self.prediction_count * 1000)
                    if self.prediction_count > 0 else 0
                ),
                'cache_size': len(self.prediction_cache),
                'cache_capacity': self.cache_size,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': (
                    self.cache_hits / total_requests
                    if total_requests > 0 else 0
                ),
                'monitoring_enabled': self.enable_monitoring
            }

            return stats

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary of model information
        """
        if self.model is None:
            return {'model_loaded': False}

        return {
            'model_loaded': True,
            'model_type': self.model.model_type,
            'best_score': self.model.best_score,
            'feature_count': len(self.model.feature_extractor.get_feature_names()),
            'training_history_count': len(self.model.training_history)
        }

    def reset_stats(self):
        """Reset performance statistics."""
        with self.lock:
            self.prediction_count = 0
            self.total_inference_time = 0.0
            self.cache_hits = 0
            self.cache_misses = 0
            logger.info("Statistics reset")


class ModelRegistry:
    """
    Manage multiple models and versioning.
    """

    def __init__(self, base_path: str = "models"):
        """
        Initialize model registry.

        Args:
            base_path: Base directory for storing models
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.models = {}
        self.current_model = None
        self.current_version = None

    def register_model(self, version: str, model: DisruptionPredictor):
        """
        Register a model version.

        Args:
            version: Model version string
            model: Trained DisruptionPredictor
        """
        model_path = self.base_path / f"model_{version}.joblib"
        model.save_model(str(model_path))
        self.models[version] = {
            'path': str(model_path),
            'registered_at': datetime.now().isoformat(),
            'model_type': model.model_type,
            'best_score': model.best_score
        }
        logger.info(f"Registered model version: {version}")

    def load_model(self, version: str) -> DisruptionPredictor:
        """
        Load a model version.

        Args:
            version: Model version to load

        Returns:
            Loaded DisruptionPredictor
        """
        if version not in self.models:
            raise ValueError(f"Model version {version} not found")

        model_info = self.models[version]
        model = DisruptionPredictor()
        model.load_model(model_info['path'])

        return model

    def set_current_model(self, version: str):
        """
        Set the current production model.

        Args:
            version: Model version to use
        """
        if version not in self.models:
            raise ValueError(f"Model version {version} not found")

        self.current_model = self.load_model(version)
        self.current_version = version
        logger.info(f"Current model set to version: {version}")

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all registered models.

        Returns:
            List of model information dictionaries
        """
        models_list = []
        for version, info in self.models.items():
            model_info = {
                'version': version,
                'is_current': version == self.current_version,
                **info
            }
            models_list.append(model_info)

        return sorted(models_list, key=lambda x: x['registered_at'], reverse=True)

    def get_current_model(self) -> Optional[DisruptionPredictor]:
        """
        Get the current production model.

        Returns:
            Current DisruptionPredictor or None
        """
        return self.current_model

    def rollback(self, version: str):
        """
        Rollback to a previous model version.

        Args:
            version: Model version to rollback to
        """
        logger.warning(f"Rolling back to model version: {version}")
        self.set_current_model(version)
        logger.info("Rollback completed")


# Global model server instance
_model_server = None
_server_lock = threading.Lock()


def get_model_server() -> ModelServer:
    """
    Get global model server instance (singleton pattern).

    Returns:
        ModelServer instance
    """
    global _model_server

    if _model_server is None:
        with _server_lock:
            if _model_server is None:
                _model_server = ModelServer()
                logger.info("Global model server initialized")

    return _model_server


def set_model_server(server: ModelServer):
    """
    Set global model server instance.

    Args:
        server: ModelServer to use
    """
    global _model_server
    with _server_lock:
        _model_server = server
        logger.info("Global model server set")
