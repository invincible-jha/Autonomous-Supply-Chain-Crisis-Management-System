"""
Repository layer for database CRUD operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime

from .models import (
    LocationModel, SupplierModel, RouteModel, DisruptionModel,
    AlertModel, ResponsePlanModel, EventModel
)
from ..models.supply_chain import (
    Location, Supplier, Route, Disruption, Alert, ResponsePlan,
    DisruptionSeverity, DisruptionType, SupplierStatus
)


class LocationRepository:
    """Repository for Location operations."""

    @staticmethod
    def create(db: Session, location: Location) -> LocationModel:
        """Create a new location."""
        db_location = LocationModel(
            country=location.country,
            region=location.region,
            city=location.city,
            latitude=location.latitude,
            longitude=location.longitude
        )
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location

    @staticmethod
    def get_by_id(db: Session, location_id: int) -> Optional[LocationModel]:
        """Get location by ID."""
        return db.query(LocationModel).filter(LocationModel.id == location_id).first()

    @staticmethod
    def get_by_coordinates(db: Session, latitude: float, longitude: float, tolerance: float = 0.1) -> Optional[LocationModel]:
        """Get location by coordinates with tolerance."""
        return db.query(LocationModel).filter(
            and_(
                LocationModel.latitude.between(latitude - tolerance, latitude + tolerance),
                LocationModel.longitude.between(longitude - tolerance, longitude + tolerance)
            )
        ).first()

    @staticmethod
    def get_by_country(db: Session, country: str) -> List[LocationModel]:
        """Get all locations in a country."""
        return db.query(LocationModel).filter(LocationModel.country == country).all()

    @staticmethod
    def find_or_create(db: Session, location: Location) -> LocationModel:
        """Find existing location or create new one."""
        existing = LocationRepository.get_by_coordinates(
            db, location.latitude, location.longitude
        )
        if existing:
            return existing
        return LocationRepository.create(db, location)


class SupplierRepository:
    """Repository for Supplier operations."""

    @staticmethod
    def create(db: Session, supplier: Supplier) -> SupplierModel:
        """Create a new supplier."""
        # Find or create location
        location = LocationRepository.find_or_create(db, supplier.location)

        db_supplier = SupplierModel(
            id=supplier.id,
            name=supplier.name,
            location_id=location.id,
            status=supplier.status,
            reliability_score=supplier.reliability_score,
            lead_time_days=supplier.lead_time_days,
            capacity=supplier.capacity,
            products=supplier.products,
            risk_factors=supplier.risk_factors
        )
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        return db_supplier

    @staticmethod
    def get_by_id(db: Session, supplier_id: str) -> Optional[SupplierModel]:
        """Get supplier by ID."""
        return db.query(SupplierModel).filter(SupplierModel.id == supplier_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[SupplierModel]:
        """Get all suppliers with pagination."""
        return db.query(SupplierModel).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_status(db: Session, status: SupplierStatus) -> List[SupplierModel]:
        """Get suppliers by status."""
        return db.query(SupplierModel).filter(SupplierModel.status == status).all()

    @staticmethod
    def update_status(db: Session, supplier_id: str, status: SupplierStatus) -> Optional[SupplierModel]:
        """Update supplier status."""
        supplier = SupplierRepository.get_by_id(db, supplier_id)
        if supplier:
            supplier.status = status
            supplier.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(supplier)
        return supplier

    @staticmethod
    def update_reliability(db: Session, supplier_id: str, reliability_score: float) -> Optional[SupplierModel]:
        """Update supplier reliability score."""
        supplier = SupplierRepository.get_by_id(db, supplier_id)
        if supplier:
            supplier.reliability_score = reliability_score
            supplier.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(supplier)
        return supplier


class RouteRepository:
    """Repository for Route operations."""

    @staticmethod
    def create(db: Session, route: Route) -> RouteModel:
        """Create a new route."""
        origin = LocationRepository.find_or_create(db, route.origin)
        destination = LocationRepository.find_or_create(db, route.destination)

        db_route = RouteModel(
            id=route.id,
            origin_id=origin.id,
            destination_id=destination.id,
            transport_mode=route.transport_mode,
            distance_km=route.distance_km,
            avg_duration_hours=route.avg_duration_hours,
            cost_per_unit=route.cost_per_unit,
            reliability_score=route.reliability_score,
            status=route.status
        )
        db.add(db_route)
        db.commit()
        db.refresh(db_route)
        return db_route

    @staticmethod
    def get_by_id(db: Session, route_id: str) -> Optional[RouteModel]:
        """Get route by ID."""
        return db.query(RouteModel).filter(RouteModel.id == route_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[RouteModel]:
        """Get all routes with pagination."""
        return db.query(RouteModel).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_location(db: Session, location_id: int, is_origin: bool = True) -> List[RouteModel]:
        """Get routes by origin or destination location."""
        if is_origin:
            return db.query(RouteModel).filter(RouteModel.origin_id == location_id).all()
        return db.query(RouteModel).filter(RouteModel.destination_id == location_id).all()


class DisruptionRepository:
    """Repository for Disruption operations."""

    @staticmethod
    def create(db: Session, disruption: Disruption) -> DisruptionModel:
        """Create a new disruption."""
        location = LocationRepository.find_or_create(db, disruption.location)

        db_disruption = DisruptionModel(
            id=disruption.id,
            type=disruption.type,
            severity=disruption.severity,
            location_id=location.id,
            description=disruption.description,
            start_time=disruption.start_time,
            end_time=disruption.end_time,
            affected_suppliers=disruption.affected_suppliers,
            affected_routes=disruption.affected_routes,
            predicted_impact_score=disruption.predicted_impact_score,
            source=disruption.source,
            is_active=disruption.is_active()
        )
        db.add(db_disruption)
        db.commit()
        db.refresh(db_disruption)
        return db_disruption

    @staticmethod
    def get_by_id(db: Session, disruption_id: str) -> Optional[DisruptionModel]:
        """Get disruption by ID."""
        return db.query(DisruptionModel).filter(DisruptionModel.id == disruption_id).first()

    @staticmethod
    def get_active(db: Session, skip: int = 0, limit: int = 100) -> List[DisruptionModel]:
        """Get active disruptions."""
        return db.query(DisruptionModel).filter(
            DisruptionModel.is_active == True
        ).order_by(desc(DisruptionModel.start_time)).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_severity(db: Session, severity: DisruptionSeverity) -> List[DisruptionModel]:
        """Get disruptions by severity."""
        return db.query(DisruptionModel).filter(
            DisruptionModel.severity == severity
        ).order_by(desc(DisruptionModel.start_time)).all()

    @staticmethod
    def get_by_type(db: Session, disruption_type: DisruptionType) -> List[DisruptionModel]:
        """Get disruptions by type."""
        return db.query(DisruptionModel).filter(
            DisruptionModel.type == disruption_type
        ).order_by(desc(DisruptionModel.start_time)).all()

    @staticmethod
    def update_end_time(db: Session, disruption_id: str, end_time: datetime) -> Optional[DisruptionModel]:
        """Update disruption end time and mark as inactive."""
        disruption = DisruptionRepository.get_by_id(db, disruption_id)
        if disruption:
            disruption.end_time = end_time
            disruption.is_active = False
            disruption.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(disruption)
        return disruption


class AlertRepository:
    """Repository for Alert operations."""

    @staticmethod
    def create(db: Session, alert: Alert) -> AlertModel:
        """Create a new alert."""
        db_alert = AlertModel(
            id=alert.id,
            timestamp=alert.timestamp,
            disruption_id=alert.disruption_id,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            recommended_actions=alert.recommended_actions,
            affected_entities=alert.affected_entities,
            estimated_financial_impact=alert.estimated_financial_impact
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert

    @staticmethod
    def get_by_id(db: Session, alert_id: str) -> Optional[AlertModel]:
        """Get alert by ID."""
        return db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    @staticmethod
    def get_recent(db: Session, hours: int = 24, skip: int = 0, limit: int = 100) -> List[AlertModel]:
        """Get recent alerts within specified hours."""
        cutoff_time = datetime.utcnow()
        from datetime import timedelta
        cutoff_time = cutoff_time - timedelta(hours=hours)

        return db.query(AlertModel).filter(
            AlertModel.timestamp >= cutoff_time
        ).order_by(desc(AlertModel.timestamp)).offset(skip).limit(limit).all()

    @staticmethod
    def get_unacknowledged(db: Session, skip: int = 0, limit: int = 100) -> List[AlertModel]:
        """Get unacknowledged alerts."""
        return db.query(AlertModel).filter(
            AlertModel.acknowledged == False
        ).order_by(desc(AlertModel.timestamp)).offset(skip).limit(limit).all()

    @staticmethod
    def acknowledge(db: Session, alert_id: str, acknowledged_by: str) -> Optional[AlertModel]:
        """Acknowledge an alert."""
        alert = AlertRepository.get_by_id(db, alert_id)
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            db.commit()
            db.refresh(alert)
        return alert


class ResponsePlanRepository:
    """Repository for Response Plan operations."""

    @staticmethod
    def create(db: Session, plan: ResponsePlan) -> ResponsePlanModel:
        """Create a new response plan."""
        db_plan = ResponsePlanModel(
            id=plan.id,
            disruption_id=plan.disruption_id,
            created_at=plan.created_at,
            priority=plan.priority,
            alternative_suppliers=plan.alternative_suppliers,
            alternative_routes=plan.alternative_routes,
            inventory_adjustments=plan.inventory_adjustments,
            estimated_cost=plan.estimated_cost,
            estimated_time_to_resolve=plan.estimated_time_to_resolve,
            confidence_score=plan.confidence_score
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan

    @staticmethod
    def get_by_id(db: Session, plan_id: str) -> Optional[ResponsePlanModel]:
        """Get response plan by ID."""
        return db.query(ResponsePlanModel).filter(ResponsePlanModel.id == plan_id).first()

    @staticmethod
    def get_by_disruption(db: Session, disruption_id: str) -> List[ResponsePlanModel]:
        """Get all response plans for a disruption."""
        return db.query(ResponsePlanModel).filter(
            ResponsePlanModel.disruption_id == disruption_id
        ).order_by(desc(ResponsePlanModel.priority)).all()

    @staticmethod
    def get_pending(db: Session, skip: int = 0, limit: int = 100) -> List[ResponsePlanModel]:
        """Get pending response plans."""
        return db.query(ResponsePlanModel).filter(
            ResponsePlanModel.status == "pending"
        ).order_by(desc(ResponsePlanModel.priority), desc(ResponsePlanModel.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def approve(db: Session, plan_id: str, approved_by: str) -> Optional[ResponsePlanModel]:
        """Approve a response plan."""
        plan = ResponsePlanRepository.get_by_id(db, plan_id)
        if plan:
            plan.status = "approved"
            plan.approved_at = datetime.utcnow()
            plan.approved_by = approved_by
            plan.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(plan)
        return plan

    @staticmethod
    def implement(db: Session, plan_id: str) -> Optional[ResponsePlanModel]:
        """Mark response plan as implemented."""
        plan = ResponsePlanRepository.get_by_id(db, plan_id)
        if plan:
            plan.status = "implemented"
            plan.implemented_at = datetime.utcnow()
            plan.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(plan)
        return plan


class EventRepository:
    """Repository for raw Event operations."""

    @staticmethod
    def create(db: Session, event_data: Dict[str, Any]) -> EventModel:
        """Create a new event."""
        db_event = EventModel(**event_data)
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    @staticmethod
    def get_by_event_id(db: Session, event_id: str) -> Optional[EventModel]:
        """Get event by event ID."""
        return db.query(EventModel).filter(EventModel.event_id == event_id).first()

    @staticmethod
    def get_unprocessed(db: Session, source: Optional[str] = None, limit: int = 100) -> List[EventModel]:
        """Get unprocessed events."""
        query = db.query(EventModel).filter(EventModel.processed == False)
        if source:
            query = query.filter(EventModel.source == source)
        return query.order_by(EventModel.published_at).limit(limit).all()

    @staticmethod
    def mark_processed(db: Session, event_id: int) -> Optional[EventModel]:
        """Mark event as processed."""
        event = db.query(EventModel).filter(EventModel.id == event_id).first()
        if event:
            event.processed = True
            db.commit()
            db.refresh(event)
        return event

    @staticmethod
    def bulk_create(db: Session, events: List[Dict[str, Any]]) -> int:
        """Bulk create events. Returns count of created events."""
        count = 0
        for event_data in events:
            # Check if event already exists
            existing = EventRepository.get_by_event_id(db, event_data['event_id'])
            if not existing:
                db_event = EventModel(**event_data)
                db.add(db_event)
                count += 1

        db.commit()
        return count
