from llm_int_deepseek import analyse_transaction_deepseek
from database_connection import DatabaseManager
from validator import validate_transaction

def get_financial_risk_analysis(data,save_to_db=True):
    try:
        if not validate_transaction(data):
            raise ValueError("Invalid transaction data format")
        
        print("🔍 Starting financial risk analysis...")
        
        # Get LLM analysis
        result = analyse_transaction_deepseek(data, save_to_db=save_to_db)

        print("✅ Risk analysis completed successfully")
        return result
        
    except Exception as e:
        print(f"❌ Risk analysis failed: {str(e)}")
        raise


def get_risk_history(limit=50):
    """Get historical risk analyses"""
    return DatabaseManager.get_all_analyses(limit=limit)

def get_high_risk_history(threshold=0.7, limit=25):
    """Get high-risk transaction history"""
    return DatabaseManager.get_high_risk_transactions(threshold, limit)
