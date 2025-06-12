from .llm_int_deepseek import analyse_transaction_deepseek
from .database_connection import DatabaseManager
from .validator import validate_transaction
from flask import jsonify

def get_financial_risk_analysis(data,save_to_db=True):
    try:
        if not validate_transaction(data):
            raise ValueError("Invalid transaction data format")
                
        llm_response = analyse_transaction_deepseek(data)
        return jsonify({
            "message": "Transaction validated and analyzed.",
            "llm_result": llm_response
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


def get_risk_history():
    try:
        analyses = DatabaseManager.get_all_analyses()
        if analyses is None:
            return []
        return analyses
    except Exception as e:
        print(f"Error getting analyses: {str(e)}")
        return jsonify({"error": "Failed to retrieve analyses"}), 500

def get_high_risk_history():
    try:
        analyses = DatabaseManager.get_high_risk_analyses()
        if analyses is None:
            return []
        return analyses
    except Exception as e:
        print(f"Error getting analyses: {str(e)}")
        return jsonify({"error": "Failed to retrieve analyses"}), 500
