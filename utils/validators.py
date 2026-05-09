"""
Input Validation Utilities for API Endpoints

Provides decorators and functions for validating JSON requests.
"""

from functools import wraps
from flask import request, jsonify
import json


class ValidationError(Exception):
    """Custom validation exception"""
    pass


# Basic type validators
VALIDATORS = {
    'email': lambda v: isinstance(v, str) and '@' in v and '.' in v,
    'string': lambda v: isinstance(v, str) and len(v) > 0,
    'integer': lambda v: isinstance(v, int),
    'float': lambda v: isinstance(v, (int, float)),
    'boolean': lambda v: isinstance(v, bool),
    'datetime': lambda v: isinstance(v, str),  # Simplified
    'uuid': lambda v: isinstance(v, str) and len(v) == 36,
}


def validate_json_schema(schema):
    """
    Decorator to validate incoming JSON against schema.
    
    Schema format:
    {
        'field_name': {
            'type': 'email|string|integer|float|boolean|datetime|uuid',
            'required': True/False,
            'min_length': int,
            'max_length': int
        }
    }
    
    Usage:
    @app.route('/api/users', methods=['POST'])
    @validate_json_schema({
        'email': {'type': 'email', 'required': True},
        'name': {'type': 'string', 'required': True, 'min_length': 2}
    })
    def create_user():
        data = request.get_json()
        ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            
            try:
                # Check required fields and types
                for field, rules in schema.items():
                    value = data.get(field)
                    required = rules.get('required', False)
                    field_type = rules.get('type')
                    
                    # Check if required
                    if required and (value is None or value == ''):
                        raise ValidationError(f"Field '{field}' is required")
                    
                    # Skip validation if not required and empty
                    if not required and (value is None or value == ''):
                        continue
                    
                    # Validate type
                    if value is not None and field_type in VALIDATORS:
                        if not VALIDATORS[field_type](value):
                            raise ValidationError(f"Field '{field}' has invalid type (expected {field_type})")
                    
                    # Validate string length
                    if isinstance(value, str):
                        if 'min_length' in rules and len(value) < rules['min_length']:
                            raise ValidationError(
                                f"Field '{field}' must be at least {rules['min_length']} characters"
                            )
                        if 'max_length' in rules and len(value) > rules['max_length']:
                            raise ValidationError(
                                f"Field '{field}' must be at most {rules['max_length']} characters"
                            )
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                return jsonify({"error": f"Validation error: {str(e)}"}), 400
        
        return decorated_function
    return decorator


def validate_required_fields(*fields):
    """
    Simple decorator to check if required fields exist.
    
    Usage:
    @validate_required_fields('email', 'password')
    def login():
        ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            
            missing = [field for field in fields if field not in data or data[field] == '']
            
            if missing:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing)}"
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Common validation functions
def validate_email(email):
    """Check if email is valid"""
    import re
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """Check if password meets requirements (min 8 chars)"""
    return isinstance(password, str) and len(password) >= 8


def validate_phone(phone):
    """Check if phone is valid (basic: digits and +)"""
    import re
    pattern = r'^[+\d\-\s()]*$'
    return bool(re.match(pattern, phone))


def validate_uuid(uuid_string):
    """Check if valid UUID format"""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string, re.IGNORECASE))


# Request sanitizers
def sanitize_string(s, max_length=None):
    """Remove whitespace and optionally limit length"""
    if not isinstance(s, str):
        return s
    s = s.strip()
    if max_length:
        s = s[:max_length]
    return s


def sanitize_email(email):
    """Normalize email (lowercase, strip)"""
    if isinstance(email, str):
        return email.strip().lower()
    return email
