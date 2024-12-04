import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta
from jose import jwt
from app.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    authenticate_user,
    create_email_token
)
from app.models import User


@pytest.mark.asyncio
async def test_create_access_token(monkeypatch):
    monkeypatch.setattr("app.auth.SECRET_KEY", "test_secret_key")
    data = {"sub": "James Bond"}
    expires_delta = timedelta(minutes=15)
    token = await create_access_token(data, expires_delta=expires_delta)
    decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
    assert decoded_token["sub"] == "James Bond"

    # async def test_create_refresh_token(monkeypatch):
    monkeypatch.setattr("app.auth.SECRET_KEY", "test_secret_key")
    data = {"sub": "James Bond"}
    token = await create_refresh_token(data)
    decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
    assert decoded_token["sub"] == "James Bond"
    assert "exp" in decoded_token


@pytest.mark.asyncio
async def test_get_current_user(monkeypatch):
    monkeypatch.setattr("app.auth.SECRET_KEY", "test_secret_key")
    test_token = jwt.encode({"sub": "stilgar@dune.com"}, "test_secret_key", algorithm="HS256")

    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Redis returns no cached user

    # Mock request object
    mock_request = MagicMock()
    mock_request.app.redis = mock_redis

    # Mock database
    mock_db = AsyncMock()
    mock_user = User(
        id=1,
        email="stilgar@dune.com",
        hashed_password="mock_hash_pass",
        is_verified=True,
        is_active=True,
    )
    # Mock the CRUD function
    with patch("app.crud.get_user_by_email", AsyncMock(return_value=mock_user)):
        user = await get_current_user(request=mock_request, token=test_token, db=mock_db)

    # Checks
    assert user.email == "stilgar@dune.com"
    assert user.is_verified is True
    assert user.is_active is True


@pytest.mark.asyncio
async def test_authenticate_user_success(monkeypatch):
    mock_verify_password = AsyncMock(return_value=True)
    monkeypatch.setattr("app.auth.Hash.verify_password", mock_verify_password)

    mock_user = User(
        # id=1,
        email="ghanima@dune.com",
        hashed_password="mock_hash_pass",
        is_verified=True,
        is_active=True,
    )
    mock_db_session = AsyncMock()
    mock_query_result = AsyncMock()
    mock_query_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_query_result

    # Calling authenticate_user
    user = await authenticate_user(mock_db_session, "ghanima@dune.com", "qwerty12345")

    # Checks
    assert user is not None
    assert user.email == "ghanima@dune.com"
    assert user.is_active is True
    assert user.is_verified is True
    mock_verify_password.assert_called_once_with("qwerty12345", "mock_hash_pass")


@pytest.mark.asyncio
async def test_authenticate_user_fail(monkeypatch):
    # Mock database to return None (no user found)
    mock_db_session = AsyncMock()
    mock_query_result = AsyncMock()
    mock_query_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_query_result

    # Mock Hash.verify_password not to call it
    mock_verify_password = AsyncMock(return_value=False)
    monkeypatch.setattr("app.auth.Hash.verify_password", mock_verify_password)

    # Call authenticate_user with invalid credentials
    user = await authenticate_user(mock_db_session, "no_such_user@emptiness.com", "invalid_password")

    assert user is None
    mock_verify_password.assert_not_called()


@pytest.mark.asyncio
async def test_create_email_token(monkeypatch):
    monkeypatch.setattr("app.auth.SECRET_KEY", "test_secret_key")
    data = {"email": "test@example.com"}
    token = await create_email_token(data)
    decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
    assert decoded_token["email"] == "test@example.com"
    assert "exp" in decoded_token

# pytest --disable-warnings
