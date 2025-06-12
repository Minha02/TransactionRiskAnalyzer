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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  
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

def test_create_transaction(client, api_key,mocker):
    mocker.patch(
        "main.get_financial_risk.analyse_transaction_deepseek",
        return_value={"risk_score": 0.3, "reasoning": "Low risk transaction"}
    )
    mocker.patch(
        "main.validator.validate_transaction",
        return_value=True
    )
    mocker.patch(
        "main.database_connection.DatabaseManager.save_transaction_analysis",
        return_value=True
    )
    transaction = {
        "transaction_id": "tx_12345",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 129.99,
        "currency": "USD",
        "customer": {"id": "cust_98765", "country": "US", "ip_address": "192.168.1.1"},
        "payment_method": {"type": "credit_card", "last_four": "4242", "country_of_issue": "US"},
        "merchant": {"id": "merch_12345", "name": "Example Store", "category": "electronics"}
    }
    with client.application.app_context():
        response = client.post(
            "/transaction",
            json=transaction,
            headers={"X-API-KEY": api_key}
        )
        
        # Debug output
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {response.get_json()}")
        
        # Assertions
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Transaction validated and analyzed."
        assert "llm_result" in data

def test_get_analyses(client, api_key, mocker):
    mock_data = [{
        "id": 1,
        "transaction_data": {
            "transaction_id": "tx_12345abcde",
            "timestamp": "2025-05-07T14:30:45Z",
            "amount": 129.99,
            "currency": "USD",
            "customer": {
            "id": "cust_98765zyxwv",
            "country": "US",
            "ip_address": "192.168.1.1"
            },
            "payment_method": {
            "type": "credit_card",
            "last_four": "4242",
            "country_of_issue": "CA"
            },
            "merchant": {
            "id": "merch_abcde12345",
            "name": "Example Store",
            "category": "electronics"
            }
            },
        "risk_score": 0.5,
        "recommended_action": "review",
        "created_at": "2025-05-07T14:30:45Z"
    }]
    
    mocker.patch("main.database_connection.DatabaseManager.get_all_analyses", 
                 return_value=mock_data)
    with client.application.app_context():
        response = client.get("/analyses", headers={"X-API-KEY": api_key})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['analyses']) > 0
        
        analysis = data['analyses'][0]
        assert analysis["transaction_id"] == "tx_12345abcde"
        assert analysis["risk_score"] == 0.5
        assert analysis["recommended_action"] == "review"

def test_get_admin_notifications(client, api_key, mocker):
    mock_data = [{
        "transaction_data": {
            "transaction_id": "tx_12345abcde",
            "timestamp": "2025-05-07T14:30:45Z",
            "amount": 129.99,
            "currency": "USD",
            "customer": {
            "id": "cust_98765zyxwv",
            "country": "US",
            "ip_address": "192.168.1.1"
            },
            "payment_method": {
            "type": "credit_card",
            "last_four": "4242",
            "country_of_issue": "CA"
            },
            "merchant": {
            "id": "merch_abcde12345",
            "name": "Example Store",
            "category": "electronics"
            }
            },
        "risk_score": 0.8,
        "risk_factors": '["factor1", "factor2"]',
        "llm_analysis": '{"reasoning": "High risk due to geographic anomalies"}'
    }]
    
    mocker.patch("main.database_connection.DatabaseManager.get_high_risk_analyses", 
                 return_value=mock_data)
    
    with client.application.app_context():
        # Make the request
        response = client.get("/admin/notifications", headers={"X-API-KEY": api_key})
        
        # Debug the response
        print(f"Response: {response}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {response.get_json()}")
        
        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None, "Response data should not be None"
        assert data['success'] is True, "Response should indicate success"
        assert 'notifications' in data, "Response should contain 'notifications' key"
        assert len(data['notifications']) > 0, "Notifications should not be empty"
        
        notification = data['notifications'][0]
        assert notification["alert_type"] == "high_risk_transaction"
        assert notification["risk_score"] == 0.8
        assert len(notification["risk_factors"]) > 0
        assert "transaction_details" in notification
        assert notification["transaction_details"]["transaction_id"] == "tx_12345abcde"