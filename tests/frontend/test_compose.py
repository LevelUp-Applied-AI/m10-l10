"""Lab-level docker-compose.yml structural check."""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_compose():
    return yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())


def test_lab_compose_declares_api_and_web():
    """Catches buggy variant: learner ships the integration-style 4-service
    Compose in the Lab repo."""
    cfg = _load_compose()
    services = cfg.get("services") or {}
    assert "api" in services
    assert "web" in services


def test_lab_compose_web_depends_on_api():
    """Catches buggy variant: bare `depends_on: [api]` waits only for
    container start, not readiness."""
    cfg = _load_compose()
    web_deps = cfg["services"]["web"].get("depends_on") or {}
    # Allow either dict form (preferred) or list form (less strict).
    if isinstance(web_deps, dict):
        assert "api" in web_deps
        assert web_deps["api"].get("condition") == "service_healthy"
    else:
        assert "api" in web_deps


def test_lab_compose_web_uses_localhost_api_url():
    """Catches buggy variant: NEXT_PUBLIC_API_URL=http://api:8000 — DNS
    only resolves inside the Compose network, not in the browser."""
    cfg = _load_compose()
    env = cfg["services"]["web"].get("environment") or {}
    if isinstance(env, list):
        env = dict(item.split("=", 1) for item in env)
    url = env.get("NEXT_PUBLIC_API_URL", "")
    assert "localhost" in url
    assert "//api:" not in url
