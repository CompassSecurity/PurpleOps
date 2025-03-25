import pytest
import os
import json
import pymongo
import purpleops

@pytest.fixture(scope="session")
def app():
    """Flask test client fixture with a mock database."""
    purpleops.app.config.update({
        "TESTING": True
    })
    yield purpleops.app

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
