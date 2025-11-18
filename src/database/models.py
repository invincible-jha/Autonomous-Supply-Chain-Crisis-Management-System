"""
SQLAlchemy ORM models for persistent storage.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..models.supply_chain import DisruptionSeverity, DisruptionType, SupplierStatus


Base = declarative_base()


class LocationModel(Base):
    """Location database model."""
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    suppliers = relationship("SupplierModel", back_populates="location", foreign_keys="SupplierModel.location_id")
    disruptions = relationship("DisruptionModel", back_populates="location")
    routes_origin = relationship("RouteModel", back_populates="origin", foreign_keys="RouteModel.origin_id")
    routes_destination = relationship("RouteModel", back_populates="destination", foreign_keys="RouteModel.destination_id")

    # Indexes
    __table_args__ = (
        Index('idx_location_coords', 'latitude', 'longitude'),
        Index('idx_location_country_region', 'country', 'region'),
    )

    def __repr__(self):
        return f"<Location(id={self.id}, city={self.city}, country={self.country})>"


class SupplierModel(Base):
    """Supplier database model."""
    __tablename__ = 'suppliers'

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    status = Column(SQLEnum(SupplierStatus), nullable=False, default=SupplierStatus.ACTIVE)
    reliability_score = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    products = Column(JSON, nullable=False)  # List of product names
    risk_factors = Column(JSON, default=list)  # List of risk factors
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("LocationModel", back_populates="suppliers", foreign_keys=[location_id])

    # Indexes
    __table_args__ = (
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_reliability', 'reliability_score'),
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, name={self.name}, status={self.status.value})>"


class RouteModel(Base):
    """Route database model."""
    __tablename__ = 'routes'

    id = Column(String(50), primary_key=True)
    origin_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    transport_mode = Column(String(50), nullable=False)
    distance_km = Column(Float, nullable=False)
    avg_duration_hours = Column(Float, nullable=False)
    cost_per_unit = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    status = Column(String(50), default="operational")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    origin = relationship("LocationModel", back_populates="routes_origin", foreign_keys=[origin_id])
    destination = relationship("LocationModel", back_populates="routes_destination", foreign_keys=[destination_id])

    # Indexes
    __table_args__ = (
        Index('idx_route_origin_dest', 'origin_id', 'destination_id'),
        Index('idx_route_status', 'status'),
    )

    def __repr__(self):
        return f"<Route(id={self.id}, mode={self.transport_mode}, status={self.status})>"


class DisruptionModel(Base):
    """Disruption database model."""
    __tablename__ = 'disruptions'

    id = Column(String(50), primary_key=True)
    type = Column(SQLEnum(DisruptionType), nullable=False)
    severity = Column(SQLEnum(DisruptionSeverity), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    description = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    affected_suppliers = Column(JSON, default=list)  # List of supplier IDs
    affected_routes = Column(JSON, default=list)  # List of route IDs
    predicted_impact_score = Column(Float, nullable=False)
    source = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("LocationModel", back_populates="disruptions")
    alerts = relationship("AlertModel", back_populates="disruption")
    response_plans = relationship("ResponsePlanModel", back_populates="disruption")

    # Indexes
    __table_args__ = (
        Index('idx_disruption_type_severity', 'type', 'severity'),
        Index('idx_disruption_active', 'is_active', 'start_time'),
        Index('idx_disruption_time_range', 'start_time', 'end_time'),
    )

    def __repr__(self):
        return f"<Disruption(id={self.id}, type={self.type.value}, severity={self.severity.value})>"


class AlertModel(Base):
    """Alert database model."""
    __tablename__ = 'alerts'

    id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    disruption_id = Column(String(50), ForeignKey('disruptions.id'), nullable=False)
    severity = Column(SQLEnum(DisruptionSeverity), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    recommended_actions = Column(JSON, nullable=False)  # List of action strings
    affected_entities = Column(JSON, nullable=False)  # Dict of entity types to IDs
    estimated_financial_impact = Column(Float, nullable=False)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    disruption = relationship("DisruptionModel", back_populates="alerts")

    # Indexes
    __table_args__ = (
        Index('idx_alert_severity_time', 'severity', 'timestamp'),
        Index('idx_alert_acknowledged', 'acknowledged'),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, severity={self.severity.value}, title={self.title[:50]})>"


class ResponsePlanModel(Base):
    """Response Plan database model."""
    __tablename__ = 'response_plans'

    id = Column(String(50), primary_key=True)
    disruption_id = Column(String(50), ForeignKey('disruptions.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    priority = Column(Integer, nullable=False)
    alternative_suppliers = Column(JSON, nullable=False)  # List of supplier dicts
    alternative_routes = Column(JSON, nullable=False)  # List of route dicts
    inventory_adjustments = Column(JSON, nullable=False)  # Dict of product to quantity
    estimated_cost = Column(Float, nullable=False)
    estimated_time_to_resolve = Column(Integer, nullable=False)  # in hours
    confidence_score = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, approved, implemented, rejected
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)
    implemented_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    disruption = relationship("DisruptionModel", back_populates="response_plans")

    # Indexes
    __table_args__ = (
        Index('idx_response_plan_priority', 'priority', 'created_at'),
        Index('idx_response_plan_status', 'status'),
    )

    def __repr__(self):
        return f"<ResponsePlan(id={self.id}, priority={self.priority}, status={self.status})>"


class EventModel(Base):
    """Raw event model for intelligence sources."""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=False, index=True)
    location_country = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    location_city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    severity_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Original API response
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_event_source_time', 'source', 'published_at'),
        Index('idx_event_processed', 'processed', 'created_at'),
        Index('idx_event_location', 'location_country', 'location_region'),
    )

    def __repr__(self):
        return f"<Event(id={self.id}, source={self.source}, type={self.event_type})>"
