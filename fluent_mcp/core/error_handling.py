"""
Error handling for MCP.

This module provides error handling functionality for MCP servers.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type


class MCPError(Exception):
    """Base class for MCP errors."""
    
    def __init__(self, message: str, code: str = "unknown_error", details: Optional[Dict[str, Any]] = None):
        """
        Initialize a new MCP error.
        
        Args:
            message: Error message
            code: Error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            A dictionary representation of the error
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class ConfigError(MCPError):
    """Error raised when there is a configuration issue."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a new configuration error."""
        super().__init__(message, "config_error", details)


class ServerError(MCPError):
    """Error raised when there is a server issue."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize a new server error."""
        super().__init__(message, "server_error", details)


class ErrorHandler:
    """
    Error handler for MCP.
    
    Handles errors and exceptions in MCP servers.
    """
    
    def __init__(self, log_level: str = "INFO"):
        """
        Initialize a new error handler.
        
        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger("mcp")
        self.logger.setLevel(getattr(logging, log_level))
        self.handlers: Dict[Type[Exception], Callable] = {}
        
        # Register default handlers
        self.register(MCPError, self._handle_mcp_error)
        self.register(Exception, self._handle_generic_error)
        
    def register(self, exception_type: Type[Exception], handler: Callable) -> None:
        """
        Register an error handler.
        
        Args:
            exception_type: Type of exception to handle
            handler: Function to handle the exception
        """
        self.handlers[exception_type] = handler
        
    def handle(self, exception: Exception) -> Dict[str, Any]:
        """
        Handle an exception.
        
        Args:
            exception: The exception to handle
            
        Returns:
            A dictionary representation of the error
        """
        # Find the most specific handler
        for exc_type, handler in self.handlers.items():
            if isinstance(exception, exc_type):
                return handler(exception)
                
        # Fallback to generic handler
        return self._handle_generic_error(exception)
        
    def _handle_mcp_error(self, error: MCPError) -> Dict[str, Any]:
        """
        Handle an MCP error.
        
        Args:
            error: The MCP error
            
        Returns:
            A dictionary representation of the error
        """
        self.logger.error(f"MCP Error: {error.code} - {error.message}")
        return error.to_dict()
        
    def _handle_generic_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle a generic error.
        
        Args:
            error: The exception
            
        Returns:
            A dictionary representation of the error
        """
        self.logger.error(f"Unexpected error: {str(error)}")
        self.logger.debug(traceback.format_exc())
        
        return {
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred",
                "details": {
                    "error_type": error.__class__.__name__,
                    "error_message": str(error)
                }
            }
        }
