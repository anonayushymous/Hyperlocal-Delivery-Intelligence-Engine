# Hyperlocal Delivery & Marketplace Intelligence Engine

A comprehensive analytics and intelligence platform for hyperlocal delivery operations, built to optimize 10-minute delivery promises through real-time monitoring, performance tracking, and data-driven decision making.

## Overview

This project simulates and analyzes a quick-commerce delivery platform (similar to Blinkit, Zepto, or Instamart) that promises deliveries within 12 minutes. It includes synthetic data generation, a data warehouse schema, and an interactive Streamlit dashboard for operational analytics.

## Features

### 1. Sales & Growth Analytics
- Total revenue and order volume tracking
- Customer shopping funnel analysis with drop-off visualization
- Average order value and success rate monitoring
- Real-time conversion metrics

### 2. Warehouse & Rider Operations
- Dark store performance monitoring across multiple zones
- Delivery time tracking and SLA compliance
- Rider performance leaderboard with ratings
- Late delivery identification and root cause analysis

### 3. Delivery Quality Diagnostics
- Delivery time distribution analysis (bell curve visualization)
- Failed delivery reason breakdown
- Customer complaint tracking by zone and type
- Quality metrics and root cause identification

### 4. Dynamic Surge Pricing A/B Testing
- Experimental framework for testing rush-hour surge fees
- Statistical evaluation of pricing strategies
- Conversion rate and average order value comparison
- Business impact analysis with recommendations

## Project Structure

```
hyperlocal-intelligence-engine/
├── app.py                      # Main Streamlit dashboard application
├── config.py                   # Database configuration
├── data_generator.py           # Synthetic data generation for users, orders, riders, stores
├── db_loader.py                # Database schema creation and data loading
├── requirements.txt            # Python dependencies
├── run_pipeline.sh             # Automated pipeline execution script
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-service orchestration
├── analytics/
│   ├── __init__.py
│   ├── ab_testing.py          # A/B test evaluation logic
│   └── anomaly_detection.py   # Time-series anomaly detection for fulfillment
└── sql/
    ├── 01_funnel_conversion.sql    # Funnel analysis queries
    ├── 02_rolling_sla_breach.sql   # SLA breach monitoring
    └── 03_retention_cohorts.sql    # User retention cohort analysis
```

## Tech Stack

- **Python 3.8+** - Core programming language
- **Streamlit** - Interactive dashboard framework
- **Pandas & NumPy** - Data manipulation and analysis
- **Plotly** - Interactive visualizations
- **SQLAlchemy** - Database ORM and query interface
- **PostgreSQL / SQLite** - Data warehouse (configurable)
- **Faker** - Synthetic data generation
- **SciPy & Statsmodels** - Statistical analysis for A/B testing

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) Docker for containerized deployment

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hyperlocal-intelligence-engine.git
cd hyperlocal-intelligence-engine
```

2. Create and activate a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate synthetic data and load the database:
```bash
python db_loader.py
```

5. Launch the Streamlit dashboard:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage

### Running the Full Pipeline

Execute the automated pipeline script:
```bash
bash run_pipeline.sh
```

This will:
1. Generate synthetic order, user, rider, and store data
2. Create database schema (fact and dimension tables)
3. Load data into the warehouse
4. Launch the analytics dashboard

### Dashboard Navigation

The dashboard includes four main modules accessible from the sidebar:

1. **Sales & Growth Overview** - Monitor revenue, order volume, and conversion funnels
2. **Warehouse & Rider Operations** - Track delivery performance and rider efficiency
3. **Delivery Quality & Root Cause Analysis** - Diagnose delays and failures
4. **Dynamic Surge Pricing A/B Test** - Evaluate pricing experiments

### Generating Custom Data

Modify parameters in `data_generator.py`:
```python
generate_all_data(n_users=5000, n_orders=25000)
```

Adjust:
- `n_users`: Number of customers to generate
- `n_orders`: Total order volume
- Date ranges, store locations, and other parameters

## Database Schema

### Dimension Tables
- `dim_users` - Customer profiles with experiment groups
- `dim_dark_stores` - Warehouse locations with geocoordinates
- `dim_riders` - Delivery fleet with ratings and vehicle types
- `dim_skus` - Product catalog with pricing

### Fact Tables
- `fct_orders` - Core order transactions with delivery metrics
- `fct_order_events` - Customer behavior events (search, cart, checkout)

## Key Metrics

- **Delivery SLA**: 12 minutes target
- **Success Rate**: % of orders successfully delivered
- **Average Order Value (AOV)**: Revenue per order
- **Late Delivery Rate**: % of orders exceeding SLA
- **Conversion Rate**: % of sessions resulting in orders
- **Rider Efficiency**: On-time delivery percentage

## A/B Testing Framework

The platform includes a built-in experimental framework for testing operational changes:

- **Control Group**: Standard flat delivery fee (₹15)
- **Treatment Group**: Dynamic surge pricing during peak hours (₹20-50)
- **Statistical Evaluation**: T-tests, confidence intervals, and effect size calculation
- **Business Metrics**: AOV lift, conversion impact, revenue projection

## Docker Deployment

Build and run with Docker:
```bash
docker-compose up --build
```

Access the dashboard at `http://localhost:8501`

## Sample Insights

The platform helps answer critical business questions:

- Which dark stores consistently miss SLA targets?
- What are the primary reasons for delivery failures?
- How does surge pricing affect customer behavior?
- Which riders have the best performance metrics?
- Where are customer complaints concentrated?
- What's the optimal pricing strategy for peak hours?

## Development

### Adding New Analytics Modules

1. Create SQL queries in the `sql/` directory
2. Add data loading functions in `app.py` with caching
3. Design visualizations using Plotly
4. Add navigation items to the sidebar

### Extending the Data Model

1. Modify schema in `db_loader.py`
2. Update data generation in `data_generator.py`
3. Regenerate database: `python db_loader.py`

## Future Enhancements

- Real-time order tracking with WebSocket updates
- Predictive demand forecasting using ML models
- Route optimization for delivery riders
- Inventory management and stockout prediction
- Customer lifetime value (LTV) analysis
- Multi-city expansion analytics
- Integration with actual delivery APIs

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with Streamlit for rapid dashboard development
- Inspired by real-world quick-commerce platforms
- Data visualization patterns follow modern analytics best practices

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This project uses synthetic data for demonstration purposes. All user data, locations, and business metrics are randomly generated and do not represent any real business or individuals.
