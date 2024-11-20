import unittest
from datetime import timedelta, datetime
from jose import jwt
from unittest.mock import patch, AsyncMock, MagicMock
from app.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    authenticate_user,
    create_email_token
)


class TestAUTH(unittest.IsolatedAsyncioTestCase):
    @patch("app.auth.SECRET_KEY", "test_secret_key")  # mocking SECRET_KEY
    @patch("app.auth.ALGORITHM", "HS256")  # mocking ALGORITHM
    async def test_create_access_token(self):
        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=15)

        token = await create_access_token(data, expires_delta=expires_delta)
        decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])

        # Checks
        self.assertEqual(decoded_token["sub"], "test_user")
        self.assertIn("exp", decoded_token)

        # if expiration time is correct:
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(decoded_token["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5))

    @patch("app.auth.SECRET_KEY", "test_secret_key")
    @patch("app.auth.ALGORITHM", "HS256")
    @patch("app.auth.REFRESH_TOKEN_EXPIRE_DAYS", 7)
    async def test_create_refresh_token(self):
        data = {"sub": "test_user"}

        token = await create_refresh_token(data)
        decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])

        # Checks
        self.assertEqual(decoded_token["sub"], "test_user")
        self.assertIn("exp", decoded_token)

        # if expiration time is correct
        expected_exp = datetime.utcnow() + timedelta(days=7)
        actual_exp = datetime.utcfromtimestamp(decoded_token["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5))

    @patch("app.auth.SECRET_KEY", "test_secret_key")
    @patch("app.auth.ALGORITHM", "HS256")
    async def test_get_current_user(self):
        test_token = jwt.encode({"sub": "test_user@example.com"}, "test_secret_key", algorithm="HS256")
        mock_request = MagicMock()
        mock_request.app.redis = AsyncMock()
        mock_request.app.redis.get.return_value = None  # Redis returns no cached user

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test_user@example.com"
        mock_user.is_verified = True
        mock_user.is_active = True

        # Mock the CRUD function
        with patch("app.crud.get_user_by_email", AsyncMock(return_value=mock_user)):
            user = await get_current_user(request=mock_request, token=test_token, db=mock_db)

        # Checks
        self.assertEqual(user.email, "test_user@example.com")
        self.assertTrue(user.is_verified)
        self.assertTrue(user.is_active)

    async def test_authenticate_user_success(self):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test_user@example.com"
        mock_user.password = "qwerty12345"
        mock_user.hashed_password = "mocked_hashed_password"

        # Configuring the output of SQL-query
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        mock_db.execute.return_value = mock_result

        # Mock the Hash.verify_password function
        with patch("app.auth.Hash.verify_password", AsyncMock(return_value=True)):
            user = await authenticate_user(mock_db, mock_user.email, mock_user.password)

        # Checks
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test_user@example.com")


if __name__ == "__main__":
    unittest.main()

# python3 -m unittest tests.test_auth
