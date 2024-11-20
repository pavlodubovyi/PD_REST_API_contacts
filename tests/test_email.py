import unittest
from unittest.mock import AsyncMock, patch
from app.email import send_verification_email, send_password_reset_email
from fastapi_mail import MessageSchema


class TestEmail(unittest.IsolatedAsyncioTestCase):
    @patch("app.email.create_email_token", new_callable=AsyncMock)  # Mock the token
    @patch("app.email.FastMail")
    @patch("app.email.FRONTEND_URL", "http://localhost:3000")
    async def test_send_verification_email(self, MockFastMail, mock_create_email_token):

        mock_create_email_token.return_value = "test_token"

        email = "frodo@shire.com"
        username = "frodo_baggins"

        # Mock FastMail
        mock_fast_mail = AsyncMock()
        MockFastMail.return_value = mock_fast_mail

        # Call the function
        await send_verification_email(email, username)

        # Check if create_email_token was called
        mock_create_email_token.assert_called_once_with({"sub": email})

        # Check FastMail calls
        mock_fast_mail.send_message.assert_called_once()

        # Check the sent message
        sent_message = mock_fast_mail.send_message.call_args[0][0]
        self.assertIsInstance(sent_message, MessageSchema)
        self.assertEqual(sent_message.subject, "Confirm your email")
        self.assertIn("http://localhost:3000", sent_message.template_body["host"])
        self.assertEqual(sent_message.template_body["username"], username)
        self.assertEqual(sent_message.template_body["token"], "test_token")

    @patch("app.email.FastMail")
    async def test_send_password_reset_email(self, MockFastMail):
        # Mock email data
        email = "bilbo@shire.com"
        host = "http://localhost:3000"
        token = "reset_token"

        # Mock FastMail instance
        mock_fm_instance = AsyncMock()
        MockFastMail.return_value = mock_fm_instance

        # Call the function
        await send_password_reset_email(email, host, token)

        # Verify FastMail.send_message was called
        mock_fm_instance.send_message.assert_called_once()
        sent_message = mock_fm_instance.send_message.call_args[0][0]
        self.assertIsInstance(sent_message, MessageSchema)
        self.assertEqual(sent_message.subject, "Reset your password")
        self.assertIn("http://localhost:3000", sent_message.template_body["host"])
        self.assertEqual(sent_message.template_body["token"], token)
        self.assertEqual(sent_message.template_body["username"], "bilbo")


if __name__ == "__main__":
    unittest.main()

# python3 -m unittest tests.test_email
