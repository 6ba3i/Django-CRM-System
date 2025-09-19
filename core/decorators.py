 # Custom decorators
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
import logging
import time

logger = logging.getLogger(__name__)

def firebase_auth_required(view_func):
    """Decorator to check Firebase authentication"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for Firebase auth token in headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            # Here you would verify the Firebase token
            # token = auth_header.split('Bearer ')[1]
            # decoded_token = auth.verify_id_token(token)
            # request.firebase_user = decoded_token
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Firebase auth error: {e}")
            return JsonResponse({'error': 'Invalid authentication'}, status=401)
    
    return _wrapped_view

def role_required(*roles):
    """Decorator to check user roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def log_activity(activity_type):
    """Decorator to log user activities"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            start_time = time.time()
            
            # Log the activity start
            logger.info(f"Activity started: {activity_type} by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
            
            try:
                response = view_func(request, *args, **kwargs)
                
                # Log successful completion
                execution_time = time.time() - start_time
                logger.info(f"Activity completed: {activity_type} in {execution_time:.2f}s")
                
                return response
            except Exception as e:
                # Log errors
                logger.error(f"Activity failed: {activity_type} - Error: {str(e)}")
                raise
        
        return _wrapped_view
    return decorator

def cache_result(timeout=300):
    """Decorator to cache function results"""
    def decorator(view_func):
        cache = {}
        
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{view_func.__name__}_{args}_{kwargs}"
            
            # Check if result is in cache and not expired
            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]
                if time.time() - cached_time < timeout:
                    return cached_result
            
            # Call the function and cache the result
            result = view_func(request, *args, **kwargs)
            cache[cache_key] = (result, time.time())
            
            return result
        
        return _wrapped_view
    return decorator

def validate_json_request(required_fields):
    """Decorator to validate JSON request data"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    import json
                    data = json.loads(request.body)
                    
                    # Check for required fields
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return JsonResponse({
                            'error': f'Missing required fields: {", ".join(missing_fields)}'
                        }, status=400)
                    
                    request.json_data = data
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def rate_limit(max_requests=100, time_window=3600):
    """Decorator to implement rate limiting"""
    def decorator(view_func):
        request_counts = {}
        
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get client identifier (IP address or user ID)
            client_id = request.META.get('REMOTE_ADDR')
            if request.user.is_authenticated:
                client_id = f"user_{request.user.id}"
            
            current_time = time.time()
            
            # Clean old entries
            request_counts[client_id] = [
                timestamp for timestamp in request_counts.get(client_id, [])
                if current_time - timestamp < time_window
            ]
            
            # Check rate limit
            if len(request_counts.get(client_id, [])) >= max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.'
                }, status=429)
            
            # Add current request
            if client_id not in request_counts:
                request_counts[client_id] = []
            request_counts[client_id].append(current_time)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

# Admin-only decorator using Django's built-in functionality
admin_required = user_passes_test(lambda u: u.is_staff)

# Manager-only decorator
manager_required = role_required('Admin', 'Manager')