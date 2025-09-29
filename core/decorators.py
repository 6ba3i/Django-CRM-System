# Custom decorators for CRM system
from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect
from django.contrib import messages
import json
import hashlib
import time
from datetime import datetime
from typing import List, Callable, Any

def role_required(*roles: str):
    """
    Decorator to check if user has required role.
    Usage: @role_required('Admin', 'Manager')
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # For simplicity, check if user is staff for Admin/Manager roles
            user_roles = []
            if request.user.is_superuser:
                user_roles = ['Admin', 'Manager', 'User']
            elif request.user.is_staff:
                user_roles = ['Manager', 'User']
            else:
                user_roles = ['User']
            
            # Check if user has any of the required roles
            if any(role in user_roles for role in roles):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
        
        return _wrapped_view
    return decorator

def log_activity(activity_type: str):
    """
    Decorator to log user activities.
    Usage: @log_activity('view_customers')
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Log the activity (in a real app, this would go to a database)
            activity_log = {
                'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                'activity': activity_type,
                'timestamp': datetime.now().isoformat(),
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
            
            # Store in cache for now (in production, use proper logging/database)
            cache_key = f"activity_{request.user.id}_{int(time.time())}"
            cache.set(cache_key, activity_log, timeout=86400)  # 24 hours
            
            # Execute the view
            response = view_func(request, *args, **kwargs)
            
            # Add activity to response headers for debugging
            if hasattr(response, '__setitem__'):
                response['X-Activity-Logged'] = activity_type
            
            return response
        
        return _wrapped_view
    return decorator

def cache_result(timeout: int = 300):
    """
    Decorator to cache view results.
    Usage: @cache_result(timeout=600)
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Create cache key from view name, args, kwargs, and user
            cache_data = {
                'view': view_func.__name__,
                'args': str(args),
                'kwargs': str(kwargs),
                'user': request.user.id if request.user.is_authenticated else 0,
                'get_params': str(sorted(request.GET.items()))
            }
            cache_key = 'view_cache_' + hashlib.md5(
                json.dumps(cache_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # Return cached response
                if isinstance(cached_result, dict):
                    return JsonResponse(cached_result)
                else:
                    return HttpResponse(cached_result)
            
            # Execute view and cache result
            response = view_func(request, *args, **kwargs)
            
            # Cache the response content
            if isinstance(response, JsonResponse):
                cache.set(cache_key, json.loads(response.content), timeout=timeout)
            elif isinstance(response, HttpResponse):
                cache.set(cache_key, response.content, timeout=timeout)
            
            return response
        
        return _wrapped_view
    return decorator

def validate_json_request(required_fields: List[str] = None):
    """
    Decorator to validate JSON request data.
    Usage: @validate_json_request(['name', 'email'])
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)
            
            try:
                request.json = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            # Check required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in request.json or not request.json[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    return JsonResponse({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }, status=400)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def rate_limit(max_requests: int = 100, window: int = 3600):
    """
    Simple rate limiting decorator.
    Usage: @rate_limit(max_requests=50, window=3600)  # 50 requests per hour
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get client IP
            client_ip = get_client_ip(request)
            
            # Create rate limit key
            rate_key = f"rate_limit_{view_func.__name__}_{client_ip}"
            
            # Get current count
            current_count = cache.get(rate_key, 0)
            
            if current_count >= max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.'
                }, status=429)
            
            # Increment count
            cache.set(rate_key, current_count + 1, timeout=window)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def require_permissions(*permissions: str):
    """
    Decorator to check specific Django permissions.
    Usage: @require_permissions('customers.add_customer', 'customers.change_customer')
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Check if user has all required permissions
            if not all(request.user.has_perm(perm) for perm in permissions):
                messages.error(request, "You don't have the required permissions.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def ajax_required(view_func: Callable) -> Callable:
    """
    Decorator to ensure request is AJAX.
    Usage: @ajax_required
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def measure_performance(view_func: Callable) -> Callable:
    """
    Decorator to measure view performance.
    Usage: @measure_performance
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        start_time = time.time()
        
        response = view_func(request, *args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log performance (in production, use proper logging)
        perf_log = {
            'view': view_func.__name__,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'user': request.user.username if request.user.is_authenticated else 'Anonymous'
        }
        
        # Store performance data
        cache_key = f"perf_{view_func.__name__}_{int(time.time())}"
        cache.set(cache_key, perf_log, timeout=86400)
        
        # Add performance header
        if hasattr(response, '__setitem__'):
            response['X-Execution-Time'] = f"{execution_time:.3f}s"
        
        return response
    
    return _wrapped_view

def transaction_atomic(view_func: Callable) -> Callable:
    """
    Decorator to wrap view in database transaction.
    Usage: @transaction_atomic
    """
    from django.db import transaction
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        with transaction.atomic():
            return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def get_client_ip(request) -> str:
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def method_required(*methods: str):
    """
    Decorator to check HTTP method.
    Usage: @method_required('POST', 'PUT')
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method not in methods:
                return JsonResponse({
                    'error': f'Method {request.method} not allowed. Use: {", ".join(methods)}'
                }, status=405)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def api_key_required(view_func: Callable) -> Callable:
    """
    Decorator to check for API key in headers.
    Usage: @api_key_required
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return JsonResponse({'error': 'API key required'}, status=401)
        
        # In production, validate against database
        # For now, just check for a simple key
        valid_keys = ['demo_api_key_123', 'test_key_456']
        
        if api_key not in valid_keys:
            return JsonResponse({'error': 'Invalid API key'}, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view