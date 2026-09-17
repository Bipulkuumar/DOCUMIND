from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class DocumentNotFoundException(NotFoundException):
    def __init__(self, document_id: str):
        super().__init__(message=f"Document with ID '{document_id}' not found.")
        self.code = "DOCUMENT_NOT_FOUND"


class ConversationNotFoundException(NotFoundException):
    def __init__(self, conversation_id: str):
        super().__init__(message=f"Conversation with ID '{conversation_id}' not found.")
        self.code = "CONVERSATION_NOT_FOUND"


class InvalidFileException(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_FILE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class IngestionException(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="INGESTION_FAILED",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RAGException(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="RAG_PROCESSING_FAILED",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    content = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if exc.details:
        content["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Avoid exposing raw tracebacks in response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        }
    )
