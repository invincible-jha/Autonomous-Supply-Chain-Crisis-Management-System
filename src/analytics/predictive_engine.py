"""
Predictive analytics engine for supply chain risk assessment.
"""
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime, timedelta
from ..models.supply_chain import (
    Supplier, Route, Disruption, DisruptionSeverity, 
    DisruptionType, SupplierStatus
)


class RiskScorer:
    """Calculate risk scores for supply chain entities."""
    
    def __init__(self):
        self.risk_weights = {
            'geopolitical': 0.25,
            'weather': 0.20,
            'supplier_reliability': 0.25,
            'route_reliability': 0.15,
            'geographic_concentration': 0.15
        }
    
    def calculate_supplier_risk(self, supplier: Supplier, 
                                disruptions: List[Disruption]) -> float:
        """
        Calculate risk score for a supplier (0-100).
        Higher score = higher risk.
        """
        risk_score = 0.0
        
        # Base risk from reliability score (inverse)
        reliability_risk = (100 - supplier.reliability_score) * 0.3
        risk_score += reliability_risk
        
        # Risk from location-based disruptions
        location_risk = 0.0
        for disruption in disruptions:
            if disruption.is_active():
                if disruption.location.region == supplier.location.region:
                    severity_multiplier = {
                        DisruptionSeverity.LOW: 0.1,
                        DisruptionSeverity.MEDIUM: 0.25,
                        DisruptionSeverity.HIGH: 0.5,
                        DisruptionSeverity.CRITICAL: 1.0
                    }
                    location_risk += 20 * severity_multiplier[disruption.severity]
        
        risk_score += min(location_risk, 40)  # Cap location risk at 40
        
        # Risk from status
        status_risk = {
            SupplierStatus.ACTIVE: 0,
            SupplierStatus.AT_RISK: 15,
            SupplierStatus.DISRUPTED: 40,
            SupplierStatus.OFFLINE: 100
        }
        risk_score += status_risk[supplier.status]
        
        # Risk from known risk factors
        risk_score += min(len(supplier.risk_factors) * 5, 20)
        
        return min(risk_score, 100.0)
    
    def calculate_route_risk(self, route: Route, 
                            disruptions: List[Disruption]) -> float:
        """
        Calculate risk score for a route (0-100).
        """
        risk_score = 0.0
        
        # Base risk from reliability
        reliability_risk = (100 - route.reliability_score) * 0.3
        risk_score += reliability_risk
        
        # Risk from disruptions affecting origin or destination
        location_risk = 0.0
        for disruption in disruptions:
            if disruption.is_active():
                if (disruption.location.region == route.origin.region or 
                    disruption.location.region == route.destination.region):
                    severity_multiplier = {
                        DisruptionSeverity.LOW: 0.1,
                        DisruptionSeverity.MEDIUM: 0.25,
                        DisruptionSeverity.HIGH: 0.5,
                        DisruptionSeverity.CRITICAL: 0.8
                    }
                    location_risk += 25 * severity_multiplier[disruption.severity]
        
        risk_score += min(location_risk, 50)
        
        # Status risk
        if route.status != "operational":
            risk_score += 30
        
        return min(risk_score, 100.0)


class DisruptionPredictor:
    """Predict future disruptions and their impacts."""
    
    def __init__(self):
        self.historical_patterns = {}
        self.prediction_window_days = 14
    
    def predict_disruption_probability(self, location: str, 
                                     disruption_type: DisruptionType,
                                     lookback_days: int = 90) -> float:
        """
        Predict probability of disruption in a location.
        Returns probability (0-1).
        """
        # In a real system, this would use ML models trained on historical data
        # For now, use a simplified heuristic approach
        
        base_probabilities = {
            DisruptionType.GEOPOLITICAL: 0.15,
            DisruptionType.WEATHER: 0.20,
            DisruptionType.SUPPLIER_FAILURE: 0.10,
            DisruptionType.LOGISTICS: 0.25,
            DisruptionType.DEMAND_SPIKE: 0.08,
            DisruptionType.QUALITY_ISSUE: 0.05
        }
        
        base_prob = base_probabilities.get(disruption_type, 0.1)
        
        # Adjust based on location risk (simplified)
        high_risk_regions = ["Eastern Europe", "Middle East", "South China Sea"]
        if any(region in location for region in high_risk_regions):
            base_prob *= 1.5
        
        return min(base_prob, 1.0)
    
    def predict_disruption_duration(self, disruption: Disruption) -> int:
        """
        Predict duration of a disruption in hours.
        """
        # Base durations by type
        base_durations = {
            DisruptionType.GEOPOLITICAL: 720,  # 30 days
            DisruptionType.WEATHER: 168,  # 7 days
            DisruptionType.SUPPLIER_FAILURE: 336,  # 14 days
            DisruptionType.LOGISTICS: 72,  # 3 days
            DisruptionType.DEMAND_SPIKE: 240,  # 10 days
            DisruptionType.QUALITY_ISSUE: 480  # 20 days
        }
        
        base_duration = base_durations.get(disruption.type, 168)
        
        # Adjust by severity
        severity_multipliers = {
            DisruptionSeverity.LOW: 0.5,
            DisruptionSeverity.MEDIUM: 1.0,
            DisruptionSeverity.HIGH: 1.5,
            DisruptionSeverity.CRITICAL: 2.5
        }
        
        predicted_duration = int(base_duration * 
                               severity_multipliers[disruption.severity])
        
        return predicted_duration


