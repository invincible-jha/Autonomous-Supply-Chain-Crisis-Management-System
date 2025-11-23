"""
Tests for machine learning pipeline.
"""
import unittest
import numpy as np
import tempfile
import os
from datetime import datetime, timedelta

from src.ml.feature_engineering import FeatureExtractor
from src.ml.training_data import TrainingDataGenerator
from src.ml.models import DisruptionPredictor, ModelEvaluator, train_multiple_models
from src.ml.model_serving import ModelServer, ModelRegistry


class TestFeatureExtractor(unittest.TestCase):
    """Test feature extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor()

    def test_extract_event_features(self):
        """Test extracting features from an event."""
        event = {
            'event_id': 'test_001',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Trade war escalates',
            'description': 'Major trade sanctions announced',
            'published_at': datetime.now(),
            'location_country': 'China',
            'location_region': 'East Asia',
            'severity_score': 75.0,
            'confidence_score': 0.85
        }

        features = self.extractor.extract_event_features(event)

        # Check required features exist
        self.assertIn('event_source', features)
        self.assertIn('event_type', features)
        self.assertIn('severity_score', features)
        self.assertIn('hour_of_day', features)
        self.assertIn('text_high_severity_keywords', features)

        # Check feature values
        self.assertEqual(features['event_source'], 1)  # newsapi
        self.assertEqual(features['event_type'], 1)  # geopolitical
        self.assertEqual(features['severity_score'], 75.0)

    def test_extract_supplier_features(self):
        """Test extracting supplier features."""
        supplier = {
            'id': 'SUP001',
            'name': 'Test Supplier',
            'location': {
                'country': 'Germany',
                'region': 'Europe'
            },
            'status': 'active',
            'reliability_score': 85.0,
            'lead_time_days': 14,
            'capacity': 10000,
            'products': ['electronics', 'components'],
            'risk_factors': ['single_source']
        }

        features = self.extractor.extract_supplier_features(supplier)

        self.assertIn('supplier_reliability', features)
        self.assertIn('supplier_lead_time', features)
        self.assertIn('supplier_capacity', features)
        self.assertEqual(features['supplier_reliability'], 85.0)
        self.assertEqual(features['supplier_lead_time'], 14)
        self.assertEqual(features['supplier_risk_factor_count'], 1)

    def test_extract_route_features(self):
        """Test extracting route features."""
        route = {
            'id': 'ROUTE001',
            'transport_mode': 'sea',
            'distance_km': 5000,
            'avg_duration_hours': 120,
            'cost_per_unit': 25.0,
            'reliability_score': 90.0
        }

        features = self.extractor.extract_route_features(route)

        self.assertIn('route_distance', features)
        self.assertIn('route_duration', features)
        self.assertIn('route_reliability', features)
        self.assertEqual(features['route_distance'], 5000)
        self.assertEqual(features['route_mode'], 2)  # sea

    def test_create_feature_vector(self):
        """Test creating complete feature vector."""
        event = {
            'event_id': 'test_001',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Test event',
            'description': 'Test description',
            'published_at': datetime.now(),
            'location_country': 'China',
            'severity_score': 75.0,
            'confidence_score': 0.85
        }

        feature_vector = self.extractor.create_feature_vector(event)

        # Check it's a numpy array
        self.assertIsInstance(feature_vector, np.ndarray)
        self.assertEqual(len(feature_vector.shape), 1)  # 1D array
        self.assertGreater(len(feature_vector), 0)  # Has features

        # Check feature names stored
        self.assertGreater(len(self.extractor.get_feature_names()), 0)

    def test_batch_extract_features(self):
        """Test batch feature extraction."""
        events = [
            {
                'event_id': f'test_{i:03d}',
                'source': 'newsapi',
                'event_type': 'geopolitical',
                'title': f'Event {i}',
                'description': 'Test',
                'published_at': datetime.now(),
                'location_country': 'China',
                'severity_score': 50.0 + i,
                'confidence_score': 0.8
            }
            for i in range(5)
        ]

        feature_matrix, event_ids = self.extractor.batch_extract_features(events)

        # Check matrix shape
        self.assertEqual(feature_matrix.shape[0], 5)  # 5 events
        self.assertGreater(feature_matrix.shape[1], 0)  # Multiple features

        # Check event IDs
        self.assertEqual(len(event_ids), 5)


class TestTrainingDataGenerator(unittest.TestCase):
    """Test training data generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = TrainingDataGenerator(seed=42)

    def test_generate_events(self):
        """Test generating synthetic events."""
        events = self.generator.generate_events(n_events=100)

        self.assertEqual(len(events), 100)

        # Check first event structure
        event = events[0]
        self.assertIn('event_id', event)
        self.assertIn('source', event)
        self.assertIn('event_type', event)
        self.assertIn('title', event)
        self.assertIn('description', event)
        self.assertIn('published_at', event)
        self.assertIn('location_country', event)
        self.assertIn('severity_score', event)
        self.assertIn('confidence_score', event)

        # Check value ranges
        self.assertGreaterEqual(event['severity_score'], 0)
        self.assertLessEqual(event['severity_score'], 100)
        self.assertGreaterEqual(event['confidence_score'], 0)
        self.assertLessEqual(event['confidence_score'], 1)

    def test_generate_labeled_data(self):
        """Test generating labeled training data."""
        events, labels = self.generator.generate_labeled_data(n_samples=100)

        self.assertEqual(len(events), 100)
        self.assertEqual(len(labels), 100)

        # Check labels are binary
        unique_labels = set(labels)
        self.assertTrue(unique_labels.issubset({0, 1}))

        # Check we have both classes
        self.assertGreater(sum(labels), 0)  # At least one positive
        self.assertLess(sum(labels), 100)  # At least one negative

    def test_generate_multi_class_labels(self):
        """Test generating multi-class labels."""
        events, labels = self.generator.generate_multi_class_labels(n_samples=100)

        self.assertEqual(len(events), 100)
        self.assertEqual(len(labels), 100)

        # Check labels are 0-3
        unique_labels = set(labels)
        self.assertTrue(unique_labels.issubset({0, 1, 2, 3}))

    def test_generate_suppliers(self):
        """Test generating synthetic suppliers."""
        suppliers = self.generator.generate_suppliers(n_suppliers=20)

        self.assertEqual(len(suppliers), 20)

        # Check structure
        supplier = suppliers[0]
        self.assertIn('id', supplier)
        self.assertIn('name', supplier)
        self.assertIn('location', supplier)
        self.assertIn('reliability_score', supplier)
        self.assertIn('products', supplier)

    def test_generate_routes(self):
        """Test generating synthetic routes."""
        routes = self.generator.generate_routes(n_routes=10)

        self.assertEqual(len(routes), 10)

        # Check structure
        route = routes[0]
        self.assertIn('id', route)
        self.assertIn('origin', route)
        self.assertIn('destination', route)
        self.assertIn('transport_mode', route)
        self.assertIn('distance_km', route)


