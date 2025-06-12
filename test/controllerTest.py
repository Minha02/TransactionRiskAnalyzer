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
from main.validator import validate_transaction, json_schema_validator, transaction_id_validator
import time

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

def test_multiple_high_risk_transactions(client, api_key):
    """Test system's ability to handle and return multiple high-risk transactions"""
    
    # Create 3 high-risk transactions with different characteristics
    high_risk_transactions = [
        {
            "transaction_id": "tx_high_risk_1",
            "timestamp": "2025-05-07T14:30:45Z",
            "amount": 50000.00,  # High amount
            "currency": "USD",
            "customer": {
                "id": "cust_98765",
                "country": "US",
                "ip_address": "192.168.1.1"
            },
            "payment_method": {
                "type": "credit_card",
                "last_four": "4242",
                "country_of_issue": "CA"  # Cross-border payment
            },
            "merchant": {
                "id": "merch_12345",
                "name": "Example Store",
                "category": "electronics"
            }
        },
        {
            "transaction_id": "tx_high_risk_2",
            "timestamp": "2025-05-07T02:30:45Z",  # Unusual hour
            "amount": 15000.00,  # Moderately high amount
            "currency": "USD",
            "customer": {
                "id": "cust_98766",
                "country": "US",
                "ip_address": "202.51.33.45"  # IP mismatch with country
            },
            "payment_method": {
                "type": "credit_card",
                "last_four": "1111",
                "country_of_issue": "US"
            },
            "merchant": {
                "id": "merch_12345",
                "name": "Example Store",
                "category": "electronics"
            }
        },
        {
            "transaction_id": "tx_high_risk_3",
            "timestamp": "2025-05-07T18:30:45Z",
            "amount": 9999.99,
            "currency": "EUR",  # Different currency
            "customer": {
                "id": "cust_98767",
                "country": "FR",  # Foreign customer
                "ip_address": "81.29.134.7"
            },
            "payment_method": {
                "type": "credit_card",
                "last_four": "9876",
                "country_of_issue": "UK"  # Cross-border payment
            },
            "merchant": {
                "id": "merch_12345",
                "name": "Example Store",
                "category": "electronics"
            }
        }
    ]
    
    # Submit all high-risk transactions
    transaction_ids = []
    for tx in high_risk_transactions:
        response = client.post(
            "/transaction",
            json=tx,
            headers={"X-API-KEY": api_key}
        )
        assert response.status_code == 201
        transaction_ids.append(tx["transaction_id"])
        
    # Allow time for processing
    time.sleep(2)
    
    # Check admin notifications
    response = client.get(
        "/admin/notifications",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "notifications" in data
    
    # Verify we have all 3 high-risk notifications
    notifications = data["notifications"]
    found_transactions = set()
    
    for notification in notifications:
        tx_id = notification["transaction_details"]["transaction_id"]
        if tx_id in transaction_ids:
            found_transactions.add(tx_id)
            assert notification["alert_type"] == "high_risk_transaction"
            assert "risk_score" in notification
            assert "risk_factors" in notification
    
    # Make sure we found all 3 transactions
    assert len(found_transactions) == 3, f"Expected 3 high-risk notifications, found {len(found_transactions)}"
    
    # Verify we can retrieve the high-risk transactions through the analysis endpoint
    response = client.get(
        "/analyses?risk_level=high",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    
    # Verify the analyses contain our high-risk transactions
    high_risk_analyses = data["analyses"]
    assert len(high_risk_analyses) >= 3, "Not all high-risk transactions were returned"
    
    found_in_analyses = set()
    for analysis in high_risk_analyses:
        if analysis["transaction_id"] in transaction_ids:
            found_in_analyses.add(analysis["transaction_id"])
            assert float(analysis["risk_score"]) > 0.6
    
    assert len(found_in_analyses) == 3, "Not all high-risk transactions were found in analyses endpoint"

def test_no_high_risk_transactions(client, api_key):
    """Test system behavior when there are no high-risk transactions"""
    
    # Create a low-risk transaction
    low_risk_transaction = {
        "transaction_id": "tx_low_risk",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 49.99,  # Low amount
        "currency": "USD",
        "customer": {
            "id": "cust_12345",
            "country": "US",
            "ip_address": "192.168.1.1"
        },
        "payment_method": {
            "type": "credit_card",
            "last_four": "4242",
            "country_of_issue": "US"  # Same country as customer
        },
        "merchant": {
            "id": "merch_12345",
            "name": "Coffee Shop",
            "category": "food"
        }
    }
    
    # Submit the low-risk transaction
    response = client.post(
        "/transaction",
        json=low_risk_transaction,
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 201
    data = response.get_json()
    
    # Verify the transaction was classified as low risk
    assert "llm_result" in data
    llm_result = data["llm_result"]
    risk_score = float(llm_result["risk_score"])
    assert risk_score <= 0.6, f"Expected risk score <= 0.6, got {risk_score}"
    
    # Allow time for processing
    time.sleep(1)
    
    # Check that no high-risk notifications were created
    response = client.get(
        "/admin/notifications",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "notifications" in data
    
    # Look for our transaction ID in notifications (should not be there)
    notifications = data["notifications"]
    for notification in notifications:
        if notification.get("transaction_details", {}).get("transaction_id") == low_risk_transaction["transaction_id"]:
            assert False, "Low-risk transaction incorrectly generated a notification"
    
    # Check for high-risk transactions through the analyses endpoint
    response = client.get(
        "/analyses?risk_level=high",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    
    # Either we should get an empty list or our low-risk transaction should not be included
    high_risk_analyses = data["analyses"]
    for analysis in high_risk_analyses:
        assert analysis["transaction_id"] != low_risk_transaction["transaction_id"], "Low-risk transaction incorrectly classified as high risk"