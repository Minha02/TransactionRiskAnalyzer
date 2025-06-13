import os
from importlib import resources
import json
import requests
from flask import abort
from dotenv import load_dotenv
from .database_connection import DatabaseManager

load_dotenv() 
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
API_KEY = os.getenv("DEEPSEEK_API_KEY2")
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def get_prompt_path():
    """Get the path to the prompt file regardless of how the package is installed"""
    try:
        with resources.files('main').joinpath('transaction_risk_analysis_prompt.txt') as path:
            return str(path)
    except (ImportError, TypeError):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'transaction_risk_analysis_prompt.txt')


def analyse_transaction_deepseek(data,save_to_db=True,prompt_file_path='transaction_risk_analysis_prompt.txt'):
    try:
        prompt_file_path = get_prompt_path()

        with open(prompt_file_path, 'r', encoding='utf-8') as file:
            prompt_template = file.read()
        prompt = prompt_template.replace('{transaction_data}', json.dumps(data))
        
        data_prompt = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(API_URL, json=data_prompt, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Error code: {response.status_code} - {response.text}")
        
        response_json = response.json()
        if "choices" not in response_json or not response_json["choices"]:
            raise Exception("Malformed API response: 'choices' key missing or empty")


        result_text = response.json()["choices"][0]["message"]["content"]

        if result_text.startswith("```json"):
            result_text = result_text.strip("```json").strip("```").strip()

        if not result_text.strip():
            raise Exception("Empty result text from API")

        result = json.loads(result_text)
        if "risk_score" not in result or "recommended_action" not in result:
            abort(500, description="Malformed response from LLM")

        if save_to_db:
            try:
                analysis_id = DatabaseManager.save_transaction_analysis(data, result)
                result['analysis_id'] = analysis_id
                print(f"Saved to database with ID: {analysis_id}")
            except Exception as db_error:
                print(f"Database save failed: {str(db_error)}")

        return result

    except Exception as e:
        abort(500, description=f"LLM integration failed deepseek: {str(e)}")
