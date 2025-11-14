#!/usr/bin/env python3
"""
Command-line interface for the Autonomous Supply Chain Crisis Management System.
Demonstrates real-time monitoring and automated crisis response.
"""
import sys
import time
from src.crisis_manager import SupplyChainCrisisManager, create_sample_supply_chain


def print_banner():
    """Print system banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║    AUTONOMOUS SUPPLY CHAIN CRISIS MANAGEMENT SYSTEM                      ║
║                                                                          ║
║    Predictive Intelligence | Automated Response | Crisis Orchestration   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_demo():
    """Run demonstration of the system."""
    print_banner()
    
    print("\n🚀 Initializing Autonomous Supply Chain Crisis Management System...")
    print("-" * 80)
    
    # Create system
    manager = SupplyChainCrisisManager()
    
    # Initialize with sample data
    suppliers, routes = create_sample_supply_chain()
    manager.initialize_supply_chain(suppliers, routes)
    
    print("\n📦 Supply Chain Network:")
    print(f"   • Suppliers: {len(suppliers)}")
    for supplier in suppliers:
        print(f"     - {supplier.name} ({supplier.location.country}) - Status: {supplier.status.value}")
    
    print(f"\n   • Routes: {len(routes)}")
    for route in routes:
        print(f"     - {route.origin.city} → {route.destination.city} via {route.transport_mode}")
    
    print("\n" + "-" * 80)
    print("Press Ctrl+C to stop the monitoring system")
    print("-" * 80)
    
    # Run continuous monitoring cycles
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n{'='*80}")
            print(f"MONITORING CYCLE #{cycle_count}")
            print(f"{'='*80}")
            
            # Run monitoring cycle
            result = manager.run_monitoring_cycle()
            
            # Display system status
            status = manager.get_system_status()
            print("\n📊 SYSTEM STATUS:")
            print(f"   • Total Disruptions Tracked: {status['total_disruptions']}")
            print(f"   • Active Disruptions: {status['active_disruptions']}")
            print(f"   • Active Alerts: {status['active_alerts']}")
            print(f"   • Response Plans Generated: {status['response_plans_generated']}")
            
            # Display active alerts
            alerts = manager.get_active_alerts()
            if alerts:
                print(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
                for alert in alerts[-3:]:  # Show last 3
                    print(f"\n   {alert['title']}")
                    print(f"   Financial Impact: ${alert['estimated_financial_impact']:,.0f}")
                    print(f"   Recommended Actions: {len(alert['recommended_actions'])} actions")
            
            # Wait before next cycle (in real system, this could be event-driven)
            wait_time = 10
            print(f"\n⏳ Next cycle in {wait_time} seconds...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("SYSTEM SHUTDOWN")
        print("="*80)
        
        # Final status
        final_status = manager.get_system_status()
        print(f"\nFinal Statistics:")
        print(f"   • Monitoring Cycles Completed: {cycle_count}")
        print(f"   • Total Disruptions Detected: {final_status['total_disruptions']}")
        print(f"   • Total Alerts Generated: {final_status['active_alerts']}")
        print(f"   • Total Response Plans: {final_status['response_plans_generated']}")
        
        print("\n✓ System shutdown complete")
        print("\nThank you for using Autonomous Supply Chain Crisis Management System")
        print("="*80 + "\n")


def run_single_analysis():
    """Run a single analysis cycle."""
    print_banner()
    
    print("\n🔍 Running Single Analysis Cycle...\n")
    
    # Create and initialize system
    manager = SupplyChainCrisisManager()
    suppliers, routes = create_sample_supply_chain()
    manager.initialize_supply_chain(suppliers, routes)
    
    # Run one cycle
    result = manager.run_monitoring_cycle()
    
    # Display detailed results
    print("\n" + "="*80)
    print("DETAILED ANALYSIS RESULTS")
    print("="*80)
    
    status = manager.get_system_status()
    print(f"\nSystem Status: {status['status']}")
    print(f"Suppliers Monitored: {status['suppliers_monitored']}")
    print(f"Routes Monitored: {status['routes_monitored']}")
    print(f"Health Score: {result['health_score']:.1f}/100")
    
    if result['responses']:
        print(f"\n📋 RESPONSE PLANS GENERATED: {len(result['responses'])}")
        for i, response in enumerate(result['responses'], 1):
            plan = response['response_plan']
            print(f"\n   Plan #{i}: {plan['id']}")
            print(f"   Priority: {plan['priority']}/5")
            print(f"   Confidence: {plan['confidence_score']:.1f}%")
            print(f"   Estimated Cost: ${plan['estimated_cost']:,.0f}")
            print(f"   Time to Resolve: {plan['estimated_time_to_resolve']} hours")
            print(f"   Alternative Suppliers: {len(plan['alternative_suppliers'])}")
            print(f"   Alternative Routes: {len(plan['alternative_routes'])}")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == '--single':
        run_single_analysis()
    else:
        run_demo()


if __name__ == '__main__':
    main()
