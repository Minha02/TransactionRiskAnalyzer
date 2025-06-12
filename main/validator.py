import logging

logger = logging.getLogger(__name__)

def validate_transaction(transaction: dict):
    json_schema_validator(transaction)
    transaction_id_validator(transaction)
    # Add additional validators as needed
    logger.info("Transaction validated successfully.")


def json_schema_validator(transaction: dict):
    required_fields = [
        "transaction_id", "timestamp", "amount", "currency",
        "customer", "payment_method", "merchant"
    ]
    for field in required_fields:
        if field not in transaction:
            raise ValueError(f"Missing required field: {field}")


def transaction_id_validator(transaction: dict):
    tx_id = transaction.get("transaction_id", "")
    if not isinstance(tx_id, str) or not tx_id.startswith("tx_"):
        raise ValueError("Invalid transaction_id format. Must start with 'tx_'.")
import logging

