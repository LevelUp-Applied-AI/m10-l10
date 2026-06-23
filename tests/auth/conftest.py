"""Auth-suite conftest — sets required env vars only for auth tests.

Uses a module-scoped autouse fixture with yield so the env vars are
restored to their original values before tests/backend/ runs.
Setting them at module-level (os.environ.setdefault outside a fixture)
would permanently affect the backend tests that follow alphabetically.
"""
import os

import pytest

_AUTH_ENV = {
    "AUTH_ENABLED": "1",
    "JWT_SECRET": "ci-test-jwt-secret-do-not-use-in-prod-xxxxxxxx",
    "JWT_ALGORITHM": "HS256",
    "API_KEY_VALID": "ci-test-api-key",
}


@pytest.fixture(scope="module", autouse=True)
def auth_env_vars():
    """Set auth env vars for this module, then restore originals.

    module scope means: set before first auth test, restore after
    the last auth test — so tests/backend/ sees the original values.
    """
    old = {k: os.environ.get(k) for k in _AUTH_ENV}
    os.environ.update(_AUTH_ENV)
    yield
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
