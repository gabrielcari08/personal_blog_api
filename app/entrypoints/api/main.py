"""Punto de entrada HTTP (app FastAPI, rutas y mapeo de errores)."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    ForbiddenException,
    InvalidCredentialsException,
    UserNotFoundException,
    UserValidationException,
)
from app.entrypoints.api.v1.routes.user_router import router as user_router

app = FastAPI(title='Personal Blog API', description='API for the Personal Blog')

app.include_router(user_router, prefix='/api/v1')


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    """Mapea errores de formato del cuerpo a 400 (la spec no usa 422)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': 'Invalid input.', 'code': 'validation_error'},
    )


@app.exception_handler(UserValidationException)
def user_validation_error_handler(request: Request, error: UserValidationException) -> JSONResponse:
    """Mapea violaciones de reglas de negocio a 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': str(error), 'code': 'validation_error'},
    )


@app.exception_handler(DuplicateUsernameException)
def duplicate_username_handler(request: Request, error: DuplicateUsernameException) -> JSONResponse:
    """Mapea username duplicado a 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': str(error), 'code': 'duplicate_username'},
    )


@app.exception_handler(DuplicateEmailException)
def duplicate_email_handler(request: Request, error: DuplicateEmailException) -> JSONResponse:
    """Mapea correo duplicado a 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': str(error), 'code': 'duplicate_email'},
    )


@app.exception_handler(InvalidCredentialsException)
def invalid_credentials_handler(request: Request, error: InvalidCredentialsException) -> JSONResponse:
    """Mapea cualquier fallo de login al mismo 401 generico."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={'detail': str(error), 'code': 'invalid_credentials'},
    )


@app.exception_handler(ForbiddenException)
def forbidden_handler(request: Request, error: ForbiddenException) -> JSONResponse:
    """Mapea falta de rol ADMIN a 403."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'detail': str(error), 'code': 'forbidden'},
    )


@app.exception_handler(UserNotFoundException)
def user_not_found_handler(request: Request, error: UserNotFoundException) -> JSONResponse:
    """Mapea objetivo inexistente a 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'detail': str(error), 'code': 'user_not_found'},
    )


@app.get('/')
def root():
    return {'message': 'Personal Blog is running'}