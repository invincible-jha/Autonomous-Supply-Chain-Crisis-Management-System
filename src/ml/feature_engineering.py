"""
Feature engineering for disruption prediction models.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import logging
import re

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract features from events, suppliers, and routes for ML models.

    Features include:
    - Event characteristics (type, severity, frequency)
    - Temporal patterns (time of day, day of week, seasonality)
    - Geographic patterns (country, region)
    - Text features (keyword presence, sentiment indicators)
    - Historical patterns (past disruption frequency)
    - Network features (affected suppliers/routes count)
    """

    # High severity keywords for text analysis
    HIGH_SEVERITY_KEYWORDS = [
        'war', 'crisis', 'emergency', 'critical', 'shutdown', 'collapse',
        'catastrophe', 'disaster', 'devastation', 'closure', 'blockade',
        'attack', 'conflict', 'violence', 'destruction', 'severe'
    ]

    MEDIUM_SEVERITY_KEYWORDS = [
        'disruption', 'delay', 'shortage', 'strike', 'protest', 'conflict',
        'suspension', 'restriction', 'ban', 'sanction', 'embargo', 'issue',
        'problem', 'challenge', 'concern', 'risk'
    ]

    # High-risk regions
    HIGH_RISK_REGIONS = [
        'Eastern Europe', 'Middle East', 'East Asia', 'South China Sea',
        'Taiwan Strait', 'Korean Peninsula', 'Persian Gulf'
    ]

    HIGH_RISK_COUNTRIES = [
        'Ukraine', 'Russia', 'Belarus', 'Iran', 'Iraq', 'Syria', 'Yemen',
        'North Korea', 'Myanmar', 'Afghanistan', 'Venezuela'
    ]

    def __init__(self):
        """Initialize feature extractor."""
        self.feature_names = []

    def extract_event_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from a single event.

        Args:
            event: Event dictionary from database

        Returns:
            Dictionary of features
        """
        features = {}

        # Basic event features
        features['event_source'] = self._encode_source(event.get('source', 'unknown'))
        features['event_type'] = self._encode_event_type(event.get('event_type', 'unknown'))
        features['severity_score'] = event.get('severity_score', 0.0)
        features['confidence_score'] = event.get('confidence_score', 0.5)

        # Temporal features
        published_at = event.get('published_at')
        if published_at:
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

            features['hour_of_day'] = published_at.hour
            features['day_of_week'] = published_at.weekday()
            features['day_of_month'] = published_at.day
            features['month'] = published_at.month
            features['is_weekend'] = 1 if published_at.weekday() >= 5 else 0
            features['is_business_hours'] = 1 if 9 <= published_at.hour <= 17 else 0
        else:
            features['hour_of_day'] = 0
            features['day_of_week'] = 0
            features['day_of_month'] = 0
            features['month'] = 0
            features['is_weekend'] = 0
            features['is_business_hours'] = 0

        # Geographic features
        country = event.get('location_country', '')
        region = event.get('location_region', '')

        features['is_high_risk_country'] = 1 if country in self.HIGH_RISK_COUNTRIES else 0
        features['is_high_risk_region'] = 1 if region in self.HIGH_RISK_REGIONS else 0
        features['has_location'] = 1 if country else 0

        # Geographic coordinates (if available)
        features['latitude'] = event.get('latitude', 0.0) or 0.0
        features['longitude'] = event.get('longitude', 0.0) or 0.0

        # Text features
        title = event.get('title', '')
        description = event.get('description', '')
        text = f"{title} {description}".lower()

        features.update(self._extract_text_features(text))

        return features

    def extract_supplier_features(self, supplier: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from supplier data.

        Args:
            supplier: Supplier dictionary

        Returns:
            Dictionary of features
        """
        features = {}

        features['supplier_reliability'] = supplier.get('reliability_score', 50.0)
        features['supplier_lead_time'] = supplier.get('lead_time_days', 30)
        features['supplier_capacity'] = supplier.get('capacity', 1000)
        features['supplier_status'] = self._encode_supplier_status(supplier.get('status', 'active'))

        # Risk factors count
        risk_factors = supplier.get('risk_factors', [])
        features['supplier_risk_factor_count'] = len(risk_factors) if risk_factors else 0

        # Product diversity
        products = supplier.get('products', [])
        features['supplier_product_count'] = len(products) if products else 1

        # Location risk
        location = supplier.get('location', {})
        if isinstance(location, dict):
            country = location.get('country', '')
            region = location.get('region', '')
            features['supplier_high_risk_location'] = 1 if (
                country in self.HIGH_RISK_COUNTRIES or region in self.HIGH_RISK_REGIONS
            ) else 0
        else:
            features['supplier_high_risk_location'] = 0

        return features

    def extract_route_features(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from route data.

        Args:
            route: Route dictionary

        Returns:
            Dictionary of features
        """
        features = {}

        features['route_distance'] = route.get('distance_km', 1000)
        features['route_duration'] = route.get('avg_duration_hours', 48)
        features['route_cost'] = route.get('cost_per_unit', 10.0)
        features['route_reliability'] = route.get('reliability_score', 75.0)
        features['route_mode'] = self._encode_transport_mode(route.get('transport_mode', 'sea'))

        return features

    def extract_historical_features(self,
                                    location_country: Optional[str],
                                    historical_disruptions: List[Dict[str, Any]],
                                    lookback_days: int = 90) -> Dict[str, Any]:
        """
        Extract historical disruption patterns as features.

        Args:
            location_country: Country to analyze
            historical_disruptions: List of past disruptions
            lookback_days: Days to look back

        Returns:
            Dictionary of historical features
        """
        features = {}

        if not historical_disruptions:
            # No historical data
            features['hist_disruption_count'] = 0
            features['hist_high_severity_count'] = 0
            features['hist_avg_severity'] = 0.0
            features['hist_days_since_last'] = lookback_days
            features['hist_disruption_rate'] = 0.0
            return features

        # Filter to relevant time window
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_disruptions = [
            d for d in historical_disruptions
            if d.get('start_time') and
               (isinstance(d['start_time'], datetime) and d['start_time'] >= cutoff_date or
                isinstance(d['start_time'], str) and datetime.fromisoformat(d['start_time'].replace('Z', '+00:00')) >= cutoff_date)
        ]

        # Count metrics
        features['hist_disruption_count'] = len(recent_disruptions)

        # Severity analysis
        severities = []
        for d in recent_disruptions:
            sev = d.get('severity')
            if sev:
                # Convert enum to value if needed
                sev_val = sev.value if hasattr(sev, 'value') else sev
                if isinstance(sev_val, int):
                    severities.append(sev_val)

        if severities:
            features['hist_high_severity_count'] = sum(1 for s in severities if s >= 3)  # HIGH or CRITICAL
            features['hist_avg_severity'] = np.mean(severities)
        else:
            features['hist_high_severity_count'] = 0
            features['hist_avg_severity'] = 0.0

        # Time since last disruption
        if recent_disruptions:
            last_times = []
            for d in recent_disruptions:
                start_time = d.get('start_time')
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    last_times.append(start_time)

            if last_times:
                days_since_last = (datetime.now() - max(last_times)).days
                features['hist_days_since_last'] = max(0, days_since_last)
            else:
                features['hist_days_since_last'] = lookback_days
        else:
            features['hist_days_since_last'] = lookback_days

        # Disruption rate (disruptions per week)
        features['hist_disruption_rate'] = len(recent_disruptions) / (lookback_days / 7.0)

        return features

    def extract_network_features(self,
                                 affected_suppliers: List[str],
                                 affected_routes: List[str],
                                 total_suppliers: int = 100,
                                 total_routes: int = 50) -> Dict[str, Any]:
        """
        Extract network-level features.

        Args:
            affected_suppliers: List of affected supplier IDs
            affected_routes: List of affected route IDs
            total_suppliers: Total number of suppliers in network
            total_routes: Total number of routes in network

        Returns:
            Dictionary of network features
        """
        features = {}

        affected_supplier_count = len(affected_suppliers) if affected_suppliers else 0
        affected_route_count = len(affected_routes) if affected_routes else 0

        features['affected_supplier_count'] = affected_supplier_count
        features['affected_route_count'] = affected_route_count
        features['affected_supplier_ratio'] = affected_supplier_count / max(1, total_suppliers)
        features['affected_route_ratio'] = affected_route_count / max(1, total_routes)

        # Network impact score
        features['network_impact_score'] = (
            features['affected_supplier_ratio'] * 0.6 +
            features['affected_route_ratio'] * 0.4
        ) * 100

        return features

    def create_feature_vector(self,
                            event: Dict[str, Any],
                            supplier: Optional[Dict[str, Any]] = None,
                            route: Optional[Dict[str, Any]] = None,
                            historical_disruptions: Optional[List[Dict[str, Any]]] = None,
                            network_stats: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Create complete feature vector for an event.

        Args:
            event: Event dictionary
            supplier: Optional supplier context
            route: Optional route context
            historical_disruptions: Optional historical disruptions
            network_stats: Optional network statistics

        Returns:
            Feature vector as numpy array
        """
        all_features = {}

        # Extract event features
        all_features.update(self.extract_event_features(event))

        # Extract supplier features if available
        if supplier:
            all_features.update(self.extract_supplier_features(supplier))
        else:
            # Default supplier features
            all_features.update({
                'supplier_reliability': 75.0,
                'supplier_lead_time': 30,
                'supplier_capacity': 1000,
                'supplier_status': 0,
                'supplier_risk_factor_count': 0,
                'supplier_product_count': 1,
                'supplier_high_risk_location': 0
            })

        # Extract route features if available
        if route:
            all_features.update(self.extract_route_features(route))
        else:
            # Default route features
            all_features.update({
                'route_distance': 1000,
                'route_duration': 48,
                'route_cost': 10.0,
                'route_reliability': 75.0,
                'route_mode': 0
            })

        # Extract historical features
        if historical_disruptions is not None:
            location_country = event.get('location_country')
            all_features.update(self.extract_historical_features(
                location_country, historical_disruptions
            ))
        else:
            # Default historical features
            all_features.update({
                'hist_disruption_count': 0,
                'hist_high_severity_count': 0,
                'hist_avg_severity': 0.0,
                'hist_days_since_last': 90,
                'hist_disruption_rate': 0.0
            })

        # Extract network features
        if network_stats:
            all_features.update(self.extract_network_features(
                event.get('affected_suppliers', []),
                event.get('affected_routes', []),
                network_stats.get('total_suppliers', 100),
                network_stats.get('total_routes', 50)
            ))
        else:
            # Default network features
            all_features.update({
                'affected_supplier_count': 0,
                'affected_route_count': 0,
                'affected_supplier_ratio': 0.0,
                'affected_route_ratio': 0.0,
                'network_impact_score': 0.0
            })

        # Store feature names for reference
        if not self.feature_names:
            self.feature_names = sorted(all_features.keys())

        # Convert to numpy array in consistent order
        feature_vector = np.array([all_features[name] for name in self.feature_names])

        return feature_vector

    def _extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract features from text content."""
        features = {}

        # Keyword presence
        high_sev_count = sum(1 for keyword in self.HIGH_SEVERITY_KEYWORDS if keyword in text)
        med_sev_count = sum(1 for keyword in self.MEDIUM_SEVERITY_KEYWORDS if keyword in text)

        features['text_high_severity_keywords'] = high_sev_count
        features['text_medium_severity_keywords'] = med_sev_count
        features['text_total_keywords'] = high_sev_count + med_sev_count

        # Text length
        features['text_length'] = len(text)
        features['text_word_count'] = len(text.split())

        # Specific indicators
        features['text_has_number'] = 1 if re.search(r'\d', text) else 0
        features['text_has_money'] = 1 if any(symbol in text for symbol in ['$', '€', '£', 'usd', 'eur']) else 0
        features['text_has_percent'] = 1 if '%' in text or 'percent' in text else 0

        # Urgency indicators
        urgency_words = ['urgent', 'immediate', 'emergency', 'critical', 'now', 'alert']
        features['text_urgency_score'] = sum(1 for word in urgency_words if word in text)

        return features

    def _encode_source(self, source: str) -> int:
        """Encode event source as integer."""
        source_map = {
            'newsapi': 1,
            'openweathermap': 2,
            'openweathermap_alert': 3,
            'manual': 4,
            'sensor': 5,
            'unknown': 0
        }
        return source_map.get(source.lower(), 0)

    def _encode_event_type(self, event_type: str) -> int:
        """Encode event type as integer."""
        type_map = {
            'geopolitical': 1,
            'weather': 2,
            'supplier_failure': 3,
            'logistics': 4,
            'demand_spike': 5,
            'quality_issue': 6,
            'unknown': 0
        }
        return type_map.get(event_type.lower(), 0)

    def _encode_supplier_status(self, status: str) -> int:
        """Encode supplier status as integer."""
        status_map = {
            'active': 0,
            'at_risk': 1,
            'disrupted': 2,
            'offline': 3
        }
        if hasattr(status, 'value'):
            status = status.value
        return status_map.get(str(status).lower(), 0)

    def _encode_transport_mode(self, mode: str) -> int:
        """Encode transport mode as integer."""
        mode_map = {
            'air': 1,
            'sea': 2,
            'land': 3,
            'rail': 4,
            'multimodal': 5
        }
        return mode_map.get(mode.lower(), 0)

    def get_feature_names(self) -> List[str]:
        """Get list of feature names in order."""
        return self.feature_names

    def batch_extract_features(self,
                              events: List[Dict[str, Any]],
                              suppliers_map: Optional[Dict[str, Dict]] = None,
                              routes_map: Optional[Dict[str, Dict]] = None,
                              historical_disruptions: Optional[List[Dict[str, Any]]] = None,
                              network_stats: Optional[Dict[str, int]] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Extract features for multiple events in batch.

        Args:
            events: List of event dictionaries
            suppliers_map: Map of supplier_id -> supplier dict
            routes_map: Map of route_id -> route dict
            historical_disruptions: Historical disruptions for all events
            network_stats: Network statistics

        Returns:
            Tuple of (feature matrix, event IDs)
        """
        feature_vectors = []
        event_ids = []

        for event in events:
            try:
                # Get related entities
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

                # Extract features
                feature_vector = self.create_feature_vector(
                    event=event,
                    supplier=supplier,
                    route=route,
                    historical_disruptions=historical_disruptions,
                    network_stats=network_stats
                )

                feature_vectors.append(feature_vector)
                event_ids.append(event.get('event_id', event.get('id')))

            except Exception as e:
                logger.error(f"Error extracting features for event {event.get('id')}: {e}")
                continue

        if feature_vectors:
            feature_matrix = np.vstack(feature_vectors)
        else:
            feature_matrix = np.array([])

        return feature_matrix, event_ids