class ImpactAssessor:
    """Assess financial and operational impact of disruptions."""
    
    def __init__(self):
        self.base_cost_per_day = {
            DisruptionSeverity.LOW: 50000,
            DisruptionSeverity.MEDIUM: 200000,
            DisruptionSeverity.HIGH: 1000000,
            DisruptionSeverity.CRITICAL: 5000000
        }
    
    def calculate_financial_impact(self, disruption: Disruption,
                                   affected_suppliers: List[Supplier],
                                   duration_hours: int) -> float:
        """
        Calculate estimated financial impact in USD.
        """
        base_daily_cost = self.base_cost_per_day[disruption.severity]
        duration_days = duration_hours / 24.0
        
        # Base cost
        total_impact = base_daily_cost * duration_days
        
        # Multiply by number of affected suppliers
        supplier_multiplier = 1 + (len(affected_suppliers) * 0.2)
        total_impact *= supplier_multiplier
        
        # Adjust by predicted impact score
        impact_multiplier = disruption.predicted_impact_score / 100.0
        total_impact *= impact_multiplier
        
        return total_impact
    
    def calculate_operational_impact(self, disruption: Disruption,
                                    affected_suppliers: List[Supplier]) -> Dict:
        """
        Calculate operational impact metrics.
        """
        total_capacity_loss = sum(s.capacity for s in affected_suppliers)
        avg_lead_time_increase = np.mean([s.lead_time_days for s in affected_suppliers]) * 1.5
        
        return {
            'capacity_loss_units': total_capacity_loss,
            'lead_time_increase_days': avg_lead_time_increase,
            'suppliers_affected': len(affected_suppliers),
            'products_at_risk': len(set(p for s in affected_suppliers 
                                       for p in s.products))
        }
    
    def assess_cascade_risk(self, disruption: Disruption,
                          suppliers: List[Supplier]) -> float:
        """
        Assess risk of cascade effects (0-100).
        """
        # Calculate based on network concentration
        affected_count = len([s for s in suppliers 
                            if s.location.region == disruption.location.region])
        
        concentration_ratio = affected_count / max(len(suppliers), 1)
        
        # Base cascade risk
        cascade_risk = concentration_ratio * 50
        
        # Amplify by severity
        severity_amplifier = {
            DisruptionSeverity.LOW: 1.0,
            DisruptionSeverity.MEDIUM: 1.3,
            DisruptionSeverity.HIGH: 1.7,
            DisruptionSeverity.CRITICAL: 2.5
        }
        
        cascade_risk *= severity_amplifier[disruption.severity]
        
        return min(cascade_risk, 100.0)


class PredictiveEngine:
    """Main predictive analytics engine."""
    
    def __init__(self):
        self.risk_scorer = RiskScorer()
        self.predictor = DisruptionPredictor()
        self.impact_assessor = ImpactAssessor()
    
    def analyze_supply_chain(self, suppliers: List[Supplier],
                           routes: List[Route],
                           disruptions: List[Disruption]) -> Dict:
        """
        Comprehensive supply chain analysis.
        """
        # Calculate risk scores
        supplier_risks = {
            s.id: self.risk_scorer.calculate_supplier_risk(s, disruptions)
            for s in suppliers
        }
        
        route_risks = {
            r.id: self.risk_scorer.calculate_route_risk(r, disruptions)
            for r in routes
        }
        
        # Identify high-risk entities
        high_risk_suppliers = [
            s.id for s, risk in zip(suppliers, supplier_risks.values())
            if risk > 60
        ]
        
        high_risk_routes = [
            r.id for r, risk in zip(routes, route_risks.values())
            if risk > 60
        ]
        
        # Calculate overall supply chain health
        avg_supplier_risk = np.mean(list(supplier_risks.values())) if supplier_risks else 0
        avg_route_risk = np.mean(list(route_risks.values())) if route_risks else 0
        overall_health = 100 - (avg_supplier_risk * 0.6 + avg_route_risk * 0.4)
        
        return {
            'overall_health_score': overall_health,
            'supplier_risks': supplier_risks,
            'route_risks': route_risks,
            'high_risk_suppliers': high_risk_suppliers,
            'high_risk_routes': high_risk_routes,
            'active_disruptions': len([d for d in disruptions if d.is_active()]),
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_disruption_impact(self, disruption: Disruption,
                                 suppliers: List[Supplier]) -> Dict:
        """
        Predict the full impact of a disruption.
        """
        # Predict duration
        predicted_duration = self.predictor.predict_disruption_duration(disruption)
        
        # Identify affected suppliers
        affected_suppliers = [
            s for s in suppliers 
            if s.location.region == disruption.location.region
        ]
        
        # Calculate financial impact
        financial_impact = self.impact_assessor.calculate_financial_impact(
            disruption, affected_suppliers, predicted_duration
        )
        
        # Calculate operational impact
        operational_impact = self.impact_assessor.calculate_operational_impact(
            disruption, affected_suppliers
        )
        
        # Assess cascade risk
        cascade_risk = self.impact_assessor.assess_cascade_risk(
            disruption, suppliers
        )
        
        return {
            'disruption_id': disruption.id,
            'predicted_duration_hours': predicted_duration,
            'financial_impact_usd': financial_impact,
            'operational_impact': operational_impact,
            'cascade_risk_score': cascade_risk,
            'affected_suppliers': [s.id for s in affected_suppliers],
            'confidence': 0.75  # Simplified confidence score
        }
