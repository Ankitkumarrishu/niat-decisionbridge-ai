import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Isolate unit tests from any local .env credentials
os.environ["OPENAI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["SUPABASE_ANON_KEY"] = ""
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-unit-tests-only"
os.environ["COUNSELLOR_EMAILS"] = "counsellor@test.com"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    with patch("app.routes.intake.get_db") as intake_db, patch(
        "app.routes.decision_brief.get_db"
    ) as brief_db, patch("app.routes.leads.get_db") as leads_db, patch(
        "app.routes.dashboard.get_db"
    ) as dash_db:
        db = MagicMock()
        db.is_configured.return_value = True
        intake_db.return_value = db
        brief_db.return_value = db
        leads_db.return_value = db
        dash_db.return_value = db
        yield db
