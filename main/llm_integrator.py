from openai import OpenAI
import json
import os
from flask import abort
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def analyse_transaction(data):
    try:
        transaction_json = json.dumps(data, indent=2)
        prompt = f"""
            # Transaction Risk Analysis Prompt
            ## System Instructions
            You are a specialised financial risk analyst. Your task is to evaluate
            transaction data and determine a risk score from 0.0 (no risk) to 1.0
            (extremely high risk) based on patterns and indicators of potential fraud.
            You must also provide clear reasoning for your risk assessment.
            ## Response Format
            Respond in JSON format with the following structure:
            
            {{
            "risk_score": 0.0-1.0,
            "risk_factors": ["factor1", "factor2"...],
            "reasoning": "A brief explanation of your analysis",
            "recommended_action": "allow|review|block"
            }}
            
            ## Risk Factors to Consider
            1. **Geographic Anomalies**:
            - Transactions where the customer country differs from the payment
            method country

            - Transactions from high-risk countries (consider jurisdiction with
            weak AML controls)
            - IP address location inconsistent with the customer's country
            2. **Transaction Patterns**:
            - Unusual transaction amount for the merchant category
            - Transactions outside normal business hours for the merchant's
            location
            - Multiple transactions in short succession
            3. **Payment Method Indicators**:
            - Payment method type and associated risks
            - New payment methods have recently been added to accounts
            4. **Merchant Factors**:
            - Merchant category and typical fraud rates
            - Merchant's history and reputation
            ## Additional Guidelines
            - Assign higher risk scores to combinations of multiple risk factors
            - Consider the transaction amount - higher amounts generally warrant more
            scrutiny
            - Account for normal cross-border shopping patterns while flagging unusual
            combinations
            - Provide actionable reasoning that explains why the transaction received
            its risk score
            - Recommend "allow" for scores 0.0-0.3, "review" for scores 0.3-0.7, and
            "block" for scores 0.7-1.0
            ## Transaction Data
            {transaction_json}
            """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.choices[0].message.content

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            abort(500, description="LLM response is not valid JSON")

        required_keys = {"risk_score", "risk_factors", "reasoning", "recommended_action"}
        if not required_keys.issubset(result.keys()):
            abort(500, description="Malformed response from LLM: missing required fields")

        return result
    
    except Exception as e:
        abort(500, description=f"LLM integration failed openai: {str(e)}")