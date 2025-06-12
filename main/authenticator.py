from functools import wraps
from flask import request, abort
import os
from dotenv import load_dotenv

load_dotenv()

API_SECRET = os.getenv("SECRET_API_KEY")

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')

        if not api_key:
            abort(401, description="API key required")
        
        if api_key != API_SECRET:
            abort(403, description="Invalid API key")
        
        return f(*args, **kwargs)
    
    return decorated_function