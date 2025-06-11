from flask import Blueprint, request, jsonify, abort
from get_financial_risk import get_financial_risk_analysis, get_risk_history, get_high_risk_history
from validator import validate_transaction
from database_connection import DatabaseManager
from llm_integrator import analyse_transaction
from llm_int_deepseek import analyse_transaction_deepseek
from authenticator import require_auth
import json

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


@main_bp.route("/admin/notifications", methods=["GET"])
@require_auth  # Optional: Secure it
def get_admin_notifications():
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        high_risk_analyses = DatabaseManager.get_high_risk_analyses(limit=limit, offset=offset)
        notifications = []

        for analysis in high_risk_analyses:
            # Safely parse fields only if they're strings
            transaction_data = analysis["transaction_data"]
            if isinstance(transaction_data, str):
                transaction_data = json.loads(transaction_data)

            risk_factors = analysis["risk_factors"]
            if isinstance(risk_factors, str):
                risk_factors = json.loads(risk_factors)

            llm_response = analysis["llm_response"]
            if isinstance(llm_response, str):
                llm_response = json.loads(llm_response)

            notifications.append({
                "alert_type": "high_risk_transaction",
                "transaction_id": transaction_data.get("transaction_id", ""),
                "risk_score": analysis["risk_score"],
                "risk_factors": risk_factors,
                "transaction_details": transaction_data,
                "llm_analysis": llm_response.get("reasoning", "N/A")
            })

        return jsonify({
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }), 200

    except Exception as e:
        abort(500, description=f"Failed to retrieve admin notifications: {str(e)}")
