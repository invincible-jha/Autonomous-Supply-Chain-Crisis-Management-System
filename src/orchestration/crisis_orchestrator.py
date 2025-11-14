"""
Automated crisis response orchestration system.
"""
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from ..models.supply_chain import (
    Disruption, Supplier, Route, Alert, ResponsePlan,
    DisruptionSeverity, SupplierStatus
)
from ..analytics.predictive_engine import PredictiveEngine


class AlertGenerator:
    """Generate alerts for supply chain disruptions."""
    
    def __init__(self):
        self.alert_thresholds = {
            DisruptionSeverity.LOW: 30,
            DisruptionSeverity.MEDIUM: 50,
            DisruptionSeverity.HIGH: 70,
            DisruptionSeverity.CRITICAL: 85
        }
    
    def should_generate_alert(self, disruption: Disruption) -> bool:
        """Determine if an alert should be generated."""
        threshold = self.alert_thresholds[disruption.severity]
        return disruption.predicted_impact_score >= threshold
    
    def generate_alert(self, disruption: Disruption,
                      impact_analysis: Dict,
                      affected_suppliers: List[Supplier],
                      affected_routes: List[Route]) -> Alert:
        """Generate a crisis alert."""
        alert_id = f"ALERT-{uuid.uuid4().hex[:12].upper()}"
        
        # Build recommended actions based on severity
        recommended_actions = self._generate_recommendations(
            disruption, impact_analysis, affected_suppliers
        )
        
        # Compile affected entities
        affected_entities = {
            'suppliers': [s.id for s in affected_suppliers],
            'routes': [r.id for r in affected_routes],
            'products': list(set(p for s in affected_suppliers for p in s.products))
        }
        
        # Create alert message
        title = self._generate_alert_title(disruption)
        message = self._generate_alert_message(disruption, impact_analysis)
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            disruption_id=disruption.id,
            severity=disruption.severity,
            title=title,
            message=message,
            recommended_actions=recommended_actions,
            affected_entities=affected_entities,
            estimated_financial_impact=impact_analysis.get('financial_impact_usd', 0)
        )
        
        return alert
    
    def _generate_alert_title(self, disruption: Disruption) -> str:
        """Generate alert title."""
        severity_prefix = {
            DisruptionSeverity.LOW: "⚠️ Low Priority",
            DisruptionSeverity.MEDIUM: "⚠️ Medium Priority",
            DisruptionSeverity.HIGH: "🔴 High Priority",
            DisruptionSeverity.CRITICAL: "🚨 CRITICAL"
        }
        
        return f"{severity_prefix[disruption.severity]}: {disruption.type.value.replace('_', ' ').title()} - {disruption.location.region}"
    
    def _generate_alert_message(self, disruption: Disruption,
                               impact_analysis: Dict) -> str:
        """Generate detailed alert message."""
        duration = impact_analysis.get('predicted_duration_hours', 0)
        financial = impact_analysis.get('financial_impact_usd', 0)
        
        message = f"""
Supply chain disruption detected:

Type: {disruption.type.value.replace('_', ' ').title()}
Location: {disruption.location.region}
Severity: {disruption.severity.name}
Description: {disruption.description}

Predicted Impact:
- Duration: {duration} hours ({duration/24:.1f} days)
- Financial Impact: ${financial:,.0f}
- Affected Suppliers: {len(impact_analysis.get('affected_suppliers', []))}
- Cascade Risk: {impact_analysis.get('cascade_risk_score', 0):.1f}/100

Status: Active monitoring and response plan generation initiated.
        """.strip()
        
        return message
    
    def _generate_recommendations(self, disruption: Disruption,
                                 impact_analysis: Dict,
                                 affected_suppliers: List[Supplier]) -> List[str]:
        """Generate recommended actions."""
        recommendations = []
        
        # Priority 1: Immediate assessment
        recommendations.append("Activate crisis management team immediately")
        recommendations.append("Assess current inventory levels for affected products")
        
        # Priority 2: Communication
        recommendations.append("Notify key stakeholders and customers of potential delays")
        recommendations.append("Establish direct communication with affected suppliers")
        
        # Priority 3: Mitigation
        if disruption.severity in [DisruptionSeverity.HIGH, DisruptionSeverity.CRITICAL]:
            recommendations.append("Activate alternative suppliers from response plan")
            recommendations.append("Expedite shipments from unaffected regions")
            recommendations.append("Consider air freight for critical components")
        
        # Priority 4: Operational adjustments
        recommendations.append("Review and adjust production schedules")
        recommendations.append("Increase safety stock for affected products")
        
        # Priority 5: Monitoring
        recommendations.append("Implement enhanced monitoring for cascade effects")
        recommendations.append("Schedule daily disruption status reviews")
        
        return recommendations


