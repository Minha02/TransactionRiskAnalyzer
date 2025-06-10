import os
import json
import requests
from flask import abort
from dotenv import load_dotenv
from database_connection import DatabaseManager

load_dotenv() 
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
API_KEY = os.getenv("DEEPSEEK_API_KEY")
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def analyse_transaction_deepseek(data,save_to_db=True):
    try:
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
            "risk_factors": ["factor1", "factor2", ...],
            "reasoning": "short explanation",
            "recommended_action": "allow | review | block"
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
            {json.dumps(data)}
        """

        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        # Send the POST request to the DeepSeek API
        response = requests.post(API_URL, json=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Error code: {response.status_code} - {response.text}")

        print(f"Raw Response: {response.text}")

        response_json = response.json()
        if "choices" not in response_json or not response_json["choices"]:
            raise Exception("Malformed API response: 'choices' key missing or empty")


        result_text = response.json()["choices"][0]["message"]["content"]
        print(f"Result Text: {result_text}")

        # Remove Markdown formatting (```json ... ```)
        if result_text.startswith("```json"):
            result_text = result_text.strip("```json").strip("```").strip()


        if not result_text.strip():
            raise Exception("Empty result text from API")

        # Parse the JSON content from the response
        result = json.loads(result_text)

        print(f"Parsed Result: {result}")

        if "risk_score" not in result or "recommended_action" not in result:
            abort(500, description="Malformed response from LLM")

        if save_to_db:
            try:
                analysis_id = DatabaseManager.save_transaction_analysis(data, result)
                result['analysis_id'] = analysis_id
                print(f"💾 Saved to database with ID: {analysis_id}")
            except Exception as db_error:
                print(f"⚠️ Database save failed: {str(db_error)}")
                # Continue without failing the entire request


        return result

    except Exception as e:
        abort(500, description=f"LLM integration failed deepseek: {str(e)}")
