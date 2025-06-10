import logging

logger = logging.getLogger(__name__)

def validate_transaction(transaction: dict):
    """
    Master validation function to orchestrate all checks.
    Raises ValueError if any validation fails.
    """
    json_schema_validator(transaction)
    transaction_id_validator(transaction)
    # Add additional validators as needed
    logger.info("Transaction validated successfully.")


def json_schema_validator(transaction: dict):
    """
    Ensures all required fields exist in the transaction dictionary.
    """
    required_fields = [
        "transaction_id", "timestamp", "amount", "currency",
        "customer", "payment_method", "merchant"
    ]
    for field in required_fields:
        if field not in transaction:
            raise ValueError(f"Missing required field: {field}")


def transaction_id_validator(transaction: dict):
    """
    Validates that the transaction ID exists and follows the expected format.
    """
    tx_id = transaction.get("transaction_id", "")
    if not isinstance(tx_id, str) or not tx_id.startswith("tx_"):
        raise ValueError("Invalid transaction_id format. Must start with 'tx_'.")
import logging

logger = logging.getLogger(__name__)

def validate_transaction(transaction: dict):
    """
    Master validation function to orchestrate all checks.
    Raises ValueError if any validation fails.
    """
    json_schema_validator(transaction)
    transaction_id_validator(transaction)
    # Add additional validators as needed
    logger.info("Transaction validated successfully.")


def json_schema_validator(transaction: dict):
    """
    Ensures all required fields exist in the transaction dictionary.
    """
    required_fields = [
        "transaction_id", "timestamp", "amount", "currency",
        "customer", "payment_method", "merchant"
    ]
    for field in required_fields:
        if field not in transaction:
            raise ValueError(f"Missing required field: {field}")


def transaction_id_validator(transaction: dict):
    """
    Validates that the transaction ID exists and follows the expected format.
    """
    tx_id = transaction.get("transaction_id", "")
    if not isinstance(tx_id, str) or not tx_id.startswith("tx_"):
        raise ValueError("Invalid transaction_id format. Must start with 'tx_'.")
