"""
Performance monitoring views for EYTGaming platform
Handles performance data collection and reporting
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def performance_data(request):
    """
    Collect performance data from frontend
    This is a simple endpoint that logs performance metrics
    """
    try:
        data = json.loads(request.body)
        
        # Log performance data for monitoring
        logger.info(f"Performance data received: {data}")
        
        # In a production environment, you might want to:
        # - Store data in a database
        # - Send to monitoring service (e.g., DataDog, New Relic)
        # - Aggregate metrics for analysis
        
        return JsonResponse({
            'status': 'success',
            'message': 'Performance data received'
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in performance data request")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error processing performance data: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


class PerformanceAPIView(View):
    """
    Class-based view for performance data collection
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle POST requests for performance data"""
        return performance_data(request)
    
    def options(self, request):
        """Handle OPTIONS requests for CORS"""
        response = JsonResponse({'status': 'ok'})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response