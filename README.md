# Hyperlocal Delivery & Marketplace Intelligence Engine

A comprehensive analytics and intelligence platform for hyperlocal delivery operations, built to optimize 10-minute delivery promises through real-time monitoring, performance tracking, and data-driven decision making.

## Overview

This project simulates and analyzes a quick-commerce delivery platform (similar to Blinkit, Zepto, or Instamart) that promises deliveries within 12 minutes. Built on a modern microservices architecture, it features a FastAPI backend for data services, a Streamlit frontend for visualization, PostgreSQL database, and containerized deployment with Docker Compose.

## Architecture

This platform is built on a microservices architecture with clear separation of concerns:

- **Backend (FastAPI)**: RESTful API providing real-time metrics and analytics services
- **Frontend (Streamlit)**: Interactive dashboard consuming backend API endpoints
- **Database (PostgreSQL)**: Data warehouse with dimensional modeling for OLAP queries
- **Containerization (Docker)**: Fully orchestrated multi-service deployment

## Features

### 1. Sales & Growth Analytics
- Total revenue and order volume tracking via RESTful API
- Customer shopping funnel analysis with drop-off visualization
- Average order value and success rate monitoring
- Real-time conversion metrics

### 2. Warehouse & Rider Operations
- Dark store performance monitoring across multiple zones
- Delivery time tracking and SLA compliance
- Rider performance leaderboard with ratings
- Late delivery identification and root cause analysis

## Project Structure

```
hyperlocal-intelligence-engine/
├── backend/                          # FastAPI microservice
│   ├── app/
│   │   ├── main.py                  # API entry point with endpoint definitions
│   │   ├── database.py              # SQLAlchemy engine and session management
│   │   ├── models.py                # ORM models for database tables
│   │   ├── schemas.py               # Pydantic schemas for API contracts
│   │   └── services/
│   │       ├── analytics.py         # Business logic for metrics computation
│   │       └── ab_testing.py        # A/B testing evaluation service
│   ├── tests/
│   │   └── test_api.py              # API endpoint integration tests
│   ├── Dockerfile                   # Backend container image
│   └── requirements.txt             # Backend Python dependencies
├── frontend/                         # Streamlit dashboard
│   ├── app.py                       # UI application consuming backend APIs
│   ├── Dockerfile                   # Frontend container image
│   └── requirements.txt             # Frontend Python dependencies
├── scripts/                          # Data pipeline utilities
│   ├── data_generator.py            # Synthetic data generation
│   └── db_loader.py                 # Database schema creation and seeding
├── data/                             # Generated data files
├── sql/                              # Analytical SQL queries
│   ├── 01_funnel_conversion.sql
│   ├── 02_rolling_sla_breach.sql
│   └── 03_retention_cohorts.sql
├── docker-compose.yml                # Multi-container orchestration
├── pytest.ini                        # Test configuration
└── requirements.txt                  # Root-level dependencies
```

## Tech Stack

### Backend
- **FastAPI** - High-performance async web framework for RESTful APIs
- **SQLAlchemy** - Database ORM and query interface
- **Pydantic** - Data validation and serialization
- **PostgreSQL** - Production-grade data warehouse
- **Uvicorn** - ASGI server for FastAPI

### Frontend
- **Streamlit** - Interactive dashboard framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive visualizations
- **Requests** - HTTP client for API consumption

### Data & DevOps
- **Faker** - Synthetic data generation
- **Docker & Docker Compose** - Containerization and orchestration
- **Pytest** - Backend API testing framework

## Installation

### Prerequisites
- Docker & Docker Compose (recommended)
- **OR** Python 3.8+ and PostgreSQL for local development

### Option 1: Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hyperlocal-intelligence-engine.git
cd hyperlocal-intelligence-engine
```

2. Start all services with Docker Compose:
```bash
docker-compose up --build
```

This will start three containers:
- **PostgreSQL** on port 5432
- **FastAPI Backend** on port 8000
- **Streamlit Frontend** on port 8501

3. Access the application:
- Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs
- API Health: http://localhost:8000/health

### Option 2: Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hyperlocal-intelligence-engine.git
cd hyperlocal-intelligence-engine
```

2. Set up PostgreSQL database:
```bash
# Create database
createdb hyperlocal_db

# Or use the provided docker-compose for just the database
docker-compose up db -d
```

3. Generate synthetic data and load the database:
```bash
python scripts/data_generator.py
python scripts/db_loader.py
```

4. Start the backend API:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Start the frontend dashboard (in a new terminal):
```bash
cd frontend
pip install -r requirements.txt
export API_URL=http://localhost:8000  # On Windows: set API_URL=http://localhost:8000
streamlit run app.py
```

6. Access the application:
- Dashboard: http://localhost:8501
- API: http://localhost:8000

## Usage

### API Endpoints

The FastAPI backend exposes the following RESTful endpoints:

- `GET /health` - Health check
- `GET /api/v1/metrics/sales-summary` - Total revenue, orders, success rate, avg bill
- `GET /api/v1/metrics/funnel` - Customer journey funnel data
- `GET /api/v1/metrics/store-delays` - Dark store late delivery rates
- `GET /api/v1/metrics/rider-performance` - Rider leaderboard

Interactive API documentation available at: http://localhost:8000/docs

### Dashboard Navigation

The Streamlit frontend includes modules accessible from the sidebar:

1. **Sales & Growth Overview** - Monitor revenue, order volume, and conversion funnels
2. **Warehouse & Rider Operations** - Track delivery performance and rider efficiency

### Generating Custom Data

Modify parameters in `scripts/data_generator.py`:
```python
generate_all_data(n_users=5000, n_orders=25000)
```

Then reload the database:
```bash
python scripts/db_loader.py
```

Restart the backend service to reflect changes.

## Database Schema

The PostgreSQL data warehouse uses a dimensional model optimized for OLAP queries:

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

## Testing

Run backend API tests:
```bash
cd backend
pytest tests/ -v
```

The test suite includes integration tests for all API endpoints.

## Sample Insights

The platform helps answer critical business questions:

- Which dark stores consistently miss SLA targets?
- What are the primary reasons for delivery failures?
- How does surge pricing affect customer behavior?
- Which riders have the best performance metrics?
- Where are customer complaints concentrated?
- What's the optimal pricing strategy for peak hours?

## Development

### Adding New API Endpoints

1. Define Pydantic schemas in `backend/app/schemas.py`
2. Implement business logic in `backend/app/services/analytics.py`
3. Add endpoint routes in `backend/app/main.py`
4. Write tests in `backend/tests/test_api.py`

### Adding Frontend Visualizations

1. Fetch data from backend API using `requests`
2. Transform data with Pandas
3. Create visualizations using Plotly
4. Add navigation items to sidebar in `frontend/app.py`

### Extending the Data Model

1. Modify ORM models in `backend/app/models.py`
2. Update schema in `scripts/db_loader.py`
3. Update data generation in `scripts/data_generator.py`
4. Regenerate database: `python scripts/db_loader.py`

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
