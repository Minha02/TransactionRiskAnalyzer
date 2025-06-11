from datetime import datetime
import json
import logging
from typing import Dict, Any, List
from database_connection import DatabaseManager

class AdminNotificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def should_notify_admins(self, transaction: Dict[str, Any], llm_analysis: Dict[str, Any]) -> bool:
        """
        Determine if a transaction warrants admin notification based on LLM risk analysis
        """
        risk_score = llm_analysis.get('risk_score', 0.0)
        recommended_action = llm_analysis.get('recommended_action', 'allow').lower()
        
        # Notify admins for high-risk transactions
        high_risk_criteria = [
            risk_score >= 0.7,  # High risk score (block threshold)
            recommended_action in ['block', 'review'],
            risk_score >= 0.5 and transaction.get('amount', 0) > 5000,  # Medium risk + high amount
        ]
        
        return any(high_risk_criteria)
    
    def create_admin_notification(self, transaction: Dict[str, Any], llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create admin notification in the specified format
        """
        try:
            if not self.should_notify_admins(transaction, llm_analysis):
                return {'created': False, 'reason': 'Transaction does not meet notification criteria'}
            
            # Determine alert type based on risk score and action
            risk_score = llm_analysis.get('risk_score', 0.0)
            recommended_action = llm_analysis.get('recommended_action', 'allow')
            
            if risk_score >= 0.8 or recommended_action == 'block':
                alert_type = 'critical_risk_transaction'
                priority = 'critical'
            elif risk_score >= 0.7 or recommended_action == 'review':
                alert_type = 'high_risk_transaction'
                priority = 'high'
            elif risk_score >= 0.5:
                alert_type = 'medium_risk_transaction'
                priority = 'medium'
            else:
                alert_type = 'low_risk_transaction'
                priority = 'low'
            
            # Extract key transaction details
            transaction_id = transaction.get('transaction_id', f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            amount = transaction.get('amount', 0)
            currency = transaction.get('currency', 'USD')
            
            # Extract customer info
            customer = transaction.get('customer', {})
            customer_country = customer.get('country', 'Unknown')
            customer_ip = customer.get('ip_address', 'Unknown')
            
            # Extract payment method info
            payment_method = transaction.get('payment_method', {})
            payment_type = payment_method.get('type', 'Unknown')
            card_country = payment_method.get('country_of_issue', 'Unknown')
            
            # Extract merchant info
            merchant = transaction.get('merchant', {})
            merchant_name = merchant.get('name', 'Unknown')
            merchant_category = merchant.get('category', 'Unknown')
            
            # Create the notification in the specified format
            notification_data = {
                'alert_type': alert_type,
                'transaction_id': transaction_id,
                'risk_score': risk_score,
                'risk_factors': llm_analysis.get('risk_factors', []),
                'recommended_action': recommended_action,
                'reasoning': llm_analysis.get('reasoning', 'No reasoning provided'),
                'transaction_summary': {
                    'amount': f"{currency} {amount:,.2f}",
                    'customer_country': customer_country,
                    'payment_country': card_country,
                    'merchant_name': merchant_name,
                    'merchant_category': merchant_category,
                    'payment_type': payment_type,
                    'timestamp': transaction.get('timestamp', datetime.now().isoformat())
                },
                'geographic_flags': self.extract_geographic_flags(transaction),
                'transaction_details': transaction,  # Full transaction JSON
                'llm_analysis': llm_analysis.get('reasoning', 'Risk analysis completed'),
                'priority': priority,
                'status': 'unread',
                'created_at': datetime.now().isoformat(),
                'requires_immediate_action': recommended_action == 'block'
            }
            
            # Save to database
            notification_id = DatabaseManager.create_admin_notification(notification_data)
            
            self.logger.info(f"Admin notification created: {alert_type} for transaction {transaction_id}")
            
            return {
                'created': True,
                'notification_id': notification_id,
                'alert_type': alert_type,
                'priority': priority,
                'requires_immediate_action': notification_data['requires_immediate_action']
            }
            
        except Exception as e:
            self.logger.error(f"Error creating admin notification: {str(e)}")
            return {'created': False, 'error': str(e)}
    
    def extract_geographic_flags(self, transaction: Dict[str, Any]) -> List[str]:
        """Extract geographic risk indicators"""
        flags = []
        
        customer = transaction.get('customer', {})
        payment_method = transaction.get('payment_method', {})
        
        customer_country = customer.get('country', '')
        card_country = payment_method.get('country_of_issue', '')
        
        if customer_country and card_country and customer_country != card_country:
            flags.append(f"Cross-border: Customer in {customer_country}, Card from {card_country}")
        
        # Add high-risk country flags (you can customize this list)
        high_risk_countries = ['XX', 'YY']  # Replace with actual high-risk country codes
        if customer_country in high_risk_countries:
            flags.append(f"High-risk customer location: {customer_country}")
        
        if card_country in high_risk_countries:
            flags.append(f"High-risk card issuer country: {card_country}")
        
        return flags