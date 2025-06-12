import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pytest
from main import create_app
from main.models import TransactionAnalysis
from main import db
import json
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def api_key():
    return os.getenv('SECRET_API_KEY', 'test-api-key')

@pytest.fixture
def sample_transaction():
    return {
        "transaction_id": "tx_12345",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 999.99,
        "currency": "USD",
        "customer": {
            "id": "cust_98765",
            "country": "US",
            "ip_address": "192.168.1.1"
        },
        "payment_method": {
            "type": "credit_card",
            "last_four": "4242",
            "country_of_issue": "CA"
        },
        "merchant": {
            "id": "merch_12345",
            "name": "Example Store",
            "category": "electronics"
        }
    }

def test_end_to_end_transaction_flow(client, api_key, sample_transaction):
    """Test the complete flow from transaction creation to analysis retrieval"""
    
    # Step 1: Create transaction and get analysis
    response = client.post(
        "/transaction",
        json=sample_transaction,
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert "message" in data
    assert "llm_result" in data
    
    # Verify LLM result structure
    llm_result = data["llm_result"]
    assert "risk_score" in llm_result
    assert "risk_factors" in llm_result
    assert "recommended_action" in llm_result
    
    # Step 2: Retrieve analyses
    response = client.get(
        "/analyses",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "analyses" in data
    analyses = data["analyses"]
    assert len(analyses) > 0
    
    # Verify the created transaction is in the analyses
    found_transaction = False
    for analysis in analyses:
        if analysis["transaction_id"] == sample_transaction["transaction_id"]:
            found_transaction = True
            assert "risk_score" in analysis
            assert "recommended_action" in analysis
            break
    
    assert found_transaction, "Created transaction not found in analyses"

def test_high_risk_notification_flow(client, api_key, sample_transaction):
    """Test the high-risk transaction notification flow"""
    
    # Modify transaction to be high risk (large amount)
    sample_transaction["amount"] = 50000.00
    
    # Create high-risk transaction
    response = client.post(
        "/transaction",
        json=sample_transaction,
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 201
    data = response.get_json()
    
    # Debug print initial response
    print("Initial transaction response:", json.dumps(data, indent=2))
    
    # Verify the transaction was flagged as high risk
    assert "llm_result" in data
    llm_result = data["llm_result"]
    risk_score = float(llm_result["risk_score"])
    print(f"Risk score: {risk_score}")
    assert risk_score > 0.6, f"Expected risk score > 0.6, got {risk_score}"
    
    # Add a longer delay to ensure notification processing
    import time
    time.sleep(2)
    
    # Check admin notifications with debug info
    print("\nChecking notifications...")
    response = client.get(
        "/admin/notifications",
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.get_json()
    print("Notifications endpoint response:", json.dumps(data, indent=2))
    
    assert data["success"] is True, "Notifications request was not successful"
    assert "notifications" in data, "No notifications key in response"
    
    notifications = data["notifications"]
    print(f"\nFound {len(notifications)} notifications")
    
    # Print each notification for debugging
    for idx, notif in enumerate(notifications):
        print(f"\nNotification {idx + 1}:")
        print(json.dumps(notif, indent=2))
    
    # Verify notification content
    found_notification = False
    for notification in notifications:
        if notification["transaction_details"]["transaction_id"] == sample_transaction["transaction_id"]:
            found_notification = True
            assert notification["alert_type"] == "high_risk_transaction"
            assert "risk_score" in notification
            assert "risk_factors" in notification
            print("\nFound matching notification:", json.dumps(notification, indent=2))
            break
    
    assert found_notification, "High-risk transaction notification not found"
def test_invalid_authentication(client, sample_transaction):
    """Test API authentication requirements"""
    
    # Test without API key
    response = client.post("/transaction", json=sample_transaction)
    assert response.status_code == 401
    
    # Test with invalid API key
    response = client.post(
        "/transaction",
        json=sample_transaction,
        headers={"X-API-KEY": "invalid-key"}
    )
    assert response.status_code == 403

def test_invalid_transaction_data(client, api_key):
    """Test transaction validation"""
    
    invalid_transaction = {
        "amount": 100,  # Missing required fields
        "currency": "USD"
    }
    
    response = client.post(
        "/transaction",
        json=invalid_transaction,
        headers={"X-API-KEY": api_key}
    )
    
    assert response.status_code == 422
    data = response.get_json()
    assert "error" in data