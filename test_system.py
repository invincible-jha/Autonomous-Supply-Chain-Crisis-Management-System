#!/usr/bin/env python3
"""Quick test to demonstrate disruption detection and response."""
from src.crisis_manager import SupplyChainCrisisManager, create_sample_supply_chain

# Initialize system
manager = SupplyChainCrisisManager()
suppliers, routes = create_sample_supply_chain()
manager.initialize_supply_chain(suppliers, routes)

# Run multiple cycles to detect disruptions
for i in range(5):
    print(f"\n{'='*70}")
    print(f"CYCLE {i+1}")
    print('='*70)
    result = manager.run_monitoring_cycle()
    
    if result['responses']:
        print(f"\n✅ RESPONSES GENERATED: {len(result['responses'])}")
        for resp in result['responses']:
            plan = resp['response_plan']
            print(f"   Plan: {plan['id']}")
            print(f"   Priority: {plan['priority']}/5")
            print(f"   Cost: ${plan['estimated_cost']:,.0f}")
            print(f"   Confidence: {plan['confidence_score']:.1f}%")
            if resp['alert']:
                print(f"   Alert: {resp['alert']['title']}")
        break
