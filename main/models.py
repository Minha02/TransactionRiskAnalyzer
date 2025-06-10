from __init__ import db 
from datetime import datetime
import json 

class TransactionAnalysis(db.Model):
    __tablename__ = 'transaction_analyses'

    id = db.Column(db.Integer, primary_key= True)
    transaction_data = db.Column(db.Text, nullable = False)
    llm_response = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    recommended_action = db.Column(db.String(20), nullable=False, default='review')
    risk_factors = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        try:
            return {
                'id': self.id,
                'transaction_data': json.loads(self.transaction_data) if self.transaction_data else {},
                'llm_response': json.loads(self.llm_response) if self.llm_response else {},
                'risk_score': self.risk_score,
                'recommended_action': self.recommended_action,
                'risk_factors': json.loads(self.risk_factors) if self.risk_factors else [],
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in model {self.id}: {str(e)}")
            return {
                'id': self.id,
                'transaction_data': {},
                'llm_response': {},
                'risk_score': self.risk_score,
                'recommended_action': self.recommended_action,
                'risk_factors': [],
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'error': 'Data parsing error'
            }
    
def __repr__(self):
    return f'<TransactionAnalysis {self.id}: {self.recommended_action} (Risk: {self.risk_score})>'
