import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from app import User

@pytest.fixture(scope='module')
def test_client():
    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
            yield testing_client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def init_database():
    db.create_all()
    yield db 
    db.session.remove()
    db.drop_all()

@pytest.fixture(autouse=True)
def rollback_transaction(request):
    yield
    db.session.rollback()