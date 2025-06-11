from flask import Blueprint, request, jsonify, abort
from get_financial_risk import get_financial_risk_analysis, get_risk_history, get_high_risk_history
from validator import validate_transaction
from database_connection import DatabaseManager
from llm_integrator import analyse_transaction
from llm_int_deepseek import analyse_transaction_deepseek
from authenticator import require_auth

main_bp = Blueprint('main', __name__)

@main_bp.route("/transaction", methods=["POST"])
@require_auth
def create_transaction():
    try:
        transaction = request.get_json(force=True)
        validate_transaction(transaction)
        # Here, you could add code to save or process the transaction

        #return jsonify({"message": "Transaction validated and processed successfully."}), 201
    
        llm_response = analyse_transaction_deepseek(transaction)
        return jsonify({
            "message": "Transaction validated and analyzed.",
            "llm_result": llm_response
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    
@main_bp.route("/analyses", methods=["GET"])
#@require_auth
def get_analyses():
    try:
        limit = request.args.get('limit',50, type=int)
        offset = request.args.get('offset', 0, type=int)

        analyses = DatabaseManager.get_all_analyses(limit=limit, offset=offset)

        return jsonify({
            'success': True,
            'analyses': analyses,
            'count': len(analyses)
        })
        
    except Exception as e:
        abort(500, description=f"Failed to retrieve analyses: {str(e)}")
