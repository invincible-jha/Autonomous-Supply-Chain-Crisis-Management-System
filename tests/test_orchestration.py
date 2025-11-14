"""
Tests for crisis orchestration module.
"""
import unittest
from datetime import datetime
from src.orchestration.crisis_orchestrator import (
    AlertGenerator, ResponsePlanner, CrisisOrchestrator
)
from src.analytics.predictive_engine import PredictiveEngine
from src.models.supply_chain import (
    Disruption, Supplier, Route, Location,
    DisruptionType, DisruptionSeverity, SupplierStatus
)


class TestAlertGenerator(unittest.TestCase):
    """Test alert generation."""
    
    def setUp(self):
        """Set up test data."""
        self.generator = AlertGenerator()
        self.location = Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5)
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=self.location,
            description="Trade restrictions",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=["SUP-001"],
            affected_routes=["ROUTE-001"],
            predicted_impact_score=75.0,
            source="news"
        )
    
    def test_should_generate_alert(self):
        """Test alert generation decision."""
        should_alert = self.generator.should_generate_alert(self.disruption)
        self.assertIsInstance(should_alert, bool)
    
    def test_generate_alert(self):
        """Test alert generation."""
        impact = {
            'predicted_duration_hours': 168,
            'financial_impact_usd': 1000000.0,
            'affected_suppliers': ['SUP-001'],
            'cascade_risk_score': 60.0
        }
        supplier = Supplier(
            id="SUP-001",
            name="Test Supplier",
            location=self.location,
            status=SupplierStatus.ACTIVE,
            reliability_score=85.0,
            lead_time_days=30,
            capacity=10000,
            products=["semiconductors"]
        )
        route = Route(
            id="ROUTE-001",
            origin=self.location,
            destination=Location("USA", "Americas", "LA", 34.0, -118.2),
            transport_mode="sea",
            distance_km=11500,
            avg_duration_hours=720,
            cost_per_unit=50.0,
            reliability_score=85.0
        )
        
        alert = self.generator.generate_alert(
            self.disruption, impact, [supplier], [route]
        )
        
        self.assertIsNotNone(alert.id)
        self.assertEqual(alert.severity, DisruptionSeverity.HIGH)
        self.assertGreater(len(alert.recommended_actions), 0)
        self.assertGreater(alert.estimated_financial_impact, 0)


class TestResponsePlanner(unittest.TestCase):
    """Test response planning."""
    
    def setUp(self):
        """Set up test data."""
        self.engine = PredictiveEngine()
        self.planner = ResponsePlanner(self.engine)
        self.location1 = Location("China", "Asia", "Shanghai", 31.2, 121.5)
        self.location2 = Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5)
        
        self.suppliers = [
            Supplier(
                id=f"SUP-{i:03d}",
                name=f"Supplier {i}",
                location=self.location1 if i <= 2 else self.location2,
                status=SupplierStatus.ACTIVE if i > 2 else SupplierStatus.DISRUPTED,
                reliability_score=85.0 if i > 2 else 50.0,
                lead_time_days=30,
                capacity=10000,
                products=["electronics", "semiconductors"]
            ) for i in range(1, 5)
        ]
        
        self.routes = [
            Route(
                id="ROUTE-001",
                origin=self.location1,
                destination=Location("USA", "Americas", "LA", 34.0, -118.2),
                transport_mode="sea",
                distance_km=11500,
                avg_duration_hours=720,
                cost_per_unit=50.0,
                reliability_score=85.0,
                status="disrupted"
            ),
            Route(
                id="ROUTE-002",
                origin=self.location2,
                destination=Location("USA", "Americas", "LA", 34.0, -118.2),
                transport_mode="air",
                distance_km=10500,
                avg_duration_hours=15,
                cost_per_unit=200.0,
                reliability_score=90.0,
                status="operational"
            )
        ]
        
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=self.location1,
            description="Port closure",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[s.id for s in self.suppliers[:2]],
            affected_routes=["ROUTE-001"],
            predicted_impact_score=80.0,
            source="news"
        )
    
    def test_find_alternative_suppliers(self):
        """Test finding alternative suppliers."""
        affected = [s for s in self.suppliers if s.status == SupplierStatus.DISRUPTED]
        alternatives = self.planner.find_alternative_suppliers(
            affected, self.suppliers, ["electronics", "semiconductors"]
        )
        self.assertIsInstance(alternatives, list)
    
    def test_find_alternative_routes(self):
        """Test finding alternative routes."""
        affected = [r for r in self.routes if r.status == "disrupted"]
        alternatives = self.planner.find_alternative_routes(affected, self.routes)
        self.assertIsInstance(alternatives, list)
    
    def test_generate_response_plan(self):
        """Test response plan generation."""
        impact = {
            'predicted_duration_hours': 168,
            'financial_impact_usd': 2000000.0,
            'affected_suppliers': [s.id for s in self.suppliers[:2]]
        }
        
        plan = self.planner.generate_response_plan(
            self.disruption, impact,
            self.suppliers[:2], [self.routes[0]],
            self.suppliers, self.routes
        )
        
        self.assertIsNotNone(plan.id)
        self.assertGreater(plan.priority, 0)
        self.assertGreater(plan.confidence_score, 0)


class TestCrisisOrchestrator(unittest.TestCase):
    """Test crisis orchestration."""
    
    def setUp(self):
        """Set up test data."""
        self.engine = PredictiveEngine()
        self.orchestrator = CrisisOrchestrator(self.engine)
        
        self.location = Location("China", "Asia", "Shanghai", 31.2, 121.5)
        self.suppliers = [
            Supplier(
                id="SUP-001",
                name="Test Supplier",
                location=self.location,
                status=SupplierStatus.ACTIVE,
                reliability_score=85.0,
                lead_time_days=30,
                capacity=10000,
                products=["electronics"]
            )
        ]
        
        self.routes = [
            Route(
                id="ROUTE-001",
                origin=self.location,
                destination=Location("USA", "Americas", "LA", 34.0, -118.2),
                transport_mode="sea",
                distance_km=11500,
                avg_duration_hours=720,
                cost_per_unit=50.0,
                reliability_score=85.0
            )
        ]
        
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.WEATHER,
            severity=DisruptionSeverity.CRITICAL,
            location=self.location,
            description="Typhoon",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[],
            affected_routes=[],
            predicted_impact_score=90.0,
            source="weather"
        )
    
    def test_orchestrate_response(self):
        """Test complete response orchestration."""
        response = self.orchestrator.orchestrate_response(
            self.disruption, self.suppliers, self.routes
        )
        
        self.assertIn('disruption', response)
        self.assertIn('impact_analysis', response)
        self.assertIn('response_plan', response)
        self.assertIsNotNone(response['response_plan'])
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        # Generate some alerts
        self.orchestrator.orchestrate_response(
            self.disruption, self.suppliers, self.routes
        )
        alerts = self.orchestrator.get_active_alerts()
        self.assertIsInstance(alerts, list)
    
    def test_get_response_plans(self):
        """Test getting response plans."""
        self.orchestrator.orchestrate_response(
            self.disruption, self.suppliers, self.routes
        )
        plans = self.orchestrator.get_response_plans()
        self.assertIsInstance(plans, list)
        self.assertGreater(len(plans), 0)


if __name__ == '__main__':
    unittest.main()
