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

def analyse_transaction_deepseek(data,save_to_db=True,prompt_file_path='transaction_risk_analysis_prompt.txt'):
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as file:
            prompt_template = file.read()

        prompt = prompt_template.replace('{transaction_data}', json.dumps(data))
        
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
