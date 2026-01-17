"""
Request logging middleware for Geo-Analytics API.

Logs all incoming requests with timing, response status, and other metrics.
"""
import time
import logging
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests with detailed information.
    
    Logs:
    - Request ID
    - Method and path
    - Client IP
    - User agent
    - Request duration
    - Response status code
    - Response size
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request information
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request started: {request_id} | {method} {url} | "
            f"Client: {client_ip} | User-Agent: {user_agent}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration:.4f}"
            
            # Log response
            logger.info(
                f"Request completed: {request_id} | {method} {url} | "
                f"Status: {response.status_code} | Duration: {duration:.4f}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request_id} | {method} {url} | "
                f"Error: {str(e)} | Duration: {duration:.4f}s",
                exc_info=True
            )
            
            raise


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Simplified access log middleware for production use.
    
    Logs requests in Apache Common Log Format.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.access_logger = logging.getLogger("access")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process and log request in access log format.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response
        """
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Apache Common Log Format
        # host - user [timestamp] "method path protocol" status size
        client_ip = request.client.host if request.client else "-"
        method = request.method
        path = request.url.path
        status_code = response.status_code
        size = response.headers.get("content-length", "-")
        
        self.access_logger.info(
            f'{client_ip} - - [{time.strftime("%d/%b/%Y:%H:%M:%S %z")}] '
            f'"{method} {path} HTTP/1.1" {status_code} {size} '
            f'{duration:.4f}s'
        )
        
        return response


def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for a request.
    
    Args:
        request: HTTP request
        
    Returns:
        str: Request ID
    """
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return str(uuid.uuid4())
