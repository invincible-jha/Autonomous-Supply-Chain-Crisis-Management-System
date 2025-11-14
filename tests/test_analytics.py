"""
Tests for predictive analytics engine.
"""
import unittest
from src.analytics.predictive_engine import (
    RiskScorer, DisruptionPredictor, ImpactAssessor, PredictiveEngine
)
from src.models.supply_chain import (
    Supplier, Route, Disruption, Location,
    SupplierStatus, DisruptionType, DisruptionSeverity
)
from datetime import datetime


class TestRiskScorer(unittest.TestCase):
    """Test risk scoring functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.scorer = RiskScorer()
        self.location = Location("China", "Asia", "Shanghai", 31.2, 121.5)
        self.supplier = Supplier(
            id="SUP-001",
            name="Test Supplier",
            location=self.location,
            status=SupplierStatus.ACTIVE,
            reliability_score=85.0,
            lead_time_days=30,
            capacity=10000,
            products=["electronics"]
        )
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=self.location,
            description="Test disruption",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[],
            affected_routes=[],
            predicted_impact_score=75.0,
            source="test"
        )
    
    def test_calculate_supplier_risk(self):
        """Test supplier risk calculation."""
        risk = self.scorer.calculate_supplier_risk(self.supplier, [self.disruption])
        self.assertGreaterEqual(risk, 0)
        self.assertLessEqual(risk, 100)
    
    def test_calculate_route_risk(self):
        """Test route risk calculation."""
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
        risk = self.scorer.calculate_route_risk(route, [self.disruption])
        self.assertGreaterEqual(risk, 0)
        self.assertLessEqual(risk, 100)


class TestDisruptionPredictor(unittest.TestCase):
    """Test disruption prediction."""
    
    def setUp(self):
        """Set up test data."""
        self.predictor = DisruptionPredictor()
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.WEATHER,
            severity=DisruptionSeverity.MEDIUM,
            location=Location("USA", "Americas", "Miami", 25.8, -80.2),
            description="Hurricane",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[],
            affected_routes=[],
            predicted_impact_score=60.0,
            source="weather"
        )
    
    def test_predict_disruption_probability(self):
        """Test disruption probability prediction."""
        prob = self.predictor.predict_disruption_probability(
            "Eastern Europe", DisruptionType.GEOPOLITICAL
        )
        self.assertGreaterEqual(prob, 0)
        self.assertLessEqual(prob, 1)
    
    def test_predict_disruption_duration(self):
        """Test disruption duration prediction."""
        duration = self.predictor.predict_disruption_duration(self.disruption)
        self.assertGreater(duration, 0)
        self.assertIsInstance(duration, int)


class TestImpactAssessor(unittest.TestCase):
    """Test impact assessment."""
    
    def setUp(self):
        """Set up test data."""
        self.assessor = ImpactAssessor()
        self.location = Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5)
        self.suppliers = [
            Supplier(
                id=f"SUP-{i:03d}",
                name=f"Supplier {i}",
                location=self.location,
                status=SupplierStatus.ACTIVE,
                reliability_score=85.0,
                lead_time_days=30,
                capacity=5000,
                products=["semiconductors"]
            ) for i in range(1, 4)
        ]
        self.disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=self.location,
            description="Trade restrictions",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[s.id for s in self.suppliers],
            affected_routes=[],
            predicted_impact_score=80.0,
            source="news"
        )
    
    def test_calculate_financial_impact(self):
        """Test financial impact calculation."""
        impact = self.assessor.calculate_financial_impact(
            self.disruption, self.suppliers, 168
        )
        self.assertGreater(impact, 0)
    
    def test_calculate_operational_impact(self):
        """Test operational impact calculation."""
        impact = self.assessor.calculate_operational_impact(
            self.disruption, self.suppliers
        )
        self.assertIn('capacity_loss_units', impact)
        self.assertIn('suppliers_affected', impact)
        self.assertEqual(impact['suppliers_affected'], 3)
    
    def test_assess_cascade_risk(self):
        """Test cascade risk assessment."""
        all_suppliers = self.suppliers + [
            Supplier(
                id="SUP-004",
                name="Other Supplier",
                location=Location("Germany", "Europe", "Berlin", 52.5, 13.4),
                status=SupplierStatus.ACTIVE,
                reliability_score=90.0,
                lead_time_days=21,
                capacity=8000,
                products=["automotive"]
            )
        ]
        risk = self.assessor.assess_cascade_risk(self.disruption, all_suppliers)
        self.assertGreaterEqual(risk, 0)
        self.assertLessEqual(risk, 100)


class TestPredictiveEngine(unittest.TestCase):
    """Test main predictive engine."""
    
    def setUp(self):
        """Set up test data."""
        self.engine = PredictiveEngine()
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
        self.disruptions = []
    
    def test_analyze_supply_chain(self):
        """Test supply chain analysis."""
        analysis = self.engine.analyze_supply_chain(
            self.suppliers, self.routes, self.disruptions
        )
        self.assertIn('overall_health_score', analysis)
        self.assertIn('supplier_risks', analysis)
        self.assertIn('route_risks', analysis)
    
    def test_predict_disruption_impact(self):
        """Test disruption impact prediction."""
        disruption = Disruption(
            id="DISR-001",
            type=DisruptionType.WEATHER,
            severity=DisruptionSeverity.MEDIUM,
            location=self.location,
            description="Storm",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=[],
            affected_routes=[],
            predicted_impact_score=50.0,
            source="weather"
        )
        impact = self.engine.predict_disruption_impact(disruption, self.suppliers)
        self.assertIn('predicted_duration_hours', impact)
        self.assertIn('financial_impact_usd', impact)
        self.assertIn('cascade_risk_score', impact)


if __name__ == '__main__':
    unittest.main()