class TestDisruptionPredictor(unittest.TestCase):
    """Test disruption prediction models."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = TrainingDataGenerator(seed=42)
        self.extractor = FeatureExtractor()

        # Generate training data
        events, labels = self.generator.generate_labeled_data(n_samples=200)

        # Extract features
        feature_vectors = []
        for event in events:
            feature_vector = self.extractor.create_feature_vector(event)
            feature_vectors.append(feature_vector)

        self.X = np.vstack(feature_vectors)
        self.y = np.array(labels)

    def test_model_initialization(self):
        """Test model initialization."""
        model = DisruptionPredictor(model_type='logistic')
        self.assertIsNotNone(model.model)
        self.assertEqual(model.model_type, 'logistic')

    def test_train_logistic(self):
        """Test training logistic regression model."""
        model = DisruptionPredictor(model_type='logistic')
        metrics = model.train(self.X, self.y, validation_split=0.2, verbose=False)

        # Check metrics exist
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)

        # Check reasonable values (not perfect, not terrible)
        self.assertGreater(metrics['accuracy'], 0.5)
        self.assertLess(metrics['accuracy'], 1.0)

    def test_train_random_forest(self):
        """Test training random forest model."""
        model = DisruptionPredictor(model_type='random_forest')
        metrics = model.train(self.X, self.y, validation_split=0.2, verbose=False)

        self.assertGreater(metrics['f1_score'], 0.3)

    def test_train_xgboost(self):
        """Test training XGBoost model."""
        model = DisruptionPredictor(model_type='xgboost')
        metrics = model.train(self.X, self.y, validation_split=0.2, verbose=False)

        self.assertGreater(metrics['f1_score'], 0.3)

    def test_predict(self):
        """Test making predictions."""
        model = DisruptionPredictor(model_type='logistic')
        model.train(self.X, self.y, validation_split=0.2, verbose=False)

        # Predict on training data (just for testing)
        predictions = model.predict(self.X[:10])

        self.assertEqual(len(predictions), 10)
        self.assertTrue(all(p in [0, 1] for p in predictions))

    def test_predict_proba(self):
        """Test probability predictions."""
        model = DisruptionPredictor(model_type='logistic')
        model.train(self.X, self.y, validation_split=0.2, verbose=False)

        probabilities = model.predict_proba(self.X[:10])

        self.assertEqual(probabilities.shape, (10, 2))
        # Check probabilities sum to 1
        np.testing.assert_array_almost_equal(probabilities.sum(axis=1), np.ones(10))

    def test_predict_from_event(self):
        """Test predicting from event data."""
        model = DisruptionPredictor(model_type='logistic')
        model.train(self.X, self.y, validation_split=0.2, verbose=False)

        event = {
            'event_id': 'test_001',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Critical situation',
            'description': 'Major crisis',
            'published_at': datetime.now(),
            'location_country': 'Ukraine',
            'severity_score': 85.0,
            'confidence_score': 0.9
        }

        prediction, probability = model.predict_from_event(event)

        self.assertIn(prediction, [0, 1])
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    def test_feature_importance(self):
        """Test getting feature importance."""
        model = DisruptionPredictor(model_type='random_forest')
        model.train(self.X, self.y, validation_split=0.2, verbose=False)

        importance_df = model.get_feature_importance(top_n=10)

        self.assertEqual(len(importance_df), 10)
        self.assertIn('feature', importance_df.columns)
        self.assertIn('importance', importance_df.columns)

    def test_save_and_load_model(self):
        """Test saving and loading model."""
        # Train model
        model = DisruptionPredictor(model_type='logistic')
        model.train(self.X, self.y, validation_split=0.2, verbose=False)

        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.joblib')
            model.save_model(model_path)

            # Load model
            loaded_model = DisruptionPredictor()
            loaded_model.load_model(model_path)

            # Check predictions match
            pred1 = model.predict(self.X[:5])
            pred2 = loaded_model.predict(self.X[:5])
            np.testing.assert_array_equal(pred1, pred2)


class TestModelEvaluator(unittest.TestCase):
    """Test model evaluation and comparison."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = TrainingDataGenerator(seed=42)
        self.extractor = FeatureExtractor()

        # Generate training data
        events, labels = self.generator.generate_labeled_data(n_samples=150)

        feature_vectors = []
        for event in events:
            feature_vector = self.extractor.create_feature_vector(event)
            feature_vectors.append(feature_vector)

        self.X = np.vstack(feature_vectors)
        self.y = np.array(labels)

    def test_add_and_compare_models(self):
        """Test adding and comparing models."""
        evaluator = ModelEvaluator()

        # Train two models
        model1 = DisruptionPredictor(model_type='logistic')
        model1.train(self.X, self.y, validation_split=0.2, verbose=False)

        model2 = DisruptionPredictor(model_type='random_forest')
        model2.train(self.X, self.y, validation_split=0.2, verbose=False)

        # Add models
        evaluator.add_model('logistic', model1)
        evaluator.add_model('random_forest', model2)

        # Compare models
        results = evaluator.compare_models(self.X[:30], self.y[:30])

        self.assertEqual(len(results), 2)
        self.assertIn('model', results.columns)
        self.assertIn('f1_score', results.columns)

    def test_get_best_model(self):
        """Test getting best model."""
        evaluator = ModelEvaluator()

        # Train models
        model1 = DisruptionPredictor(model_type='logistic')
        model1.train(self.X, self.y, validation_split=0.2, verbose=False)

        model2 = DisruptionPredictor(model_type='random_forest')
        model2.train(self.X, self.y, validation_split=0.2, verbose=False)

        evaluator.add_model('logistic', model1)
        evaluator.add_model('random_forest', model2)

        # Compare and get best
        evaluator.compare_models(self.X[:30], self.y[:30])
        best_name, best_model = evaluator.get_best_model()

        self.assertIsInstance(best_name, str)
        self.assertIsInstance(best_model, DisruptionPredictor)


