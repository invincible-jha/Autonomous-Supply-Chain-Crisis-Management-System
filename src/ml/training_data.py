"""
Training data generation for ML models.

Generates synthetic historical data for initial model training before
real historical data accumulates.
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import random
from faker import Faker
import logging

from ..models.supply_chain import DisruptionSeverity, DisruptionType, SupplierStatus

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """
    Generate synthetic training data for disruption prediction models.

    Creates realistic event-disruption pairs with proper labels for training.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize training data generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)

    def generate_events(self, n_events: int = 1000) -> List[Dict[str, Any]]:
        """
        Generate synthetic events.

        Args:
            n_events: Number of events to generate

        Returns:
            List of event dictionaries
        """
        events = []

        # Event type probabilities (based on realistic distribution)
        event_types = ['geopolitical', 'weather', 'supplier_failure', 'logistics']
        event_type_probs = [0.2, 0.3, 0.25, 0.25]

        # High-risk regions
        high_risk_countries = [
            'Ukraine', 'Russia', 'Iran', 'China', 'Taiwan', 'North Korea',
            'Syria', 'Yemen', 'Venezuela', 'Myanmar', 'Afghanistan'
        ]

        normal_countries = [
            'United States', 'Germany', 'Japan', 'United Kingdom', 'France',
            'Canada', 'Australia', 'South Korea', 'Singapore', 'Netherlands',
            'Italy', 'Spain', 'Brazil', 'Mexico', 'India', 'Indonesia'
        ]

        sources = ['newsapi', 'openweathermap', 'manual', 'sensor']

        for i in range(n_events):
            # Choose event type
            event_type = np.random.choice(event_types, p=event_type_probs)

            # Choose location (bias towards high-risk for certain event types)
            if event_type == 'geopolitical' and random.random() < 0.6:
                country = random.choice(high_risk_countries)
            else:
                country = random.choice(normal_countries)

            # Published time (spread over last 180 days)
            days_ago = random.randint(0, 180)
            published_at = datetime.now() - timedelta(days=days_ago)

            # Severity score (higher for certain conditions)
            base_severity = random.uniform(10, 90)

            # Increase severity for high-risk locations
            if country in high_risk_countries:
                base_severity = min(100, base_severity + random.uniform(10, 30))

            # Increase severity for certain event types
            if event_type == 'geopolitical':
                base_severity = min(100, base_severity + random.uniform(5, 15))

            severity_score = base_severity

            # Confidence score (correlated with source)
            if event_type == 'weather':
                confidence_score = random.uniform(0.8, 0.95)
            elif event_type == 'geopolitical':
                confidence_score = random.uniform(0.6, 0.85)
            else:
                confidence_score = random.uniform(0.5, 0.8)

            # Determine source
            if event_type == 'weather':
                source = 'openweathermap'
            elif event_type == 'geopolitical':
                source = 'newsapi'
            else:
                source = random.choice(sources)

            # Generate title and description
            title = self._generate_title(event_type, country, severity_score)
            description = self._generate_description(event_type, country, severity_score)

            event = {
                'event_id': f'synth_event_{i:06d}',
                'source': source,
                'event_type': event_type,
                'title': title,
                'description': description,
                'url': f'https://example.com/event/{i}',
                'published_at': published_at,
                'location_country': country,
                'location_region': self._get_region(country),
                'location_city': self.fake.city(),
                'latitude': self.fake.latitude(),
                'longitude': self.fake.longitude(),
                'severity_score': severity_score,
                'confidence_score': confidence_score,
                'processed': False
            }

            events.append(event)

        logger.info(f"Generated {len(events)} synthetic events")
        return events

    def generate_labeled_data(self,
                             n_samples: int = 1000,
                             disruption_probability: float = 0.3) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Generate labeled training data (events + labels).

        Args:
            n_samples: Number of samples to generate
            disruption_probability: Probability of an event causing disruption

        Returns:
            Tuple of (events list, labels list) where label is 1 for disruption, 0 for no disruption
        """
        events = self.generate_events(n_samples)
        labels = []

        for event in events:
            # Determine if event causes disruption based on characteristics
            disruption_prob = self._calculate_disruption_probability(event)

            # Binary label: 1 = disruption, 0 = no disruption
            label = 1 if random.random() < disruption_prob else 0
            labels.append(label)

        # Ensure we have balanced classes (adjust if needed)
        disruption_rate = sum(labels) / len(labels)
        logger.info(f"Generated {n_samples} labeled samples. Disruption rate: {disruption_rate:.2%}")

        return events, labels

    def generate_multi_class_labels(self,
                                    n_samples: int = 1000) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Generate multi-class labeled data for severity prediction.

        Args:
            n_samples: Number of samples to generate

        Returns:
            Tuple of (events, severity labels) where label is 0-3 (LOW, MEDIUM, HIGH, CRITICAL)
        """
        events = self.generate_events(n_samples)
        labels = []

        for event in events:
            # Determine severity based on event characteristics
            severity = self._calculate_severity_label(event)
            labels.append(severity)

        severity_dist = [labels.count(i) for i in range(4)]
        logger.info(f"Generated {n_samples} samples. Severity distribution: {severity_dist}")

        return events, labels

    def generate_suppliers(self, n_suppliers: int = 50) -> List[Dict[str, Any]]:
        """Generate synthetic supplier data."""
        suppliers = []

        countries = [
            'China', 'United States', 'Germany', 'Japan', 'South Korea',
            'Taiwan', 'Vietnam', 'India', 'Mexico', 'Thailand'
        ]

        for i in range(n_suppliers):
            country = random.choice(countries)

            supplier = {
                'id': f'SUP{i:04d}',
                'name': f'{self.fake.company()} Ltd',
                'location': {
                    'country': country,
                    'region': self._get_region(country),
                    'city': self.fake.city(),
                    'latitude': self.fake.latitude(),
                    'longitude': self.fake.longitude()
                },
                'status': random.choice(['active', 'active', 'active', 'at_risk']),  # Bias towards active
                'reliability_score': random.uniform(60, 95),
                'lead_time_days': random.randint(7, 90),
                'capacity': random.randint(1000, 100000),
                'products': [self.fake.bs() for _ in range(random.randint(1, 5))],
                'risk_factors': []
            }

            # Add risk factors for some suppliers
            if random.random() < 0.3:
                risk_factors = random.sample([
                    'single_source', 'high_lead_time', 'financial_risk',
                    'quality_issues', 'geopolitical_risk', 'capacity_constraints'
                ], random.randint(1, 3))
                supplier['risk_factors'] = risk_factors

            suppliers.append(supplier)

        return suppliers

    def generate_routes(self, n_routes: int = 30) -> List[Dict[str, Any]]:
        """Generate synthetic route data."""
        routes = []

        major_ports = [
            ('Shanghai', 'China', 31.2304, 121.4737),
            ('Singapore', 'Singapore', 1.3521, 103.8198),
            ('Los Angeles', 'United States', 34.0522, -118.2437),
            ('Rotterdam', 'Netherlands', 51.9225, 4.4792),
            ('Hamburg', 'Germany', 53.5511, 9.9937),
            ('Tokyo', 'Japan', 35.6762, 139.6503),
        ]

        transport_modes = ['sea', 'air', 'land', 'rail']

        for i in range(n_routes):
            origin = random.choice(major_ports)
            destination = random.choice([p for p in major_ports if p != origin])

            # Calculate approximate distance (simplified)
            distance = random.uniform(1000, 15000)

            # Calculate duration based on mode and distance
            mode = random.choice(transport_modes)
            if mode == 'air':
                duration = distance / 800  # ~800 km/h
            elif mode == 'sea':
                duration = distance / 40  # ~40 km/h
            elif mode == 'rail':
                duration = distance / 80  # ~80 km/h
            else:  # land
                duration = distance / 60  # ~60 km/h

            route = {
                'id': f'ROUTE{i:04d}',
                'origin': {
                    'country': origin[1],
                    'region': self._get_region(origin[1]),
                    'city': origin[0],
                    'latitude': origin[2],
                    'longitude': origin[3]
                },
                'destination': {
                    'country': destination[1],
                    'region': self._get_region(destination[1]),
                    'city': destination[0],
                    'latitude': destination[2],
                    'longitude': destination[3]
                },
                'transport_mode': mode,
                'distance_km': distance,
                'avg_duration_hours': duration,
                'cost_per_unit': random.uniform(5, 100),
                'reliability_score': random.uniform(70, 95),
                'status': 'operational'
            }

            routes.append(route)

        return routes

    def _calculate_disruption_probability(self, event: Dict[str, Any]) -> float:
        """Calculate probability that an event causes a disruption."""
        base_prob = 0.2  # Base 20% probability

        # Increase probability based on severity
        severity = event.get('severity_score', 50)
        if severity > 80:
            base_prob += 0.4
        elif severity > 60:
            base_prob += 0.3
        elif severity > 40:
            base_prob += 0.15

        # Increase for high-risk locations
        country = event.get('location_country', '')
        high_risk_countries = ['Ukraine', 'Russia', 'Iran', 'China', 'Taiwan', 'North Korea']
        if country in high_risk_countries:
            base_prob += 0.2

        # Increase for certain event types
        event_type = event.get('event_type', '')
        if event_type in ['geopolitical', 'weather']:
            base_prob += 0.1

        # Decrease for low confidence
        confidence = event.get('confidence_score', 0.5)
        if confidence < 0.6:
            base_prob *= 0.8

        return min(0.95, base_prob)

    def _calculate_severity_label(self, event: Dict[str, Any]) -> int:
        """Calculate severity label (0-3) based on event characteristics."""
        severity_score = event.get('severity_score', 50)

        # Map continuous score to discrete severity
        if severity_score >= 80:
            return 3  # CRITICAL
        elif severity_score >= 60:
            return 2  # HIGH
        elif severity_score >= 35:
            return 1  # MEDIUM
        else:
            return 0  # LOW

    def _generate_title(self, event_type: str, country: str, severity: float) -> str:
        """Generate event title."""
        if event_type == 'geopolitical':
            if severity > 70:
                templates = [
                    f"Breaking: Major Political Crisis in {country}",
                    f"Trade Restrictions Imposed on {country}",
                    f"Emergency: Border Closure in {country}",
                    f"Sanctions Announced Against {country}"
                ]
            else:
                templates = [
                    f"Political Tensions Rise in {country}",
                    f"Trade Negotiations Stalled with {country}",
                    f"Supply Chain Concerns in {country}",
                    f"Regulatory Changes in {country}"
                ]
        elif event_type == 'weather':
            if severity > 70:
                templates = [
                    f"Severe Storm Hits {country}",
                    f"Hurricane Warning Issued for {country}",
                    f"Flooding Emergency in {country}",
                    f"Typhoon Approaching {country}"
                ]
            else:
                templates = [
                    f"Weather Advisory for {country}",
                    f"Heavy Rain Expected in {country}",
                    f"Wind Warning for {country}",
                    f"Snow Forecast in {country}"
                ]
        elif event_type == 'supplier_failure':
            templates = [
                f"Supplier Issues Reported in {country}",
                f"Production Delays in {country}",
                f"Quality Concerns in {country}",
                f"Capacity Shortage in {country}"
            ]
        else:  # logistics
            templates = [
                f"Port Congestion in {country}",
                f"Transportation Delays in {country}",
                f"Logistics Disruption in {country}",
                f"Shipping Route Closure near {country}"
            ]

        return random.choice(templates)

    def _generate_description(self, event_type: str, country: str, severity: float) -> str:
        """Generate event description."""
        severity_words = ['minor', 'moderate', 'significant', 'severe', 'critical']
        severity_idx = min(4, int(severity / 20))
        severity_word = severity_words[severity_idx]

        base = f"A {severity_word} {event_type} event has been detected in {country}. "

        if event_type == 'geopolitical':
            base += "This may impact supply chain operations and international trade. "
        elif event_type == 'weather':
            base += "Adverse weather conditions may affect transportation and logistics. "
        elif event_type == 'supplier_failure':
            base += "Supplier operations may be impacted, leading to potential delays. "
        else:
            base += "Transportation and logistics networks may experience disruptions. "

        base += f"Confidence level: {random.randint(60, 95)}%"

        return base

    def _get_region(self, country: str) -> str:
        """Get region for country."""
        region_map = {
            'United States': 'North America',
            'Canada': 'North America',
            'Mexico': 'North America',
            'China': 'East Asia',
            'Japan': 'East Asia',
            'South Korea': 'East Asia',
            'Taiwan': 'East Asia',
            'North Korea': 'East Asia',
            'Germany': 'Europe',
            'United Kingdom': 'Europe',
            'France': 'Europe',
            'Italy': 'Europe',
            'Spain': 'Europe',
            'Netherlands': 'Europe',
            'Russia': 'Eastern Europe',
            'Ukraine': 'Eastern Europe',
            'India': 'South Asia',
            'Singapore': 'Southeast Asia',
            'Thailand': 'Southeast Asia',
            'Vietnam': 'Southeast Asia',
            'Indonesia': 'Southeast Asia',
            'Myanmar': 'Southeast Asia',
            'Iran': 'Middle East',
            'Syria': 'Middle East',
            'Yemen': 'Middle East',
            'Australia': 'Oceania',
            'Brazil': 'South America',
            'Venezuela': 'South America',
            'Afghanistan': 'Central Asia'
        }
        return region_map.get(country, 'Other')
