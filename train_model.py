#!/usr/bin/env python
"""
Train disruption prediction models.

Usage:
    python train_model.py --model xgboost --samples 1000 --output models/xgboost_v1.joblib
"""
import argparse
import logging
import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ml.training_data import TrainingDataGenerator
from src.ml.feature_engineering import FeatureExtractor
from src.ml.models import DisruptionPredictor, ModelEvaluator, train_multiple_models
from src.ml.model_serving import ModelRegistry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train disruption prediction models')

    parser.add_argument(
        '--model',
        type=str,
        default='xgboost',
        choices=['logistic', 'random_forest', 'xgboost', 'lightgbm', 'all'],
        help='Model type to train (default: xgboost)'
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=1000,
        help='Number of training samples to generate (default: 1000)'
    )

    parser.add_argument(
        '--validation-split',
        type=float,
        default=0.2,
        help='Validation split fraction (default: 0.2)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='models/model.joblib',
        help='Output path for saved model (default: models/model.joblib)'
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare multiple model types'
    )

    parser.add_argument(
        '--register',
        type=str,
        help='Register model in registry with given version'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose training output'
    )

    return parser.parse_args()


def generate_training_data(n_samples: int, seed: int):
    """Generate synthetic training data."""
    logger.info(f"Generating {n_samples} synthetic training samples...")

    generator = TrainingDataGenerator(seed=seed)
    events, labels = generator.generate_labeled_data(n_samples=n_samples)

    logger.info(f"Generated {len(events)} events")
    logger.info(f"Disruption rate: {np.mean(labels):.2%}")

    return events, labels


def extract_features(events, seed: int):
    """Extract features from events."""
    logger.info("Extracting features from events...")

    extractor = FeatureExtractor()
    feature_vectors = []

    for event in events:
        feature_vector = extractor.create_feature_vector(event)
        feature_vectors.append(feature_vector)

    X = np.vstack(feature_vectors)

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Feature names: {len(extractor.get_feature_names())}")

    return X, extractor


def train_single_model(model_type: str,
                      X: np.ndarray,
                      y: np.ndarray,
                      validation_split: float,
                      verbose: bool):
    """Train a single model."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {model_type} model")
    logger.info(f"{'='*60}\n")

    model = DisruptionPredictor(model_type=model_type)
    metrics = model.train(X, y, validation_split=validation_split, verbose=verbose)

    logger.info("\nTraining completed!")
    logger.info(f"Final metrics:")
    for metric_name, value in metrics.items():
        logger.info(f"  {metric_name}: {value:.4f}")

    # Show feature importance
    if model_type in ['random_forest', 'xgboost', 'lightgbm']:
        logger.info("\nTop 10 most important features:")
        importance_df = model.get_feature_importance(top_n=10)
        for idx, row in importance_df.iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

    return model, metrics


def compare_models(X: np.ndarray, y: np.ndarray, validation_split: float):
    """Compare multiple model types."""
    logger.info("\n" + "="*60)
    logger.info("Comparing Multiple Models")
    logger.info("="*60 + "\n")

    evaluator = train_multiple_models(X, y, validation_split=validation_split)

    # Get test split for comparison
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=validation_split, random_state=42, stratify=y
    )

    # Compare on test set
    results = evaluator.compare_models(X_test, y_test)

    logger.info("\n" + "="*60)
    logger.info("Model Comparison Results")
    logger.info("="*60)
    print(results.to_string(index=False))

    # Get best model
    best_name, best_model = evaluator.get_best_model()
    logger.info(f"\nBest model: {best_name}")

    return best_model, results


def main():
    """Main training function."""
    args = parse_args()

    logger.info("Starting model training pipeline...")
    logger.info(f"Configuration:")
    logger.info(f"  Model type: {args.model}")
    logger.info(f"  Samples: {args.samples}")
    logger.info(f"  Validation split: {args.validation_split}")
    logger.info(f"  Random seed: {args.seed}")
    logger.info(f"  Output path: {args.output}")

    # Generate training data
    events, labels = generate_training_data(args.samples, args.seed)
    y = np.array(labels)

    # Extract features
    X, extractor = extract_features(events, args.seed)

    # Train model(s)
    if args.compare or args.model == 'all':
        model, results = compare_models(X, y, args.validation_split)
    else:
        model, metrics = train_single_model(
            args.model, X, y, args.validation_split, args.verbose
        )

    # Save model
    logger.info(f"\nSaving model to {args.output}...")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    model.save_model(args.output)
    logger.info("Model saved successfully!")

    # Register model if requested
    if args.register:
        logger.info(f"\nRegistering model as version {args.register}...")
        registry = ModelRegistry()
        registry.register_model(args.register, model)
        logger.info(f"Model registered successfully!")

    logger.info("\n" + "="*60)
    logger.info("Training pipeline completed successfully!")
    logger.info("="*60)
    logger.info(f"\nModel saved to: {args.output}")
    logger.info(f"Model type: {model.model_type}")
    logger.info(f"Best F1 score: {model.best_score:.4f}")
    logger.info("\nTo use this model:")
    logger.info(f"  from src.ml.models import DisruptionPredictor")
    logger.info(f"  model = DisruptionPredictor()")
    logger.info(f"  model.load_model('{args.output}')")


if __name__ == '__main__':
    main()
