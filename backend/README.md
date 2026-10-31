# MediRisk 2.0 Backend Service

FastAPI Python 3.12 backend service providing REST API endpoints for multi-disease tabular risk assessment, authentication, probability calibration, and hospital GIS query proxying.

## Structure
- `app/main.py`: Application entry point and healthcheck route.
- `app/core/`: Settings configuration and security helpers.
- `app/api/`: Versioned API endpoint routers.
- `app/models/`: SQLAlchemy ORM models.
- `app/schemas/`: Pydantic V2 validation schemas.
- `app/services/`: Core business logic services.
- `app/db/`: Database session generator and base models.

## Local Running
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python -m app.main
```
Server starts on `http://localhost:8000`. OpenAPI docs available at `http://localhost:8000/docs`.
