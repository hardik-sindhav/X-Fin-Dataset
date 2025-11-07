"""
Validation Utilities
Helper functions for request validation
"""

from flask import request, jsonify
from marshmallow import ValidationError
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def validate_request(schema_class, source='json'):
    """
    Decorator to validate request data using a Marshmallow schema
    
    Args:
        schema_class: Marshmallow Schema class
        source: Where to get data from - 'json', 'args', 'form', or 'query_string'
    
    Usage:
        @app.route('/api/endpoint')
        @validate_request(LoginSchema, source='json')
        def endpoint(validated_data):
            # validated_data contains validated and cleaned data
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get data from appropriate source
                if source == 'json':
                    data = request.get_json() or {}
                elif source == 'args':
                    data = request.args.to_dict()
                elif source == 'form':
                    data = request.form.to_dict()
                elif source == 'query_string':
                    data = request.args.to_dict()
                else:
                    data = {}
                
                # Create schema instance with context for cross-field validation
                schema = schema_class()
                
                # For date validation schemas, pass context for cross-field validation
                if 'Date' in schema_class.__name__ or 'PaginationDate' in schema_class.__name__:
                    schema.context = {'start_date': data.get('start_date')}
                
                validated_data = schema.load(data)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as err:
                logger.warning(f"Validation error: {err.messages}")
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'errors': err.messages
                }), 400
            except Exception as e:
                logger.error(f"Validation error: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'message': str(e)
                }), 400
        
        return decorated_function
    return decorator


def validate_query_params(schema_class):
    """
    Convenience decorator for validating query parameters
    
    Usage:
        @app.route('/api/endpoint')
        @validate_query_params(PaginationSchema)
        def endpoint(validated_data):
            page = validated_data.get('page', 1)
            pass
    """
    return validate_request(schema_class, source='args')


def validate_json_body(schema_class):
    """
    Convenience decorator for validating JSON request body
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_json_body(LoginSchema)
        def endpoint(validated_data):
            username = validated_data['username']
            pass
    """
    return validate_request(schema_class, source='json')


def validate_path_param(param_name, validator_func, error_message="Invalid parameter"):
    """
    Decorator to validate path parameters
    
    Args:
        param_name: Name of the path parameter
        validator_func: Function that takes the param value and returns True if valid
        error_message: Error message to return if validation fails
    
    Usage:
        @app.route('/api/data/<record_id>')
        @validate_path_param('record_id', ObjectId.is_valid, 'Invalid record ID')
        def endpoint(record_id):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            param_value = kwargs.get(param_name)
            if param_value and not validator_func(param_value):
                return jsonify({
                    'success': False,
                    'error': error_message
                }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