class TestModelServer(unittest.TestCase):
    """Test model serving."""

    def setUp(self):
        """Set up test fixtures."""
        # Create and train a simple model
        generator = TrainingDataGenerator(seed=42)
        extractor = FeatureExtractor()

        events, labels = generator.generate_labeled_data(n_samples=100)
        feature_vectors = []
        for event in events:
            feature_vector = extractor.create_feature_vector(event)
            feature_vectors.append(feature_vector)

        X = np.vstack(feature_vectors)
        y = np.array(labels)

        self.model = DisruptionPredictor(model_type='logistic')
        self.model.train(X, y, validation_split=0.2, verbose=False)

        # Save model to temp file
        self.tmpdir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.tmpdir, 'test_model.joblib')
        self.model.save_model(self.model_path)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_model_server_initialization(self):
        """Test server initialization."""
        server = ModelServer()
        self.assertIsNone(server.model)

        server.load_model(self.model_path)
        self.assertIsNotNone(server.model)

    def test_predict(self):
        """Test making predictions through server."""
        server = ModelServer(model_path=self.model_path)

        event = {
            'event_id': 'test_001',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Test',
            'description': 'Test',
            'published_at': datetime.now(),
            'location_country': 'China',
            'severity_score': 75.0,
            'confidence_score': 0.85
        }

        result = server.predict(event)

        self.assertIn('event_id', result)
        self.assertIn('prediction', result)
        self.assertIn('probability', result)
        self.assertIn('will_disrupt', result)
        self.assertIn('inference_time_ms', result)

    def test_caching(self):
        """Test prediction caching."""
        server = ModelServer(model_path=self.model_path, cache_size=100)

        event = {
            'event_id': 'test_cached',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Test',
            'description': 'Test',
            'published_at': datetime.now(),
            'location_country': 'China',
            'severity_score': 75.0,
            'confidence_score': 0.85
        }

        # First prediction (cache miss)
        result1 = server.predict(event, use_cache=True)
        self.assertFalse(result1['cached'])

        # Second prediction (cache hit)
        result2 = server.predict(event, use_cache=True)
        self.assertTrue(result2['cached'])

        # Check predictions match
        self.assertEqual(result1['prediction'], result2['prediction'])

    def test_get_stats(self):
        """Test getting server statistics."""
        server = ModelServer(model_path=self.model_path)

        event = {
            'event_id': 'test_001',
            'source': 'newsapi',
            'event_type': 'geopolitical',
            'title': 'Test',
            'description': 'Test',
            'published_at': datetime.now(),
            'location_country': 'China',
            'severity_score': 75.0,
            'confidence_score': 0.85
        }

        # Make some predictions
        server.predict(event)
        server.predict(event)

        stats = server.get_stats()

        self.assertIn('total_predictions', stats)
        self.assertIn('avg_inference_time_ms', stats)
        self.assertIn('cache_hit_rate', stats)
        self.assertEqual(stats['total_predictions'], 2)


