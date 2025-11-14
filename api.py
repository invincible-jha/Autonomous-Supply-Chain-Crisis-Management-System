"""
REST API for Autonomous Supply Chain Crisis Management System.
"""
from flask import Flask, jsonify, request
from datetime import datetime
from src.crisis_manager import SupplyChainCrisisManager, create_sample_supply_chain

app = Flask(__name__)

# Global system instance
crisis_manager = None


def initialize_system():
    """Initialize the crisis management system."""
    global crisis_manager
    if crisis_manager is None:
        crisis_manager = SupplyChainCrisisManager()
        suppliers, routes = create_sample_supply_chain()
        crisis_manager.initialize_supply_chain(suppliers, routes)
        print("✓ System initialized")


@app.route('/')
def index():
    """API root endpoint."""
    return jsonify({
        'name': 'Autonomous Supply Chain Crisis Management System',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            'status': '/api/status',
            'health': '/api/health',
            'alerts': '/api/alerts',
            'plans': '/api/plans',
            'monitor': '/api/monitor',
            'suppliers': '/api/suppliers',
            'routes': '/api/routes',
            'disruptions': '/api/disruptions'
        }
    })


@app.route('/api/status')
def get_status():
    """Get system status."""
    initialize_system()
    status = crisis_manager.get_system_status()
    return jsonify(status)


@app.route('/api/health')
def get_health():
    """Get supply chain health analysis."""
    initialize_system()
    analysis = crisis_manager.analyze_supply_chain_health()
    return jsonify(analysis)


@app.route('/api/alerts')
def get_alerts():
    """Get active alerts."""
    initialize_system()
    alerts = crisis_manager.get_active_alerts()
    return jsonify({
        'count': len(alerts),
        'alerts': alerts
    })


@app.route('/api/plans')
def get_plans():
    """Get response plans."""
    initialize_system()
    plans = crisis_manager.get_response_plans()
    return jsonify({
        'count': len(plans),
        'plans': plans
    })


@app.route('/api/monitor', methods=['POST'])
def run_monitor():
    """Run a monitoring cycle."""
    initialize_system()
    result = crisis_manager.run_monitoring_cycle()
    return jsonify(result)


@app.route('/api/suppliers')
def get_suppliers():
    """Get all suppliers."""
    initialize_system()
    suppliers = [s.to_dict() for s in crisis_manager.suppliers]
    return jsonify({
        'count': len(suppliers),
        'suppliers': suppliers
    })


@app.route('/api/routes')
def get_routes():
    """Get all routes."""
    initialize_system()
    routes = [{
        'id': r.id,
        'origin': f"{r.origin.city}, {r.origin.country}",
        'destination': f"{r.destination.city}, {r.destination.country}",
        'transport_mode': r.transport_mode,
        'distance_km': r.distance_km,
        'duration_hours': r.avg_duration_hours,
        'reliability_score': r.reliability_score,
        'status': r.status
    } for r in crisis_manager.routes]
    return jsonify({
        'count': len(routes),
        'routes': routes
    })


@app.route('/api/disruptions')
def get_disruptions():
    """Get all disruptions."""
    initialize_system()
    disruptions = [d.to_dict() for d in crisis_manager.disruptions]
    active = [d for d in disruptions if d['is_active']]
    return jsonify({
        'total': len(disruptions),
        'active': len(active),
        'disruptions': disruptions
    })


@app.route('/api/intelligence/collect', methods=['POST'])
def collect_intelligence():
    """Manually trigger intelligence collection."""
    initialize_system()
    new_disruptions = crisis_manager.run_intelligence_cycle()
    return jsonify({
        'new_disruptions': len(new_disruptions),
        'disruptions': [d.to_dict() for d in new_disruptions]
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


def main():
    """Run the API server."""
    print("="*80)
    print("Autonomous Supply Chain Crisis Management System - REST API")
    print("="*80)
    print("\nInitializing system...")
    initialize_system()
    print("\n✓ System ready")
    print("\nAPI Documentation:")
    print("  • GET  /              - API information")
    print("  • GET  /api/status    - System status")
    print("  • GET  /api/health    - Supply chain health")
    print("  • GET  /api/alerts    - Active alerts")
    print("  • GET  /api/plans     - Response plans")
    print("  • POST /api/monitor   - Run monitoring cycle")
    print("  • GET  /api/suppliers - List suppliers")
    print("  • GET  /api/routes    - List routes")
    print("  • GET  /api/disruptions - List disruptions")
    print("\nStarting server on http://localhost:5000")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
