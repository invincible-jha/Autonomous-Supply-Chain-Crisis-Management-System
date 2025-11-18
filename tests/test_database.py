"""
Tests for database models and repositories.
"""
import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, LocationModel, SupplierModel, RouteModel, DisruptionModel, AlertModel, ResponsePlanModel
from src.database.repositories import (
    LocationRepository, SupplierRepository, RouteRepository,
    DisruptionRepository, AlertRepository, ResponsePlanRepository
)
from src.models.supply_chain import (
    Location, Supplier, Route, Disruption, Alert, ResponsePlan,
    DisruptionSeverity, DisruptionType, SupplierStatus
)


class TestDatabase(unittest.TestCase):
    """Test database operations."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Use in-memory SQLite for tests
        cls.engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up test session."""
        self.db = self.SessionLocal()

    def tearDown(self):
        """Clean up test session."""
        self.db.rollback()
        self.db.close()

        # Clear all tables
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

    def test_location_create(self):
        """Test creating a location."""
        location = Location(
            country="United States",
            region="West Coast",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194
        )

        db_location = LocationRepository.create(self.db, location)

        self.assertIsNotNone(db_location.id)
        self.assertEqual(db_location.country, "United States")
        self.assertEqual(db_location.city, "San Francisco")

    def test_location_find_or_create(self):
        """Test find or create location."""
        location = Location(
            country="China",
            region="East Asia",
            city="Shanghai",
            latitude=31.2304,
            longitude=121.4737
        )

        # First call creates
        db_location1 = LocationRepository.find_or_create(self.db, location)
        self.assertIsNotNone(db_location1.id)

        # Second call finds existing
        db_location2 = LocationRepository.find_or_create(self.db, location)
        self.assertEqual(db_location1.id, db_location2.id)

    def test_supplier_create(self):
        """Test creating a supplier."""
        location = Location(
            country="Germany",
            region="Europe",
            city="Munich",
            latitude=48.1351,
            longitude=11.5820
        )

        supplier = Supplier(
            id="SUP001",
            name="German Auto Parts GmbH",
            location=location,
            status=SupplierStatus.ACTIVE,
            reliability_score=85.0,
            lead_time_days=14,
            capacity=10000,
            products=["automotive parts", "electronics"],
            risk_factors=[]
        )

        db_supplier = SupplierRepository.create(self.db, supplier)

        self.assertEqual(db_supplier.id, "SUP001")
        self.assertEqual(db_supplier.name, "German Auto Parts GmbH")
        self.assertEqual(db_supplier.status, SupplierStatus.ACTIVE)
        self.assertIsNotNone(db_supplier.location_id)

    def test_supplier_update_status(self):
        """Test updating supplier status."""
        location = Location(
            country="Japan",
            region="East Asia",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503
        )

        supplier = Supplier(
            id="SUP002",
            name="Tokyo Electronics",
            location=location,
            status=SupplierStatus.ACTIVE,
            reliability_score=90.0,
            lead_time_days=7,
            capacity=50000,
            products=["semiconductors"],
            risk_factors=[]
        )

        db_supplier = SupplierRepository.create(self.db, supplier)
        self.assertEqual(db_supplier.status, SupplierStatus.ACTIVE)

        # Update status
        updated = SupplierRepository.update_status(self.db, "SUP002", SupplierStatus.AT_RISK)
        self.assertEqual(updated.status, SupplierStatus.AT_RISK)

    def test_route_create(self):
        """Test creating a route."""
        origin = Location(
            country="China",
            region="East Asia",
            city="Shanghai",
            latitude=31.2304,
            longitude=121.4737
        )

        destination = Location(
            country="United States",
            region="West Coast",
            city="Los Angeles",
            latitude=34.0522,
            longitude=-118.2437
        )

        route = Route(
            id="ROUTE001",
            origin=origin,
            destination=destination,
            transport_mode="sea",
            distance_km=10000,
            avg_duration_hours=336,
            cost_per_unit=50.0,
            reliability_score=85.0,
            status="operational"
        )

        db_route = RouteRepository.create(self.db, route)

        self.assertEqual(db_route.id, "ROUTE001")
        self.assertEqual(db_route.transport_mode, "sea")
        self.assertIsNotNone(db_route.origin_id)
        self.assertIsNotNone(db_route.destination_id)

    def test_disruption_create(self):
        """Test creating a disruption."""
        location = Location(
            country="Ukraine",
            region="Eastern Europe",
            city="Kyiv",
            latitude=50.4501,
            longitude=30.5234
        )

        disruption = Disruption(
            id="DISR001",
            type=DisruptionType.GEOPOLITICAL,
            severity=DisruptionSeverity.HIGH,
            location=location,
            description="Political unrest affecting supply routes",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=["SUP001", "SUP002"],
            affected_routes=["ROUTE001"],
            predicted_impact_score=75.0,
            source="news"
        )

        db_disruption = DisruptionRepository.create(self.db, disruption)

        self.assertEqual(db_disruption.id, "DISR001")
        self.assertEqual(db_disruption.type, DisruptionType.GEOPOLITICAL)
        self.assertEqual(db_disruption.severity, DisruptionSeverity.HIGH)
        self.assertTrue(db_disruption.is_active)

    def test_alert_create(self):
        """Test creating an alert."""
        # First create a disruption
        location = Location(
            country="Japan",
            region="East Asia",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503
        )

        disruption = Disruption(
            id="DISR002",
            type=DisruptionType.WEATHER,
            severity=DisruptionSeverity.CRITICAL,
            location=location,
            description="Typhoon approaching",
            start_time=datetime.now(),
            end_time=None,
            affected_suppliers=["SUP003"],
            affected_routes=["ROUTE002"],
            predicted_impact_score=90.0,
            source="weather"
        )

        DisruptionRepository.create(self.db, disruption)

        # Create alert
        alert = Alert(
            id="ALERT001",
            timestamp=datetime.now(),
            disruption_id="DISR002",
            severity=DisruptionSeverity.CRITICAL,
            title="Critical Weather Alert",
            message="Typhoon expected to hit Tokyo area",
            recommended_actions=["Activate alternative suppliers", "Increase inventory"],
            affected_entities={"suppliers": ["SUP003"], "routes": ["ROUTE002"]},
            estimated_financial_impact=5000000.0
        )

        db_alert = AlertRepository.create(self.db, alert)

        self.assertEqual(db_alert.id, "ALERT001")
        self.assertEqual(db_alert.disruption_id, "DISR002")
        self.assertFalse(db_alert.acknowledged)

    def test_alert_acknowledge(self):
        """Test acknowledging an alert."""
        # Create disruption and alert
        location = Location(country="Test", region="Test", city="Test", latitude=0.0, longitude=0.0)
        disruption = Disruption(
            id="DISR003", type=DisruptionType.LOGISTICS, severity=DisruptionSeverity.MEDIUM,
            location=location, description="Test", start_time=datetime.now(), end_time=None,
            affected_suppliers=[], affected_routes=[], predicted_impact_score=50.0, source="test"
        )
        DisruptionRepository.create(self.db, disruption)

        alert = Alert(
            id="ALERT002", timestamp=datetime.now(), disruption_id="DISR003",
            severity=DisruptionSeverity.MEDIUM, title="Test Alert", message="Test",
            recommended_actions=[], affected_entities={}, estimated_financial_impact=10000.0
        )
        AlertRepository.create(self.db, alert)

        # Acknowledge
        acknowledged = AlertRepository.acknowledge(self.db, "ALERT002", "test_user")

        self.assertTrue(acknowledged.acknowledged)
        self.assertEqual(acknowledged.acknowledged_by, "test_user")
        self.assertIsNotNone(acknowledged.acknowledged_at)

    def test_response_plan_create(self):
        """Test creating a response plan."""
        # Create disruption
        location = Location(country="Test", region="Test", city="Test", latitude=0.0, longitude=0.0)
        disruption = Disruption(
            id="DISR004", type=DisruptionType.SUPPLIER_FAILURE, severity=DisruptionSeverity.HIGH,
            location=location, description="Test", start_time=datetime.now(), end_time=None,
            affected_suppliers=["SUP001"], affected_routes=[], predicted_impact_score=70.0, source="test"
        )
        DisruptionRepository.create(self.db, disruption)

        # Create response plan
        plan = ResponsePlan(
            id="PLAN001",
            disruption_id="DISR004",
            created_at=datetime.now(),
            priority=5,
            alternative_suppliers=[{"id": "SUP002", "name": "Alt Supplier"}],
            alternative_routes=[{"id": "ROUTE003", "name": "Alt Route"}],
            inventory_adjustments={"product1": 1000},
            estimated_cost=100000.0,
            estimated_time_to_resolve=48,
            confidence_score=85.0
        )

        db_plan = ResponsePlanRepository.create(self.db, plan)

        self.assertEqual(db_plan.id, "PLAN001")
        self.assertEqual(db_plan.disruption_id, "DISR004")
        self.assertEqual(db_plan.priority, 5)
        self.assertEqual(db_plan.status, "pending")

    def test_get_active_disruptions(self):
        """Test getting active disruptions."""
        location = Location(country="Test", region="Test", city="Test", latitude=0.0, longitude=0.0)

        # Create active disruption
        disruption1 = Disruption(
            id="DISR005", type=DisruptionType.WEATHER, severity=DisruptionSeverity.HIGH,
            location=location, description="Active", start_time=datetime.now(), end_time=None,
            affected_suppliers=[], affected_routes=[], predicted_impact_score=80.0, source="test"
        )
        DisruptionRepository.create(self.db, disruption1)

        # Create inactive disruption
        disruption2 = Disruption(
            id="DISR006", type=DisruptionType.WEATHER, severity=DisruptionSeverity.LOW,
            location=location, description="Resolved", start_time=datetime.now(),
            end_time=datetime.now(), affected_suppliers=[], affected_routes=[],
            predicted_impact_score=30.0, source="test"
        )
        db_disr2 = DisruptionRepository.create(self.db, disruption2)
        db_disr2.is_active = False
        self.db.commit()

        # Get active only
        active = DisruptionRepository.get_active(self.db)

        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, "DISR005")


if __name__ == '__main__':
    unittest.main()
