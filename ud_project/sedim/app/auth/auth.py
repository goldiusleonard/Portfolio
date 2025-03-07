"""Authentication module for the application."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from utils.logger import Logger

load_dotenv()


log = Logger("Knowledge_Hub")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES_STRING = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ACCESS_TOKEN_EXPIRE_DELTA = 1

# Define constants at the top of your file
UNAUTHORIZED_STATUS_CODE = 401
BAD_REQUEST_STATUS_CODE = 400
SUCCESS_CODE = 200

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if a plain password matches a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a given password using the configured password context."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JSON Web Token (JWT) with the provided data and expiration delta."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_DELTA,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    log.info("Encoded String: %s", encoded_jwt)
    return encoded_jwt


def decode_access_token(token: str) -> str | None:
    """Decode an access token for information extraction.

    This function attempts to decode the provided token.
    If successful, it extracts the username from the payload.
    If the token is invalid or does not contain a username.

    Args:
        token (str): The access token to decode.

    Returns:
        str | None: The username extracted from the token if successful, otherwise None.

    """
    try:
        log.info("Before Decoding the TOKEN: %s", token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except jwt.exceptions.InvalidTokenError:
        log.exception("Invalid token error occurred while decoding the token")
        return None
    except Exception:
        log.exception("An error occurred while decoding the token")
        return None
    else:
        return username


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Extract the username from a given token.

    Decodes the provided token to extract the username.
    If the token is invalid or does not contain a username, raises an exception.

    Args:
        token (str): The token to decode and extract the username from.

    Returns:
        str: The username extracted from the token.

    Raises:
        HTTPException: If the token is invalid or does not contain a username.

    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.exceptions.InvalidTokenError as e:
        raise credentials_exception from e
    return username


def validate_token(token: str) -> dict:
    """Validate a JWT token and check its expiration and validity.

    Decode the provided JWT token to verify its authenticity and
    check for expiration. If valid, return the token payload
    with additional validation information.

    Parameters
    ----------
    token : str
        The JWT token to be validated.

    Returns
    -------
    dict
        The token payload with 'valid' and 'status_code' fields
        if the token is valid.

    Raises
    ------
    HTTPException
        If the token is expired, invalid, or if any
        other unexpected error occurs during decoding.

    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        log.info("Token validated successfully.")
        payload["valid"] = True
        payload["status_code"] = 200

    except jwt.ExpiredSignatureError as e:
        log.exception("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired") from e
    except jwt.InvalidTokenError:
        log.exception("Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token") from None
    except Exception as e:
        log.exception("An unexpected error occurred")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred",
        ) from e
    else:
        return payload


def token_validation_start(token: str) -> dict | None:
    """Start the validation process for the provided JWT token.

    Log the authorization header and initiate token validation.
    If the token is valid, proceed without returning a value.
    Any errors encountered during validation are logged.

    Parameters
    ----------
    token : str
        The JWT token to be validated, used for authenticating the request.

    Returns
    -------
    Optional[dict]
        Dictionary containing status code and message, or None if validation succeeds.

    """
    try:
        log.info("Authorization header: %s", token.headers.get("Authorization"))

        if token.headers.get("Authorization") is None:
            return {"status_code": 400, "msg": "Bad Request"}

        auth = token.headers.get("Authorization")
        if auth:
            token_str = auth.split(" ")[1]
            log.info("Extracted token: %s", token_str)
            return validate_token(token_str)
        log.warning("No Authorization header found.")

    except AttributeError:
        log.exception("An unexpected error occurred")
        return {"status_code": 400, "msg": "Bad Request"}
    except Exception:
        log.exception("An unexpected error occurred")
        return {"status_code": 401, "msg": "Unauthorized"}
    else:
        return None


def get_code_after_validation(request: dict) -> dict | HTTPException:
    """Process the validation result of the JWT token.

    Parameters
    ----------
    request : dict
        The request containing the JWT token to be validated.

    Returns
    -------
    dict | HTTPException
        Returns the validation result as a dictionary.

    """
    validation = token_validation_start(request)

    if validation and validation.get("status_code") == SUCCESS_CODE:
        return validation
    if validation and validation.get("status_code") == BAD_REQUEST_STATUS_CODE:
        raise HTTPException(
            status_code=validation.get("status_code"),
            detail="Bad Request",
        )
    if validation and validation.get("status_code") == UNAUTHORIZED_STATUS_CODE:
        raise HTTPException(
            status_code=validation.get("status_code"),
            detail="Token has expired or Invalid",
        )
    raise HTTPException(status_code=500, detail="Internal Error")
