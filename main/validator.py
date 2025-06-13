import logging

logger = logging.getLogger(__name__)

def validate_transaction(transaction: dict):
    if transaction is None:
        raise ValueError("Transaction cannot be None")
    json_schema_validator(transaction)
    transaction_id_validator(transaction)
    nested_fields_validator(transaction)
    logger.info("Transaction validated successfully.")
    return True

def json_schema_validator(transaction: dict):
    required_fields = [
        "transaction_id", "timestamp", "amount", "currency",
        "customer", "payment_method", "merchant"
    ]
    for field in required_fields:
        if field not in transaction:
            raise ValueError(f"Missing required field: {field}")


def nested_fields_validator(transaction: dict):
    """Validate nested fields in the transaction"""
    # Customer fields
    required_customer_fields = ["id", "country", "ip_address"]
    for field in required_customer_fields:
        if field not in transaction["customer"]:
            raise ValueError(f"Missing required customer field: {field}")
            
    # Payment method fields
    required_payment_fields = ["type", "last_four", "country_of_issue"]
    for field in required_payment_fields:
        if field not in transaction["payment_method"]:
            raise ValueError(f"Missing required payment_method field: {field}")
            
    # Merchant fields
    required_merchant_fields = ["id", "name", "category"]
    for field in required_merchant_fields:
        if field not in transaction["merchant"]:
            raise ValueError(f"Missing required merchant field: {field}")


def transaction_id_validator(transaction: dict):
    tx_id = transaction.get("transaction_id", "")
    if not isinstance(tx_id, str) or not tx_id.startswith("tx_"):
        raise ValueError("Invalid transaction_id format. Must start with 'tx_'.")
import logging

