# SPDX-License-Identifier: Apache-2.0
"""Pytest fixtures ensuring Klaint tests import cleanly with zero pip installs and clean up broker/DB handles."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

KLAINT_SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(KLAINT_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(KLAINT_SERVICE_ROOT))

from klaint.broker.client import BrokerClient  # noqa: E402
from klaint.core.models import SessionAuthenticator  # noqa: E402
from klaint.resolution.engine import ResolutionEngine  # noqa: E402
from klaint.storage.tenant_db import TenantStorageRegistry  # noqa: E402


@pytest.fixture()
def klaint_env() -> Iterator[tuple[Path, TenantStorageRegistry, BrokerClient, SessionAuthenticator, ResolutionEngine]]:
    """Provide an isolated temporary data directory, TenantStorageRegistry, out-of-process BrokerClient, and ResolutionEngine."""
    base_dir = Path(tempfile.mkdtemp(prefix="klaint_test_"))
    storage = TenantStorageRegistry(base_dir)
    broker = BrokerClient(base_dir)
    session_auth = SessionAuthenticator()
    engine = ResolutionEngine(storage=storage, broker=broker)
    try:
        yield base_dir, storage, broker, session_auth, engine
    finally:
        broker.close()
        storage.close_all()
        shutil.rmtree(base_dir, ignore_errors=True)
