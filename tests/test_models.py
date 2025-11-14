"""
Tests for supply chain data models.
"""
import unittest
from datetime import datetime, timedelta
from src.models.supply_chain import (
    Location, Supplier, Route, Disruption, Alert, ResponsePlan,
    SupplierStatus, DisruptionType, DisruptionSeverity
)


class TestLocation(unittest.TestCase):
    """Test Location model."""
    
    def test_create_location(self):
        """Test location creation."""
        location = Location("USA", "Americas", "New York", 40.7, -74.0)
        self.assertEqual(location.country, "USA")
        self.assertEqual(location.region, "Americas")
        self.assertEqual(location.city, "New York")


class TestSupplier(unittest.TestCase):
    """Test Supplier model."""
    
    def test_create_supplier(self):
        """Test supplier creation."""
        location = Location("China", "Asia", "Shanghai", 31.2, 121.5)
        supplier = Supplier(
            id="SUP-001",
            name="Test Supplier",
            location=location,
            status=SupplierStatus.ACTIVE,
            reliability_score=85.0,
            lead_time_days=30,
            capacity=10000,
            products=["electronics", "components"]
        )
        self.assertEqual(supplier.id, "SUP-001")
        self.assertEqual(len(supplier.products), 2)
        self.assertEqual(supplier.status, SupplierStatus.ACTIVE)
    
    def test_supplier_to_dict(self):
        """Test supplier serialization."""
        location = Location("Germany", "Europe", "Berlin", 52.5, 13.4)
        supplier = Supplier(
            id="SUP-002",
            name="Euro Supplier",
            location=location,
            status=SupplierStatus.ACTIVE,
            reliability_score=90.0,
            lead_time_days=21,
            capacity=8000,
            products=["automotive"]
        )
        data = supplier.to_dict()
        self.assertIn('id', data)
        self.assertIn('location', data)
        self.assertEqual(data['status'], 'active')


class TestDisruption(unittest.TestCase):
    """Test Disruption model."""
    
    def test_create_disruption(self):
        """Test disruption creation."""
        location = Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5)
        disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=location,
            description="Trade restrictions",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=["SUP-001", "SUP-002"],
            affected_routes=["ROUTE-001"],
            predicted_impact_score=75.0,
            source="news"
        )
        self.assertTrue(disruption.is_active())
        self.assertEqual(len(disruption.affected_suppliers), 2)
    
    def test_disruption_ended(self):
        """Test ended disruption."""
        location = Location("USA", "Americas", "Miami", 25.8, -80.2)
        disruption = Disruption(
            id="DISR-002",
            type=DisruptionType.WEATHER,
            severity=DisruptionSeverity.MEDIUM,
            location=location,
            description="Hurricane",
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now() - timedelta(days=1),
            affected_suppliers=[],
            affected_routes=["ROUTE-002"],
            predicted_impact_score=60.0,
            source="weather_api"
        )
        self.assertFalse(disruption.is_active())


class TestAlert(unittest.TestCase):
    """Test Alert model."""
    
    def test_create_alert(self):
        """Test alert creation."""
        alert = Alert(
            id="ALERT-001",
            timestamp=datetime.now(),
            disruption_id="DISR-001",
            severity=DisruptionSeverity.CRITICAL,
            title="Critical Supply Chain Disruption",
            message="Immediate action required",
            recommended_actions=["Action 1", "Action 2"],
            affected_entities={"suppliers": ["SUP-001"], "routes": ["ROUTE-001"]},
            estimated_financial_impact=1000000.0
        )
        self.assertEqual(alert.severity, DisruptionSeverity.CRITICAL)
        self.assertEqual(len(alert.recommended_actions), 2)
        self.assertGreater(alert.estimated_financial_impact, 0)


class TestResponsePlan(unittest.TestCase):
    """Test ResponsePlan model."""
    
    def test_create_response_plan(self):
        """Test response plan creation."""
        plan = ResponsePlan(
            id="PLAN-001",
            disruption_id="DISR-001",
            created_at=datetime.now(),
            priority=5,
            alternative_suppliers=[{"id": "SUP-003", "name": "Alternative"}],
            alternative_routes=[{"id": "ROUTE-003"}],
            inventory_adjustments={"product1": 100},
            estimated_cost=50000.0,
            estimated_time_to_resolve=72,
            confidence_score=85.0
        )
        self.assertEqual(plan.priority, 5)
        self.assertGreater(plan.confidence_score, 0)
        self.assertEqual(len(plan.alternative_suppliers), 1)


if __name__ == '__main__':
    unittest.main()
