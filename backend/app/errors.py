"""
Custom error classes and error handling utilities for Clintra API.
"""
from fastapi import HTTPException, status
from typing import Dict, Any, Optional
import re

class ClintraException(Exception):
    """Base exception for Clintra-specific errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class SearchException(ClintraException):
    """Exception raised when search operations fail."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class APIConnectionException(ClintraException):
    """Exception raised when external API connections fail."""
    def __init__(self, api_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to connect to {api_name} API"
        super().__init__(message, status_code=503, details=details)

class DataValidationException(ClintraException):
    """Exception raised when data validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)

class AuthenticationException(ClintraException):
    """Exception raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)

class RateLimitException(ClintraException):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details)

def get_user_friendly_error(error: Exception) -> Dict[str, Any]:
    """
    Convert exceptions to user-friendly error messages.
    """
    if isinstance(error, ClintraException):
        return {
            "error": error.message,
            "details": error.details,
            "status_code": error.status_code,
            "user_message": _get_friendly_message(error)
        }
    elif isinstance(error, HTTPException):
        return {
            "error": error.detail,
            "status_code": error.status_code,
            "user_message": _get_friendly_message(error)
        }
    else:
        return {
            "error": "An unexpected error occurred",
            "status_code": 500,
            "user_message": "Something went wrong. Please try again or contact support."
        }

def _get_friendly_message(error: Exception) -> str:
    """
    Generate user-friendly error messages based on error type.
    """
    if isinstance(error, SearchException):
        return "We couldn't complete your search. Please try with different keywords or try again later."
    elif isinstance(error, APIConnectionException):
        return "We're having trouble connecting to external databases. Your request will use cached data."
    elif isinstance(error, DataValidationException):
        return "The information you provided seems incorrect. Please check and try again."
    elif isinstance(error, AuthenticationException):
        return "Please log in again to continue using Clintra."
    elif isinstance(error, RateLimitException):
        return "You're sending too many requests. Please wait a moment before trying again."
    else:
        return "Something unexpected happened. Our team has been notified and we're working on it."

def validate_query(query: str, max_length: int = 500) -> None:
    """
    Validate user query input.
    """
    if not query or not query.strip():
        raise DataValidationException("Query cannot be empty")
    
    if len(query) > max_length:
        raise DataValidationException(
            f"Query too long. Maximum {max_length} characters allowed.",
            details={"query_length": len(query), "max_length": max_length}
        )
    
    # Check for potentially malicious input
    suspicious_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
    query_lower = query.lower()
    for pattern in suspicious_patterns:
        if pattern in query_lower:
            raise DataValidationException(
                "Query contains suspicious content",
                details={"pattern_detected": pattern}
            )

def validate_compound_name(compound_name: str) -> None:
    """
    Validate compound name input.
    """
    if not compound_name or not compound_name.strip():
        raise DataValidationException("Compound name cannot be empty")
    
    if len(compound_name) > 200:
        raise DataValidationException("Compound name too long. Maximum 200 characters allowed.")
    
    # Allow only alphanumeric, spaces, hyphens, and parentheses
    if not re.match(r'^[a-zA-Z0-9\s\-()]+$', compound_name):
        raise DataValidationException(
            "Compound name contains invalid characters. Use only letters, numbers, spaces, hyphens, and parentheses."
        )

def validate_pdb_id(pdb_id: str) -> None:
    """
    Validate PDB ID format.
    """
    if not pdb_id or not pdb_id.strip():
        raise DataValidationException("PDB ID cannot be empty")
    
    # PDB IDs are exactly 4 characters (alphanumeric)
    if len(pdb_id) != 4:
        raise DataValidationException(
            "PDB ID must be exactly 4 characters",
            details={"provided_length": len(pdb_id)}
        )
    
    if not re.match(r'^[a-zA-Z0-9]{4}$', pdb_id):
        raise DataValidationException("PDB ID must contain only letters and numbers")

