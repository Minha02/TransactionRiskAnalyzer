import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pytest
from flask import Flask
from main.controller import main_bp
from main.database_connection import DatabaseManager
from main.models import TransactionAnalysis
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from main import db
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    app.register_blueprint(main_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def api_key():
    return os.getenv('SECRET_API_KEY', 'test-api-key')

def test_create_transaction(client, api_key):
    transaction = {
        "transaction_id": "tx_12345",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 129.99,
        "currency": "USD",
        "customer": {"id": "cust_98765", "country": "US", "ip_address": "192.168.1.1"},
        "payment_method": {"type": "credit_card", "last_four": "4242", "country_of_issue": "US"},
        "merchant": {"id": "merch_12345", "name": "Example Store", "category": "electronics"}
    }
    response = client.post("/transaction", 
                          json=transaction, 
                          headers={"X-API-KEY": api_key})
    assert response.status_code == 201
    assert response.json["message"] == "Transaction validated and analyzed."

def test_get_analyses(client, api_key, mocker):
    mock_data = [{
        "transaction_id": "tx_12345",
        "risk_score": 0.5,
        "recommended_action": "review"
    }]
    
    mocker.patch("main.database_connection.DatabaseManager.get_all_analyses", 
                 return_value=mock_data)
    with client.application.app_context():
        response = client.get("/analyses", headers={"X-API-KEY": api_key})
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]["transaction_id"] == "tx_12345"

def test_get_admin_notifications(client, api_key, mocker):
    mock_data = [{
        "transaction_data": '{"transaction_id": "tx_67890"}',
        "risk_score": 0.8,
        "risk_factors": '["factor1", "factor2"]',
        "llm_response": '{"reasoning": "High risk due to geographic anomalies"}'
    }]
    
    mocker.patch("main.database_connection.DatabaseManager.get_high_risk_analyses", 
                 return_value=mock_data)
    
    with client.application.app_context():
        response = client.get("/admin/notifications", headers={"X-API-KEY": api_key})
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]["alert_type"] == "high_risk_transaction"
        assert data[0]["risk_score"] == 0.8