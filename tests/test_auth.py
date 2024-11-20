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
        data = {"sub": "James_Bond"}
        expires_delta = timedelta(minutes=15)

        token = await create_access_token(data, expires_delta=expires_delta)
        decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])

        # Checks
        self.assertEqual(decoded_token["sub"], "James_Bond")
        self.assertIn("exp", decoded_token)

        # if expiration time is correct:
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(decoded_token["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5))

    @patch("app.auth.SECRET_KEY", "test_secret_key")
    @patch("app.auth.ALGORITHM", "HS256")
    @patch("app.auth.REFRESH_TOKEN_EXPIRE_DAYS", 7)
    async def test_create_refresh_token(self):
        data = {"sub": "James_Bond"}

        token = await create_refresh_token(data)
        decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])

        # Checks
        self.assertEqual(decoded_token["sub"], "James_Bond")
        self.assertIn("exp", decoded_token)

        # if expiration time is correct
        expected_exp = datetime.utcnow() + timedelta(days=7)
        actual_exp = datetime.utcfromtimestamp(decoded_token["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5))

    @patch("app.auth.SECRET_KEY", "test_secret_key")
    @patch("app.auth.ALGORITHM", "HS256")
    async def test_get_current_user(self):
        test_token = jwt.encode({"sub": "paul@arrakis.com"}, "test_secret_key", algorithm="HS256")
        mock_request = MagicMock()
        mock_request.app.redis = AsyncMock()
        mock_request.app.redis.get.return_value = None  # Redis returns no cached user

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "paul@arrakis.com"
        mock_user.is_verified = True
        mock_user.is_active = True

        # Mock the CRUD function
        with patch("app.crud.get_user_by_email", AsyncMock(return_value=mock_user)):
            user = await get_current_user(request=mock_request, token=test_token, db=mock_db)

        # Checks
        self.assertEqual(user.email, "paul@arrakis.com")
        self.assertTrue(user.is_verified)
        self.assertTrue(user.is_active)

    async def test_authenticate_user_success(self):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "gandalf@middleearth.com"
        mock_user.password = "You_Shall_Not_Pass!"
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
        self.assertEqual(user.email, "gandalf@middleearth.com")

    async def test_authenticate_user_fail(self):
        mock_db = AsyncMock()

        # Configure the result of SQL-query to return None (user not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_db.execute.return_value = mock_result

        # Mock the Hash.verify_password function (not called here)
        with patch("app.auth.Hash.verify_password", AsyncMock(return_value=False)) as mock_verify_password:
            user = await authenticate_user(mock_db, "no_such_user@void.com", "invalid_password")

        # Checks
        self.assertIsNone(user)
        mock_verify_password.assert_not_called()

    @patch("app.auth.SECRET_KEY", "test_secret_key")
    @patch("app.auth.ALGORITHM", "HS256")
    async def test_create_email_token(self):
        test_data = {"email": "sauron@mordor.com"}
        token = await create_email_token(test_data)
        decoded_token = jwt.decode(token, "test_secret_key", algorithms=["HS256"])

        # Checks
        self.assertEqual(decoded_token["email"], "sauron@mordor.com")
        self.assertIn("exp", decoded_token)

        expected_exp = datetime.utcnow() + timedelta(hours=1)
        actual_exp = datetime.utcfromtimestamp(decoded_token["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5))


if __name__ == "__main__":
    unittest.main()

# python3 -m unittest tests.test_auth
