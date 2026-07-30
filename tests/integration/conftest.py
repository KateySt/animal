import pytest


@pytest.fixture(autouse=True)
def _bind_factories_for_integration(bind_factories):
    pass
