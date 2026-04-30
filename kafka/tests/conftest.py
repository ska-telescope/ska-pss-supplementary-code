# kafka/tests/conftest.py
import os
import uuid

import pytest


@pytest.fixture
def bootstrap_servers() -> str:
    return os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


@pytest.fixture
def unique_topic() -> str:
    return f"test-spcc-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def unique_group_id() -> str:
    return f"test-cg-{uuid.uuid4().hex[:8]}"
