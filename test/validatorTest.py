import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pytest
from main.validator import validate_transaction, json_schema_validator, transaction_id_validator

@pytest.fixture
def valid_transaction():
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

def test_valid_transaction(valid_transaction):
    """Test that a valid transaction passes validation"""
    try:
        validate_transaction(valid_transaction)
    except ValueError:
        pytest.fail("Valid transaction raised ValueError unexpectedly")

def test_missing_required_fields():
    """Test that missing required fields raise ValueError"""
    invalid_transaction = {
        "amount": 100,
        "currency": "USD"
    }
    
    with pytest.raises(ValueError) as exc_info:
        json_schema_validator(invalid_transaction)
    assert "Missing required field" in str(exc_info.value)

def test_invalid_transaction_id_format():
    """Test that invalid transaction ID format raises ValueError"""
    invalid_transaction = {
        "transaction_id": "invalid_12345",  # Doesn't start with tx_
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
    
    with pytest.raises(ValueError) as exc_info:
        transaction_id_validator(invalid_transaction)
    assert "Invalid transaction_id format" in str(exc_info.value)

def test_missing_nested_fields():
    """Test that missing nested required fields raise ValueError"""
    invalid_transaction = {
        "transaction_id": "tx_12345",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 999.99,
        "currency": "USD",
        "customer": {
            # Missing required customer fields
        },
        "payment_method": {
            # Missing required payment method fields
        },
        "merchant": {
            # Missing required merchant fields
        }
    }
    
    with pytest.raises(ValueError) as exc_info:
        validate_transaction(invalid_transaction)
    assert "Missing required" in str (exc_info); "field" in str(exc_info.value)
  
def test_empty_transaction():
    """Test that an empty transaction raises ValueError"""
    with pytest.raises(ValueError) as exc_info:
        json_schema_validator({})
    assert "Missing required field" in str(exc_info.value)

def test_none_transaction():
    """Test that None transaction raises ValueError"""
    with pytest.raises(ValueError) as exc_info:
        validate_transaction(None)
    assert "Transaction cannot be None" in str(exc_info.value)

def test_nested_field_validation():
    """Test validation of specific nested fields"""
    invalid_customer = {
        "transaction_id": "tx_12345",
        "timestamp": "2025-05-07T14:30:45Z",
        "amount": 999.99,
        "currency": "USD",
        "customer": {
            "country": "US",  # Missing id
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
    
    with pytest.raises(ValueError) as exc_info:
        validate_transaction(invalid_customer)
    assert "Missing required customer field: id" in str(exc_info.value)

