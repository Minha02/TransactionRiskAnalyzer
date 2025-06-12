from flask import Blueprint, request, jsonify, abort
from .get_financial_risk import get_financial_risk_analysis, get_high_risk_history, get_risk_history
from .validator import validate_transaction
from .llm_integrator import analyse_transaction
from .llm_int_deepseek import analyse_transaction_deepseek
from .authenticator import require_auth
import json

main_bp = Blueprint('main', __name__)

@main_bp.route("/transaction", methods=["POST"])
@require_auth
def create_transaction():
    try:
        # Get and validate transaction data
        transaction = request.get_json(force=True)
        validate_transaction(transaction)
        
        # Analyze the transaction
        llm_response = analyse_transaction_deepseek(transaction)
        
        # Save to database if successful
        get_financial_risk_analysis(transaction, save_to_db=True)
        
        return jsonify({
            "message": "Transaction validated and analyzed.",
            "llm_result": llm_response
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422
    except Exception as e:
        print(f"Error in create_transaction: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500
    
@main_bp.route("/analyses", methods=["GET"])
@require_auth
def get_analyses():
    try:
        analyses = get_risk_history()
        if analyses is None:
            analyses = []

        transformed_analyses = []
        for analysis in analyses:
            transaction_data = analysis.get("transaction_data", {})
            if isinstance(transaction_data, str):
                transaction_data = json.loads(transaction_data)

            transformed_analyses.append({
                "transaction_id": transaction_data.get("transaction_id", ""),
                "risk_score": analysis.get("risk_score", 0.0),
                "recommended_action": analysis.get("recommended_action", ""),
                "created_at": analysis.get("created_at", ""),
                "transaction_details": transaction_data
            })

        return jsonify({
            'success': True,
            'analyses': transformed_analyses,
            'count': len(transformed_analyses)
        })
        
    except Exception as e:
        abort(500, description=f"Failed to retrieve analyses: {str(e)}")


@main_bp.route("/admin/notifications", methods=["GET"])
@require_auth  
def get_admin_notifications():
    try:

        high_risk_analyses = get_high_risk_history()
        if high_risk_analyses is None:
            high_risk_analyses = []
        notifications = []

        for analysis in high_risk_analyses:
            try:
                transaction_data = analysis.get("transaction_data", "{}")
                if isinstance(transaction_data, str):
                    transaction_data = json.loads(transaction_data)

                risk_factors = analysis.get("risk_factors", "[]")
                if isinstance(risk_factors, str):
                    risk_factors = json.loads(risk_factors)

                llm_response = analysis.get("llm_response", "{}")
                if isinstance(llm_response, str):
                    llm_response = json.loads(llm_response)

                notifications.append({
                    "alert_type": "high_risk_transaction",
                    "transaction_id": transaction_data.get("transaction_id", ""),
                    "risk_score": float(analysis.get("risk_score", 0.0)),
                    "risk_factors": risk_factors,
                    "transaction_details": transaction_data,
                    "llm_analysis": llm_response.get("reasoning", "N/A"),
                    "created_at": analysis.get("created_at", "")
                })  
            except json.JSONDecodeError as je:
                print(f"JSON parsing error for analysis: {str(je)}")
                continue
            except Exception as e:
                print(f"Error processing analysis: {str(e)}")
                continue

        return jsonify({
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }), 200

    except Exception as e:
        abort(500, description=f"Failed to retrieve admin notifications: {str(e)}")
