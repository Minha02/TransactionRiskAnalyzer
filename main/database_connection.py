from main import db
from .models import TransactionAnalysis
import json
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class DatabaseManager:
    @staticmethod
    def save_transaction_analysis(transaction_data, llm_response):
        try:
            analysis = TransactionAnalysis(
                transaction_data=json.dumps(transaction_data) if isinstance(transaction_data, dict) else transaction_data,
                llm_response=json.dumps(llm_response) if isinstance(llm_response, dict) else llm_response,
                risk_score=llm_response.get('risk_score', 0.0) if isinstance(llm_response, dict) else 0.0,
                recommended_action=llm_response.get('recommended_action', 'review') if isinstance(llm_response, dict) else 'review',
                risk_factors=json.dumps(llm_response.get('risk_factors', [])) if isinstance(llm_response, dict) else '[]'
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            print(f"Saved transaction analysis with ID: {analysis.id}")
            return analysis.id
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f" Database error: {str(e)}")
            raise Exception(f"Failed to save transaction analysis: {str(e)}")
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error: {str(e)}")
            raise

    @staticmethod
    def get_transaction_analysis(analysis_id):
        try:
            analysis = TransactionAnalysis.query.get(analysis_id)
            if not analysis:
                return None
            return analysis.to_dict()
        except Exception as e:
            print(f"Error retrieving analysis {analysis_id}: {str(e)}")
            return None

    @staticmethod
    def get_all_analyses(limit=100, offset=0):
        try:
            analyses = TransactionAnalysis.query.order_by(
                TransactionAnalysis.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [analysis.to_dict() for analysis in analyses]
        except Exception as e:
            print(f"Error retrieving analyses: {str(e)}")
            return []
        
    @staticmethod
    def get_high_risk_analyses():
        try:
            analyses = TransactionAnalysis.query.filter(
                TransactionAnalysis.risk_score > 0.7
            ).order_by(TransactionAnalysis.created_at.desc()).all()

            return [analysis.to_dict() for analysis in analyses]
        except Exception as e:
            print(f"Error retrieving high-risk analyses: {str(e)}")
            return []


    

    

    