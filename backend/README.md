# Araiap backend

Python 3.11 FastAPI service for versioned floor maps, floor-plan object storage, and
published-map downloads. The MVP deliberately has no account or authentication system.

## Local development

```powershell
docker compose up -d
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Manager write endpoints are open to keep the MVP focused on map editing and navigation.
Do not expose this service directly to the public internet without adding an access-control
layer later.

Run tests:

```powershell
pytest
```

Tests use async SQLite and an in-memory object-storage replacement. Production uses
PostgreSQL/PostGIS (polygon geometry with metre units and no SRID) and MinIO through the
S3 API.
