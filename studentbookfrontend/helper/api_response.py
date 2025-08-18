from rest_framework.response import Response

def api_response(message="", message_type="info", data=None, status_code=200):
    """
    Standardized API response format.
    
    message_type: success | warning | error | info
    """
    return Response({
        "message": message,
        "message_type": message_type,
        "data": data
    }, status=status_code)
