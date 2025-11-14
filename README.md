# Autonomous Supply Chain Crisis Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Problem Statement

**Fundamental Pain Point**: Supply chain disruptions cost enterprises $50-200M per incident

### First Principles Breakdown

- **Core Problem**: Reactive vs predictive supply chain management
- **Root Cause**: Lack of real-time multi-source intelligence synthesis
- **Critical Gap**: Automated crisis response orchestration
- **Time Pressure**: Increasing geopolitical instability

## 🚀 Solution Overview

An **autonomous, AI-powered system** that transforms supply chain management from reactive to predictive through:

1. **Real-time Multi-Source Intelligence Synthesis**
   - Geopolitical event monitoring
   - Weather and natural disaster tracking
   - Supplier health monitoring
   - Logistics network analysis

2. **Predictive Analytics Engine**
   - Risk scoring algorithms
   - Disruption prediction models
   - Financial impact assessment
   - Cascade risk analysis

3. **Automated Crisis Response Orchestration**
   - Real-time alert generation
   - Automated response plan creation
   - Alternative supplier/route recommendations
   - Inventory optimization suggestions

## 🏗️ Architecture

```
src/
├── models/               # Core data models
│   └── supply_chain.py  # Supplier, Route, Disruption, Alert, ResponsePlan
├── intelligence/         # Multi-source intelligence synthesis
│   └── synthesizer.py   # Geopolitical, Weather, Supplier, Logistics monitors
├── analytics/           # Predictive analytics
│   └── predictive_engine.py  # Risk scoring, impact assessment, predictions
├── orchestration/       # Crisis response automation
│   └── crisis_orchestrator.py  # Alert generation, response planning
└── crisis_manager.py    # Main system orchestrator
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/invincible-jha/Autonomous-Supply-Chain-Crisis-Management-System.git
cd Autonomous-Supply-Chain-Crisis-Management-System
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Command-Line Interface

Run continuous monitoring:
```bash
python demo.py
```

Run single analysis cycle:
```bash
python demo.py --single
```

### REST API

Start the API server:
```bash
python api.py
```

The API will be available at `http://localhost:5000`

#### API Endpoints

- `GET /` - API information and available endpoints
- `GET /api/status` - System status and metrics
- `GET /api/health` - Supply chain health analysis
- `GET /api/alerts` - Active crisis alerts
- `GET /api/plans` - Response plans
- `POST /api/monitor` - Trigger monitoring cycle
- `GET /api/suppliers` - List all suppliers
- `GET /api/routes` - List all routes
- `GET /api/disruptions` - List all disruptions
- `POST /api/intelligence/collect` - Trigger intelligence collection

### Python API

```python
from src.crisis_manager import SupplyChainCrisisManager, create_sample_supply_chain

# Initialize system
manager = SupplyChainCrisisManager()

# Load supply chain data
suppliers, routes = create_sample_supply_chain()
manager.initialize_supply_chain(suppliers, routes)

# Run monitoring cycle
result = manager.run_monitoring_cycle()

# Get system status
status = manager.get_system_status()

# Get active alerts
alerts = manager.get_active_alerts()

# Get response plans
plans = manager.get_response_plans()
```

## 🧪 Testing

Run all tests:
```bash
python -m unittest discover tests
```

Run specific test modules:
```bash
python -m unittest tests.test_models
python -m unittest tests.test_intelligence
python -m unittest tests.test_analytics
python -m unittest tests.test_orchestration
```

## 🔍 Key Features

### 1. Multi-Source Intelligence Synthesis

The system continuously monitors multiple data sources:

- **Geopolitical Monitor**: Tracks trade sanctions, border closures, political unrest
- **Weather Monitor**: Monitors hurricanes, typhoons, floods, earthquakes
- **Supplier Monitor**: Analyzes supplier health metrics and performance
- **Logistics Monitor**: Tracks port congestion, route closures, delays

### 2. Predictive Analytics

Advanced algorithms assess risk and predict impacts:

- **Risk Scoring**: Real-time risk scores (0-100) for suppliers and routes
- **Disruption Prediction**: Probabilistic forecasts of future disruptions
- **Impact Assessment**: Financial and operational impact calculations
- **Cascade Analysis**: Identifies potential cascade effects across the network

### 3. Automated Crisis Response

When disruptions are detected, the system automatically:

- **Generates Alerts**: Priority-based alerts with severity levels
- **Creates Response Plans**: Actionable plans with alternative suppliers/routes
- **Calculates Costs**: Estimates implementation costs and timelines
- **Recommends Actions**: Step-by-step mitigation strategies

## 📊 Example Output

```
================================================================================
AUTONOMOUS SUPPLY CHAIN CRISIS MANAGEMENT SYSTEM
Cycle started at: 2024-01-15 14:30:00
================================================================================

🔍 Running intelligence collection cycle...
⚠️  Detected 2 new disruption(s)

📊 Analyzing supply chain health...
Supply Chain Health Score: 72.3/100
Status: ⚠️  Moderate Risk

🚨 Responding to 2 active disruption(s)...

  Processing: DISR-20240115143001-4521
  Type: geopolitical
  Severity: HIGH
  ⚠️  Alert generated: 🔴 High Priority: Geopolitical - Eastern Europe
  📋 Response plan created: PLAN-A7B3C9D1E2F4
     - Alternative suppliers: 3
     - Alternative routes: 2
     - Estimated cost: $127,500
     - Confidence: 82.3%

================================================================================
CYCLE SUMMARY
================================================================================
New disruptions detected: 2
Active disruptions: 2
Alerts generated: 2
Response plans created: 2
Supply chain health: 72.3/100
================================================================================
```

## 🎯 Key Metrics

The system provides comprehensive metrics including:

- **Overall Health Score**: 0-100 composite score of supply chain resilience
- **Risk Scores**: Individual risk assessments for each supplier and route
- **Financial Impact**: Estimated costs of disruptions and mitigation
- **Cascade Risk**: Probability and severity of cascade effects
- **Confidence Scores**: Reliability of predictions and recommendations

## 🔧 Customization

### Adding Custom Intelligence Sources

Extend the `IntelligenceSource` base class:

```python
from src.intelligence.synthesizer import IntelligenceSource

class CustomMonitor(IntelligenceSource):
    def __init__(self):
        super().__init__("Custom Monitor")
    
    def fetch_data(self):
        # Your custom data collection logic
        return events
```

### Custom Risk Scoring

Modify risk weights in `RiskScorer`:

```python
self.risk_weights = {
    'geopolitical': 0.30,  # Increase geopolitical weight
    'weather': 0.20,
    'supplier_reliability': 0.25,
    'route_reliability': 0.15,
    'geographic_concentration': 0.10
}
```

## 🔐 Security Considerations

- All data is processed locally by default
- No credentials or sensitive data stored in code
- API endpoints can be secured with authentication (add your preferred auth method)
- Rate limiting recommended for production deployments

## 🚧 Future Enhancements

- [ ] Machine learning models for disruption prediction
- [ ] Integration with real-time news APIs
- [ ] Weather service API integration
- [ ] Supplier IoT sensor integration
- [ ] Advanced visualization dashboard
- [ ] Historical data analysis and trend detection
- [ ] Multi-language support
- [ ] Cloud deployment templates

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

Built to address the critical need for autonomous supply chain crisis management in an increasingly unstable global environment.
