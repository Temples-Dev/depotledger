"""Tests for production settings guards."""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def try_import_production(env_overrides):
    env = {"PATH": os.environ.get("PATH", ""), **env_overrides}
    return subprocess.run(
        [sys.executable, "-c", "import config.settings.production"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def test_production_refuses_default_secret_key():
    result = try_import_production({"DJANGO_ALLOWED_HOSTS": "example.com"})
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY" in result.stderr


def test_production_refuses_missing_allowed_hosts():
    result = try_import_production({"DJANGO_SECRET_KEY": "a-strong-secret-value"})
    assert result.returncode != 0
    assert "DJANGO_ALLOWED_HOSTS" in result.stderr


def test_production_imports_with_required_settings():
    result = try_import_production(
        {
            "DJANGO_SECRET_KEY": "a-strong-secret-value",
            "DJANGO_ALLOWED_HOSTS": "example.com",
        }
    )
    assert result.returncode == 0, result.stderr
