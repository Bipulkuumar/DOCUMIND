from typing import Generic, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str = "1.0.0"
    database_connected: bool
    vector_search_ready: bool
