"""
Main Autonomous Supply Chain Crisis Management System.
"""
from typing import List, Dict, Optional
from datetime import datetime
from .models.supply_chain import (
    Supplier, Route, Disruption, Location, 
    SupplierStatus, DisruptionType, DisruptionSeverity
)
from .intelligence.synthesizer import IntelligenceSynthesizer
from .analytics.predictive_engine import PredictiveEngine
from .orchestration.crisis_orchestrator import CrisisOrchestrator


class SupplyChainCrisisManager:
    """
    Main system for autonomous supply chain crisis management.
    
    Provides real-time multi-source intelligence synthesis,
    predictive analytics, and automated crisis response orchestration.
    """
    
    def __init__(self):
        # Initialize subsystems
        self.intelligence_synthesizer = IntelligenceSynthesizer()
        self.predictive_engine = PredictiveEngine()
        self.crisis_orchestrator = CrisisOrchestrator(self.predictive_engine)
        
        # Data storage
        self.suppliers: List[Supplier] = []
        self.routes: List[Route] = []
        self.disruptions: List[Disruption] = []
        
        # System state
        self.last_intelligence_update = None
        self.system_status = "initialized"
    
    def initialize_supply_chain(self, suppliers: List[Supplier], 
                               routes: List[Route]):
        """Initialize the supply chain network."""
        self.suppliers = suppliers
        self.routes = routes
        self.system_status = "ready"
        print(f"✓ Initialized supply chain with {len(suppliers)} suppliers and {len(routes)} routes")
    
    def run_intelligence_cycle(self) -> List[Disruption]:
        """
        Run intelligence collection and synthesis cycle.
        Returns newly detected disruptions.
        """
        print("\n🔍 Running intelligence collection cycle...")
        
        # Collect and synthesize intelligence
        new_disruptions = self.intelligence_synthesizer.run_intelligence_cycle()
        
        if new_disruptions:
            print(f"⚠️  Detected {len(new_disruptions)} new disruption(s)")
            self.disruptions.extend(new_disruptions)
        else:
            print("✓ No new disruptions detected")
        
        self.last_intelligence_update = datetime.now()
        return new_disruptions
    
    def analyze_supply_chain_health(self) -> Dict:
        """
        Analyze overall supply chain health and risk posture.
        """
        print("\n📊 Analyzing supply chain health...")
        
        analysis = self.predictive_engine.analyze_supply_chain(
            self.suppliers, self.routes, self.disruptions
        )
        
        health_score = analysis['overall_health_score']
        print(f"Supply Chain Health Score: {health_score:.1f}/100")
        
        if health_score >= 80:
            print("Status: ✓ Healthy")
        elif health_score >= 60:
            print("Status: ⚠️  Moderate Risk")
        elif health_score >= 40:
            print("Status: 🔴 High Risk")
        else:
            print("Status: 🚨 CRITICAL")
        
        return analysis
    
    def respond_to_disruptions(self) -> List[Dict]:
        """
        Automatically respond to active disruptions.
        """
        active_disruptions = [d for d in self.disruptions if d.is_active()]
        
        if not active_disruptions:
            print("\n✓ No active disruptions requiring response")
            return []
        
        print(f"\n🚨 Responding to {len(active_disruptions)} active disruption(s)...")
        
        responses = []
        for disruption in active_disruptions:
            print(f"\n  Processing: {disruption.id}")
            print(f"  Type: {disruption.type.value}")
            print(f"  Severity: {disruption.severity.name}")
            
            response = self.crisis_orchestrator.orchestrate_response(
                disruption, self.suppliers, self.routes
            )
            responses.append(response)
            
            # Display key metrics
            if response['alert']:
                print(f"  ⚠️  Alert generated: {response['alert']['title']}")
            
            plan = response['response_plan']
            print(f"  📋 Response plan created: {plan['id']}")
            print(f"     - Alternative suppliers: {len(plan['alternative_suppliers'])}")
            print(f"     - Alternative routes: {len(plan['alternative_routes'])}")
            print(f"     - Estimated cost: ${plan['estimated_cost']:,.0f}")
            print(f"     - Confidence: {plan['confidence_score']:.1f}%")
        
        return responses
    
    def run_monitoring_cycle(self) -> Dict:
        """
        Run a complete monitoring and response cycle.
        """
        print("\n" + "="*80)
        print("AUTONOMOUS SUPPLY CHAIN CRISIS MANAGEMENT SYSTEM")
        print(f"Cycle started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Step 1: Intelligence collection
        new_disruptions = self.run_intelligence_cycle()
        
        # Step 2: Health analysis
        health_analysis = self.analyze_supply_chain_health()
        
        # Step 3: Automated response
        responses = self.respond_to_disruptions()
        
        # Summary
        print("\n" + "="*80)
        print("CYCLE SUMMARY")
        print("="*80)
        print(f"New disruptions detected: {len(new_disruptions)}")
        print(f"Active disruptions: {len([d for d in self.disruptions if d.is_active()])}")
        print(f"Alerts generated: {len([r for r in responses if r.get('alert')])}")
        print(f"Response plans created: {len(responses)}")
        print(f"Supply chain health: {health_analysis['overall_health_score']:.1f}/100")
        print("="*80 + "\n")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'new_disruptions': len(new_disruptions),
            'active_disruptions': len([d for d in self.disruptions if d.is_active()]),
            'health_score': health_analysis['overall_health_score'],
            'responses': responses
        }
    
    def get_system_status(self) -> Dict:
        """Get current system status and metrics."""
        active_alerts = self.crisis_orchestrator.get_active_alerts()
        response_plans = self.crisis_orchestrator.get_response_plans()
        
        return {
            'status': self.system_status,
            'last_update': self.last_intelligence_update.isoformat() if self.last_intelligence_update else None,
            'suppliers_monitored': len(self.suppliers),
            'routes_monitored': len(self.routes),
            'total_disruptions': len(self.disruptions),
            'active_disruptions': len([d for d in self.disruptions if d.is_active()]),
            'active_alerts': len(active_alerts),
            'response_plans_generated': len(response_plans)
        }
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts."""
        alerts = self.crisis_orchestrator.get_active_alerts()
        return [alert.to_dict() for alert in alerts]
    
    def get_response_plans(self) -> List[Dict]:
        """Get all response plans."""
        plans = self.crisis_orchestrator.get_response_plans()
        return [plan.to_dict() for plan in plans]


def create_sample_supply_chain() -> tuple:
    """Create sample supply chain data for demonstration."""
    
    # Sample suppliers
    suppliers = [
        Supplier(
            id="SUP-001",
            name="TechComponents Asia",
            location=Location("China", "South China Sea", "Shenzhen", 22.5, 114.0),
            status=SupplierStatus.ACTIVE,
            reliability_score=85.0,
            lead_time_days=30,
            capacity=10000,
            products=["semiconductors", "circuit_boards"]
        ),
        Supplier(
            id="SUP-002",
            name="Euro Manufacturing GmbH",
            location=Location("Germany", "Europe", "Munich", 48.1, 11.5),
            status=SupplierStatus.ACTIVE,
            reliability_score=92.0,
            lead_time_days=21,
            capacity=8000,
            products=["automotive_parts", "machinery"]
        ),
        Supplier(
            id="SUP-003",
            name="Americas Logistics Inc",
            location=Location("USA", "Americas", "Chicago", 41.8, -87.6),
            status=SupplierStatus.ACTIVE,
            reliability_score=88.0,
            lead_time_days=14,
            capacity=12000,
            products=["packaging", "logistics_services"]
        ),
        Supplier(
            id="SUP-004",
            name="Eastern Textiles Ltd",
            location=Location("Ukraine", "Eastern Europe", "Kyiv", 50.4, 30.5),
            status=SupplierStatus.AT_RISK,
            reliability_score=65.0,
            lead_time_days=45,
            capacity=5000,
            products=["textiles", "raw_materials"],
            risk_factors=["geopolitical_instability", "supply_chain_disruption"]
        ),
        Supplier(
            id="SUP-005",
            name="Pacific Electronics",
            location=Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5),
            status=SupplierStatus.ACTIVE,
            reliability_score=90.0,
            lead_time_days=28,
            capacity=15000,
            products=["semiconductors", "displays"]
        )
    ]
    
    # Sample routes
    routes = [
        Route(
            id="ROUTE-001",
            origin=Location("China", "South China Sea", "Shenzhen", 22.5, 114.0),
            destination=Location("USA", "Americas", "Los Angeles", 34.0, -118.2),
            transport_mode="sea",
            distance_km=11500,
            avg_duration_hours=720,  # 30 days
            cost_per_unit=50.0,
            reliability_score=85.0
        ),
        Route(
            id="ROUTE-002",
            origin=Location("Germany", "Europe", "Munich", 48.1, 11.5),
            destination=Location("USA", "Americas", "New York", 40.7, -74.0),
            transport_mode="air",
            distance_km=6500,
            avg_duration_hours=12,
            cost_per_unit=150.0,
            reliability_score=92.0
        ),
        Route(
            id="ROUTE-003",
            origin=Location("Taiwan", "Asia-Pacific", "Taipei", 25.0, 121.5),
            destination=Location("USA", "Americas", "San Francisco", 37.7, -122.4),
            transport_mode="sea",
            distance_km=10500,
            avg_duration_hours=648,  # 27 days
            cost_per_unit=55.0,
            reliability_score=88.0
        )
    ]
    
    return suppliers, routes