class ResponsePlanner:
    """Generate automated response plans for disruptions."""
    
    def __init__(self, predictive_engine: PredictiveEngine):
        self.predictive_engine = predictive_engine
    
    def find_alternative_suppliers(self, affected_suppliers: List[Supplier],
                                  all_suppliers: List[Supplier],
                                  required_products: List[str]) -> List[Dict]:
        """Find alternative suppliers for affected products."""
        alternatives = []
        
        # Get unaffected suppliers
        affected_ids = {s.id for s in affected_suppliers}
        available_suppliers = [s for s in all_suppliers 
                              if s.id not in affected_ids 
                              and s.status == SupplierStatus.ACTIVE]
        
        # Match by products
        for product in required_products:
            matching_suppliers = [
                s for s in available_suppliers 
                if product in s.products
            ]
            
            # Sort by reliability
            matching_suppliers.sort(key=lambda s: s.reliability_score, reverse=True)
            
            if matching_suppliers:
                best_supplier = matching_suppliers[0]
                alternatives.append({
                    'product': product,
                    'supplier_id': best_supplier.id,
                    'supplier_name': best_supplier.name,
                    'reliability_score': best_supplier.reliability_score,
                    'lead_time_days': best_supplier.lead_time_days,
                    'capacity': best_supplier.capacity,
                    'location': f"{best_supplier.location.city}, {best_supplier.location.country}"
                })
        
        return alternatives
    
    def find_alternative_routes(self, affected_routes: List[Route],
                               all_routes: List[Route]) -> List[Dict]:
        """Find alternative routes for disrupted logistics."""
        alternatives = []
        
        affected_ids = {r.id for r in affected_routes}
        available_routes = [r for r in all_routes 
                          if r.id not in affected_ids 
                          and r.status == "operational"]
        
        # Group by origin-destination pairs
        for affected_route in affected_routes:
            # Find routes with similar origin/destination
            similar_routes = [
                r for r in available_routes
                if (r.origin.country == affected_route.origin.country and
                    r.destination.country == affected_route.destination.country)
            ]
            
            # Sort by reliability and cost
            similar_routes.sort(
                key=lambda r: (r.reliability_score, -r.cost_per_unit),
                reverse=True
            )
            
            if similar_routes:
                best_route = similar_routes[0]
                alternatives.append({
                    'original_route_id': affected_route.id,
                    'alternative_route_id': best_route.id,
                    'transport_mode': best_route.transport_mode,
                    'duration_hours': best_route.avg_duration_hours,
                    'cost_per_unit': best_route.cost_per_unit,
                    'reliability_score': best_route.reliability_score
                })
        
        return alternatives
    
    def calculate_inventory_adjustments(self, disruption: Disruption,
                                       impact_analysis: Dict,
                                       affected_suppliers: List[Supplier]) -> Dict[str, int]:
        """Calculate recommended inventory adjustments."""
        adjustments = {}
        
        # Get affected products
        affected_products = set()
        for supplier in affected_suppliers:
            affected_products.update(supplier.products)
        
        # Calculate safety stock increase
        duration_days = impact_analysis.get('predicted_duration_hours', 168) / 24
        
        for product in affected_products:
            # Increase by 50% of normal lead time demand + disruption duration
            avg_lead_time = sum(s.lead_time_days for s in affected_suppliers 
                              if product in s.products) / len(affected_suppliers)
            
            # Simplified calculation: assume 10 units per day baseline
            baseline_daily_demand = 10
            safety_increase = int((avg_lead_time + duration_days) * baseline_daily_demand * 0.5)
            
            adjustments[product] = safety_increase
        
        return adjustments
    
    def generate_response_plan(self, disruption: Disruption,
                              impact_analysis: Dict,
                              affected_suppliers: List[Supplier],
                              affected_routes: List[Route],
                              all_suppliers: List[Supplier],
                              all_routes: List[Route]) -> ResponsePlan:
        """Generate comprehensive automated response plan."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:12].upper()}"
        
        # Find alternatives
        affected_products = list(set(p for s in affected_suppliers for p in s.products))
        alternative_suppliers = self.find_alternative_suppliers(
            affected_suppliers, all_suppliers, affected_products
        )
        alternative_routes = self.find_alternative_routes(
            affected_routes, all_routes
        )
        
        # Calculate inventory adjustments
        inventory_adjustments = self.calculate_inventory_adjustments(
            disruption, impact_analysis, affected_suppliers
        )
        
        # Estimate implementation cost
        estimated_cost = self._estimate_plan_cost(
            alternative_suppliers, alternative_routes, inventory_adjustments
        )
        
        # Determine priority
        priority = {
            DisruptionSeverity.LOW: 2,
            DisruptionSeverity.MEDIUM: 3,
            DisruptionSeverity.HIGH: 4,
            DisruptionSeverity.CRITICAL: 5
        }[disruption.severity]
        
        # Calculate confidence score
        confidence = self._calculate_plan_confidence(
            alternative_suppliers, alternative_routes
        )
        
        plan = ResponsePlan(
            id=plan_id,
            disruption_id=disruption.id,
            created_at=datetime.now(),
            priority=priority,
            alternative_suppliers=alternative_suppliers,
            alternative_routes=alternative_routes,
            inventory_adjustments=inventory_adjustments,
            estimated_cost=estimated_cost,
            estimated_time_to_resolve=impact_analysis.get('predicted_duration_hours', 168),
            confidence_score=confidence
        )
        
        return plan
    
    def _estimate_plan_cost(self, alternative_suppliers: List[Dict],
                           alternative_routes: List[Dict],
                           inventory_adjustments: Dict[str, int]) -> float:
        """Estimate total cost of implementing the response plan."""
        # Simplified cost calculation
        
        # Cost of switching suppliers (setup costs)
        supplier_switch_cost = len(alternative_suppliers) * 5000
        
        # Additional logistics costs
        route_cost_increase = sum(
            r.get('cost_per_unit', 0) * 100  # Assume 100 units
            for r in alternative_routes
        )
        
        # Inventory holding costs (assume $10 per unit per month)
        inventory_cost = sum(inventory_adjustments.values()) * 10
        
        total_cost = supplier_switch_cost + route_cost_increase + inventory_cost
        
        return total_cost
    
    def _calculate_plan_confidence(self, alternative_suppliers: List[Dict],
                                  alternative_routes: List[Dict]) -> float:
        """Calculate confidence score for the response plan."""
        # Base confidence
        confidence = 70.0
        
        # Increase confidence if we have good alternatives
        if alternative_suppliers:
            avg_reliability = sum(s['reliability_score'] for s in alternative_suppliers) / len(alternative_suppliers)
            confidence += (avg_reliability / 100) * 15
        
        if alternative_routes:
            avg_route_reliability = sum(r['reliability_score'] for r in alternative_routes) / len(alternative_routes)
            confidence += (avg_route_reliability / 100) * 15
        
        return min(confidence, 95.0)


class CrisisOrchestrator:
    """Main orchestration system for crisis response."""
    
    def __init__(self, predictive_engine: PredictiveEngine):
        self.predictive_engine = predictive_engine
        self.alert_generator = AlertGenerator()
        self.response_planner = ResponsePlanner(predictive_engine)
        self.active_alerts = []
        self.response_plans = []
    
    def orchestrate_response(self, disruption: Disruption,
                           suppliers: List[Supplier],
                           routes: List[Route]) -> Dict:
        """
        Orchestrate complete automated response to a disruption.
        """
        # Predict impact
        impact_analysis = self.predictive_engine.predict_disruption_impact(
            disruption, suppliers
        )
        
        # Identify affected entities
        affected_suppliers = [
            s for s in suppliers
            if s.id in impact_analysis.get('affected_suppliers', [])
        ]
        
        affected_routes = [
            r for r in routes
            if (r.origin.region == disruption.location.region or
                r.destination.region == disruption.location.region)
        ]
        
        # Generate alert if needed
        alert = None
        if self.alert_generator.should_generate_alert(disruption):
            alert = self.alert_generator.generate_alert(
                disruption, impact_analysis, affected_suppliers, affected_routes
            )
            self.active_alerts.append(alert)
        
        # Generate response plan
        response_plan = self.response_planner.generate_response_plan(
            disruption, impact_analysis, affected_suppliers, 
            affected_routes, suppliers, routes
        )
        self.response_plans.append(response_plan)
        
        return {
            'disruption': disruption.to_dict(),
            'impact_analysis': impact_analysis,
            'alert': alert.to_dict() if alert else None,
            'response_plan': response_plan.to_dict(),
            'orchestration_timestamp': datetime.now().isoformat()
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return self.active_alerts
    
    def get_response_plans(self) -> List[ResponsePlan]:
        """Get all generated response plans."""
        return self.response_plans
