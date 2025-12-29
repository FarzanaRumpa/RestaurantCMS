from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def validate_required_fields(data, required_fields):
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return {'error': f'Missing required fields: {", ".join(missing)}'}, 400
    return None

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def json_response(data=None, message=None, status=200):
    response = {}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return jsonify(response), status

def error_response(message, status=400):
    return jsonify({'error': message}), status