class TestModelRegistry(unittest.TestCase):
    """Test model registry."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.registry = ModelRegistry(base_path=self.tmpdir)

        # Create simple trained model
        generator = TrainingDataGenerator(seed=42)
        extractor = FeatureExtractor()

        events, labels = generator.generate_labeled_data(n_samples=50)
        feature_vectors = []
        for event in events:
            feature_vector = extractor.create_feature_vector(event)
            feature_vectors.append(feature_vector)

        X = np.vstack(feature_vectors)
        y = np.array(labels)

        self.model = DisruptionPredictor(model_type='logistic')
        self.model.train(X, y, validation_split=0.2, verbose=False)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_register_model(self):
        """Test registering a model."""
        self.registry.register_model('v1.0', self.model)

        models = self.registry.list_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]['version'], 'v1.0')

    def test_load_model(self):
        """Test loading a registered model."""
        self.registry.register_model('v1.0', self.model)

        loaded_model = self.registry.load_model('v1.0')
        self.assertIsInstance(loaded_model, DisruptionPredictor)

    def test_set_current_model(self):
        """Test setting current production model."""
        self.registry.register_model('v1.0', self.model)
        self.registry.set_current_model('v1.0')

        current = self.registry.get_current_model()
        self.assertIsNotNone(current)
        self.assertEqual(self.registry.current_version, 'v1.0')


if __name__ == '__main__':
    unittest.main()
