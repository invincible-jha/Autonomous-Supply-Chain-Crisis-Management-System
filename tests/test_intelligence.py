"""
Tests for intelligence synthesis module.
"""
import unittest
from src.intelligence.synthesizer import (
    GeopoliticalMonitor, WeatherMonitor, SupplierMonitor,
    LogisticsMonitor, IntelligenceSynthesizer
)
from src.models.supply_chain import DisruptionType, DisruptionSeverity


class TestIntelligenceSources(unittest.TestCase):
    """Test intelligence source monitors."""
    
    def test_geopolitical_monitor(self):
        """Test geopolitical monitoring."""
        monitor = GeopoliticalMonitor()
        self.assertEqual(monitor.name, "Geopolitical Monitor")
        events = monitor.fetch_data()
        self.assertIsInstance(events, list)
        # Check event structure if any events generated
        for event in events:
            self.assertIn('source', event)
            self.assertIn('type', event)
    
    def test_weather_monitor(self):
        """Test weather monitoring."""
        monitor = WeatherMonitor()
        self.assertEqual(monitor.name, "Weather Monitor")
        events = monitor.fetch_data()
        self.assertIsInstance(events, list)
        self.assertIsNotNone(monitor.last_update)
    
    def test_supplier_monitor(self):
        """Test supplier monitoring."""
        monitor = SupplierMonitor()
        events = monitor.fetch_data()
        self.assertIsInstance(events, list)
    
    def test_logistics_monitor(self):
        """Test logistics monitoring."""
        monitor = LogisticsMonitor()
        events = monitor.fetch_data()
        self.assertIsInstance(events, list)


class TestIntelligenceSynthesizer(unittest.TestCase):
    """Test intelligence synthesizer."""
    
    def test_create_synthesizer(self):
        """Test synthesizer creation."""
        synthesizer = IntelligenceSynthesizer()
        self.assertEqual(len(synthesizer.sources), 4)
    
    def test_collect_intelligence(self):
        """Test intelligence collection."""
        synthesizer = IntelligenceSynthesizer()
        events = synthesizer.collect_intelligence()
        self.assertIsInstance(events, list)
    
    def test_synthesize_disruptions(self):
        """Test disruption synthesis."""
        synthesizer = IntelligenceSynthesizer()
        # Create mock events
        mock_events = [
            {
                'source': 'Test',
                'type': 'geopolitical',
                'severity': 'high',
                'region': 'Test Region',
                'description': 'Test disruption',
                'timestamp': '2024-01-01T00:00:00',
                'confidence': 0.85
            }
        ]
        disruptions = synthesizer.synthesize_disruptions(mock_events)
        self.assertEqual(len(disruptions), 1)
        self.assertEqual(disruptions[0].type, DisruptionType.GEOPOLITICAL)
        self.assertEqual(disruptions[0].severity, DisruptionSeverity.HIGH)
    
    def test_run_intelligence_cycle(self):
        """Test complete intelligence cycle."""
        synthesizer = IntelligenceSynthesizer()
        disruptions = synthesizer.run_intelligence_cycle()
        self.assertIsInstance(disruptions, list)
        # All disruptions should be active when just created
        for disruption in disruptions:
            self.assertTrue(disruption.is_active())
    
    def test_get_active_disruptions(self):
        """Test getting active disruptions."""
        synthesizer = IntelligenceSynthesizer()
        synthesizer.run_intelligence_cycle()
        active = synthesizer.get_active_disruptions()
        self.assertIsInstance(active, list)


if __name__ == '__main__':
    unittest.main()
