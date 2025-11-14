"""
Multi-source intelligence synthesis for supply chain monitoring.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random
from ..models.supply_chain import (
    Disruption, DisruptionType, DisruptionSeverity, Location
)


class IntelligenceSource:
    """Base class for intelligence sources."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_update = None
    
    def fetch_data(self) -> List[Dict]:
        """Fetch data from the source."""
        raise NotImplementedError


class GeopoliticalMonitor(IntelligenceSource):
    """Monitor geopolitical events affecting supply chains."""
    
    def __init__(self):
        super().__init__("Geopolitical Monitor")
        self.risk_regions = [
            "Eastern Europe", "Middle East", "South China Sea",
            "Taiwan Strait", "Korean Peninsula"
        ]
    
    def fetch_data(self) -> List[Dict]:
        """Simulate fetching geopolitical intelligence."""
        events = []
        
        # Simulate detection of geopolitical events
        risk_keywords = [
            "trade sanctions", "border closure", "export restrictions",
            "military tensions", "political unrest", "embargo"
        ]
        
        # In a real system, this would query news APIs, government feeds, etc.
        # For now, simulate some events
        if random.random() < 0.3:  # 30% chance of detecting an event
            events.append({
                'source': self.name,
                'type': 'geopolitical',
                'severity': random.choice(['medium', 'high', 'critical']),
                'region': random.choice(self.risk_regions),
                'description': f"Trade restrictions detected in {random.choice(self.risk_regions)}",
                'timestamp': datetime.now().isoformat(),
                'confidence': random.uniform(0.6, 0.95)
            })
        
        self.last_update = datetime.now()
        return events


class WeatherMonitor(IntelligenceSource):
    """Monitor weather and natural disasters."""
    
    def __init__(self):
        super().__init__("Weather Monitor")
        self.monitored_regions = [
            "Asia-Pacific", "Americas", "Europe", "Middle East", "Africa"
        ]
    
    def fetch_data(self) -> List[Dict]:
        """Simulate fetching weather and disaster data."""
        events = []
        
        weather_events = [
            "hurricane", "typhoon", "flooding", "earthquake",
            "severe storm", "drought", "wildfire"
        ]
        
        # In a real system, this would integrate with weather APIs
        if random.random() < 0.2:  # 20% chance
            events.append({
                'source': self.name,
                'type': 'weather',
                'severity': random.choice(['low', 'medium', 'high']),
                'region': random.choice(self.monitored_regions),
                'event_type': random.choice(weather_events),
                'description': f"{random.choice(weather_events).capitalize()} warning",
                'timestamp': datetime.now().isoformat(),
                'confidence': random.uniform(0.7, 0.99)
            })
        
        self.last_update = datetime.now()
        return events


class SupplierMonitor(IntelligenceSource):
    """Monitor supplier health and performance."""
    
    def __init__(self):
        super().__init__("Supplier Monitor")
    
    def fetch_data(self) -> List[Dict]:
        """Simulate fetching supplier status data."""
        events = []
        
        # In a real system, this would integrate with supplier APIs, IoT sensors, etc.
        if random.random() < 0.15:  # 15% chance
            events.append({
                'source': self.name,
                'type': 'supplier_failure',
                'severity': random.choice(['medium', 'high']),
                'description': "Supplier performance degradation detected",
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'on_time_delivery': random.uniform(0.5, 0.8),
                    'quality_score': random.uniform(0.6, 0.85),
                    'capacity_utilization': random.uniform(0.8, 1.0)
                },
                'confidence': random.uniform(0.8, 0.95)
            })
        
        self.last_update = datetime.now()
        return events


class LogisticsMonitor(IntelligenceSource):
    """Monitor logistics and transportation networks."""
    
    def __init__(self):
        super().__init__("Logistics Monitor")
    
    def fetch_data(self) -> List[Dict]:
        """Simulate fetching logistics data."""
        events = []
        
        issues = [
            "port congestion", "route closure", "transportation delay",
            "customs delay", "capacity shortage"
        ]
        
        # In a real system, integrate with shipping APIs, traffic data, etc.
        if random.random() < 0.25:  # 25% chance
            events.append({
                'source': self.name,
                'type': 'logistics',
                'severity': random.choice(['low', 'medium', 'high']),
                'description': random.choice(issues),
                'timestamp': datetime.now().isoformat(),
                'estimated_delay_hours': random.randint(12, 168),
                'confidence': random.uniform(0.75, 0.95)
            })
        
        self.last_update = datetime.now()
        return events


class IntelligenceSynthesizer:
    """Synthesize intelligence from multiple sources."""
    
    def __init__(self):
        self.sources = [
            GeopoliticalMonitor(),
            WeatherMonitor(),
            SupplierMonitor(),
            LogisticsMonitor()
        ]
        self.raw_events = []
        self.synthesized_disruptions = []
    
    def collect_intelligence(self) -> List[Dict]:
        """Collect data from all intelligence sources."""
        all_events = []
        
        for source in self.sources:
            try:
                events = source.fetch_data()
                all_events.extend(events)
            except Exception as e:
                print(f"Error fetching from {source.name}: {e}")
        
        self.raw_events = all_events
        return all_events
    
    def synthesize_disruptions(self, events: List[Dict]) -> List[Disruption]:
        """
        Synthesize raw intelligence into actionable disruption objects.
        Apply correlation, deduplication, and enrichment.
        """
        disruptions = []
        
        for event in events:
            # Map severity
            severity_map = {
                'low': DisruptionSeverity.LOW,
                'medium': DisruptionSeverity.MEDIUM,
                'high': DisruptionSeverity.HIGH,
                'critical': DisruptionSeverity.CRITICAL
            }
            severity = severity_map.get(event.get('severity', 'medium'), 
                                       DisruptionSeverity.MEDIUM)
            
            # Map type
            type_map = {
                'geopolitical': DisruptionType.GEOPOLITICAL,
                'weather': DisruptionType.WEATHER,
                'supplier_failure': DisruptionType.SUPPLIER_FAILURE,
                'logistics': DisruptionType.LOGISTICS
            }
            disruption_type = type_map.get(event.get('type', 'logistics'), 
                                          DisruptionType.LOGISTICS)
            
            # Create location (simplified)
            location = Location(
                country="Unknown",
                region=event.get('region', 'Unknown'),
                city="",
                latitude=0.0,
                longitude=0.0
            )
            
            # Calculate impact score based on severity and confidence
            confidence = event.get('confidence', 0.75)
            base_impact = {
                DisruptionSeverity.LOW: 25,
                DisruptionSeverity.MEDIUM: 50,
                DisruptionSeverity.HIGH: 75,
                DisruptionSeverity.CRITICAL: 95
            }
            impact_score = base_impact[severity] * confidence
            
            disruption = Disruption(
                id=f"DISR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
                type=disruption_type,
                severity=severity,
                location=location,
                description=event.get('description', 'Supply chain disruption detected'),
                start_time=datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')),
                end_time=None,
                affected_suppliers=[],
                affected_routes=[],
                predicted_impact_score=impact_score,
                source=event.get('source', 'Unknown')
            )
            
            disruptions.append(disruption)
        
        self.synthesized_disruptions = disruptions
        return disruptions
    
    def get_active_disruptions(self) -> List[Disruption]:
        """Get all currently active disruptions."""
        return [d for d in self.synthesized_disruptions if d.is_active()]
    
    def run_intelligence_cycle(self) -> List[Disruption]:
        """Run a complete intelligence collection and synthesis cycle."""
        events = self.collect_intelligence()
        disruptions = self.synthesize_disruptions(events)
        return disruptions
