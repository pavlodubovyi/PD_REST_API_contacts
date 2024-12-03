import os
import unittest
import app.auth
from fastapi import HTTPException, status, Request, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from unittest.mock import patch, AsyncMock, MagicMock
from starlette.responses import HTMLResponse
from app.main import (
    startup,
    register,
    login,
    refresh_token,
    request_password_reset,
    display_reset_password_form,
    confirm_password_reset,
    create_contact,
    read_contact,
    read_contacts,
    update_contact,
    delete_contact,
    search_contacts,
    get_upcoming_birthdays,
    confirm_email,
    update_avatar
)
from app.schemas import UserInDB, UserCreate, Token, ContactCreate, ContactInDB, ContactUpdate
from app.models import User, Contact
from jose import JWTError


class TestMain(unittest.IsolatedAsyncioTestCase):
    @patch("app.main.redis.Redis", new_callable=AsyncMock)
    @patch("app.main.FastAPILimiter.init", new_callable=AsyncMock)
    @patch("app.main.config")
    async def test_startup(self, mock_config, mock_fastapi_limiter_init, mock_redis):
        # config Mock
        mock_config.REDIS_HOST = "localhost"
        mock_config.REDIS_PORT = 6379

        # Redis client Mock
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        await startup()

        # Checks
        mock_redis.assert_called_once_with(host="localhost", port=6379, db=0, encoding="utf-8", decode_responses=True)
        mock_fastapi_limiter_init.assert_called_once_with(mock_redis_instance)

    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.crud.create_user", new_callable=AsyncMock)
    @patch("app.main.send_verification_email", new_callable=AsyncMock)
    @patch("app.main.hash_handler.get_password_hash", new_callable=AsyncMock)
    async def test_register_user_success(
            self, mock_get_password_hash, mock_send_verification_email, mock_create_user, mock_get_user_by_email
    ):
        test_user = UserCreate(email="legolas@forest.com", password="elf")
        hashed_password = "hashed_elf"
        created_user = UserInDB(id=1, email=test_user.email, is_active=True, is_verified=False)

        mock_get_user_by_email.return_value = None  # User does not exist
        mock_get_password_hash.return_value = hashed_password
        mock_create_user.return_value = created_user

        db_mock = AsyncMock()
        result = await register(test_user, db=db_mock)

        # Checks
        self.assertEqual(result, created_user)  # if expected user was created and registered
        mock_get_user_by_email.assert_called_once_with(db_mock, test_user.email)  # if get_user_by_email was called
        mock_get_password_hash.assert_called_once_with(test_user.password)  # if password was hashed
        mock_create_user.assert_called_once_with(db_mock, test_user.email, hashed_password)  # if user was created
        mock_send_verification_email.assert_called_once_with(
            email=test_user.email,
            username="legolas",
            host=os.getenv("FRONTEND_URL"),
        )

    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    async def test_register_user_email_already_registered(self, mock_get_user_by_email):
        test_user = UserCreate(email="frodo@shire.com", password="RingBearer")

        mock_get_user_by_email.return_value = UserInDB(id=1, email=test_user.email, is_active=True, is_verified=True)

        db_mock = AsyncMock()
        try:
            await register(test_user, db=db_mock)
            self.fail("HTTPException not raised")
        except HTTPException as e:
            self.assertEqual(e.status_code, status.HTTP_409_CONFLICT)
            self.assertEqual(e.detail, "Email already registered")

        mock_get_user_by_email.assert_called_once_with(db_mock, test_user.email)

    @patch("app.main.authenticate_user", new_callable=AsyncMock)
    @patch("app.main.create_access_token", new_callable=AsyncMock)
    @patch("app.main.create_refresh_token", new_callable=AsyncMock)
    async def test_login_success(self, mock_create_refresh_token, mock_create_access_token, mock_authenticate_user):
        test_user = UserInDB(id=1, email="bilbo@shire.com", is_active=True, is_verified=True)
        access_token = "access_token"
        refresh_token = "refresh_token"

        # Mocks
        mock_authenticate_user.return_value = test_user
        mock_create_access_token.return_value = access_token
        mock_create_refresh_token.return_value = refresh_token

        # Calling the function
        user_data = OAuth2PasswordRequestForm(username=test_user.email, password="treasure_thief")
        db_mock = AsyncMock()
        result = await login(user_data, db=db_mock)

        # Checks
        self.assertEqual(result, Token(access_token=access_token, refresh_token=refresh_token))
        mock_authenticate_user.assert_called_once_with(db_mock, test_user.email, "treasure_thief")
        mock_create_access_token.assert_called_once_with(data={"sub": test_user.email})
        mock_create_refresh_token.assert_called_once_with(data={"sub": test_user.email})

    @patch("app.main.authenticate_user", new_callable=AsyncMock)
    async def test_login_failure(self, mock_authenticate_user):
        test_user = {"username": "sauron@mordor.com", "password": "darkness"}

        mock_authenticate_user.return_value = None  # Authentication failed

        unknown_user_data = OAuth2PasswordRequestForm(username=test_user["username"], password=test_user["password"])
        db_mock = AsyncMock()
        try:
            await login(unknown_user_data, db=db_mock)
            self.fail("HTTPException not raised")
        except HTTPException as e:
            self.assertEqual(e.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(e.detail, "Invalid credentials")

        mock_authenticate_user.assert_called_once_with(db_mock, test_user["username"], test_user["password"])

    # Refresh_token test for successfully refreshed token
    @patch("app.main.jwt.decode", return_value={"sub": "gimli@dwarfs.com"})
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    @patch("app.main.create_access_token", new_callable=AsyncMock)
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    async def test_refresh_token_success(self, mock_get_user_by_email, mock_create_access_token, mock_jwt_decode):
        test_user = UserInDB(id=1, email="gimli@dwarfs.com", is_active=True, is_verified=True)
        mock_refresh_token = "mock_refresh_token"
        new_access_token = "new_access_token"

        mock_get_user_by_email.return_value = test_user
        mock_create_access_token.return_value = new_access_token

        db_mock = AsyncMock()
        result = await refresh_token(refresh_token=mock_refresh_token, db=db_mock)

        # Checks
        self.assertEqual(result, {"access_token": new_access_token, "token_type": "bearer"})
        mock_get_user_by_email.assert_called_once_with(db_mock, test_user.email)
        mock_create_access_token.assert_called_once_with(data={"sub": test_user.email})
        app.main.jwt.decode.assert_called_once_with(mock_refresh_token, "mock_secret", algorithms=["mock_algorithm"])

    # Refresh_token test for no user in the database
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    @patch("app.main.jwt.decode", return_value={"sub": "elrond@rivendell.com"})
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    async def test_refresh_token_user_not_found(self, mock_get_user_by_email, mock_jwt_decode):
        mock_refresh_token = "mock_refresh_token"

        mock_get_user_by_email.return_value = None  # no such user in our database
        db_mock = AsyncMock()
        try:
            await refresh_token(refresh_token=mock_refresh_token, db=db_mock)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(exc.detail, "User not found or not active")

        # Checks
        mock_get_user_by_email.assert_called_once_with(db_mock, "elrond@rivendell.com")
        mock_jwt_decode.assert_called_once_with(
            mock_refresh_token, "mock_secret", algorithms=["mock_algorithm"]
        )

    # Request_password_reset test in case of success
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.create_email_token", new_callable=AsyncMock)
    @patch("app.main.send_password_reset_email", new_callable=AsyncMock)
    async def test_request_password_reset_success(self, mock_send_password_reset_email, mock_create_email_token,
                                                  mock_get_user_by_email):
        test_user = UserInDB(id=1, email="paul@arrakis.com", is_active=True, is_verified=True)
        mock_email_token = "mock_email_token"

        mock_get_user_by_email.return_value = test_user
        mock_create_email_token.return_value = mock_email_token

        db_mock = AsyncMock()
        result = await request_password_reset(email=test_user.email, db=db_mock)

        # Checks
        self.assertEqual(result, {"message": "Password reset link sent."})
        mock_get_user_by_email.assert_called_once_with(db_mock, test_user.email)
        mock_create_email_token.assert_called_once_with({"sub": test_user.email})
        mock_send_password_reset_email.assert_called_once_with(
            email=test_user.email,
            token=mock_email_token,
            host=os.getenv("FRONTEND_URL"),
        )

    # Request_password_reset test in case user not found
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    async def test_request_password_reset_user_not_found(self, mock_get_user_by_email):
        test_email = "sauron@shire.com"

        mock_get_user_by_email.return_value = None  # No such user
        db_mock = AsyncMock()
        try:
            await request_password_reset(email=test_email, db=db_mock)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(exc.detail, "User not found")

        # Checks
        mock_get_user_by_email.assert_called_once_with(db_mock, test_email)

    @patch("app.main.templates", new_callable=MagicMock)
    async def test_display_reset_password_form(self, mock_templates):
        test_token = "mock_reset_token"
        mock_request = MagicMock(spec=Request)  # Mocking HTTP request
        mock_templates.TemplateResponse.return_value = HTMLResponse("Mocked HTML Response")

        result = await display_reset_password_form(request=mock_request, token=test_token)

        # Checks
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body.decode(), "Mocked HTML Response")
        mock_templates.TemplateResponse.assert_called_once_with(
            "reset_pass_form.html", {"request": mock_request, "token": test_token}
        )

    # Test for confirm_password_reset in case of success
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.hash_handler.get_password_hash", new_callable=AsyncMock)
    @patch("app.main.jwt.decode", return_value={"sub": "chani@dune.com"})
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_password_reset_success(self, mock_jwt_decode, mock_get_password_hash, mock_get_user_by_email):
        test_token = "mock_token"
        test_email = "chani@dune.com"
        new_password = "Mother_of_Leto"
        hashed_password = "new_hashed_password"

        test_user = User(
            id=1,
            email=test_email,
            hashed_password="old_hashed_password",
            is_active=True,
            is_verified=True,
            avatar=None
        )

        mock_get_user_by_email.return_value = test_user
        mock_get_password_hash.return_value = hashed_password

        db_mock = AsyncMock()
        db_mock.add = AsyncMock()
        db_mock.commit = AsyncMock()

        result = await confirm_password_reset(
            token=test_token, new_password=new_password, db=db_mock
        )

        # Checks
        self.assertEqual(result, {"message": "Password has been reset."})
        mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])
        mock_get_user_by_email.assert_called_once_with(db_mock, test_email)
        mock_get_password_hash.assert_called_once_with(new_password)
        db_mock.add.assert_awaited_once_with(test_user)
        db_mock.commit.assert_awaited_once()
        self.assertEqual(test_user.hashed_password, hashed_password)

    # Test for confirm_password_reset in case of invalid token
    @patch("app.main.jwt.decode", side_effect=JWTError)
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_password_reset_invalid_token(self, mock_jwt_decode):
        test_token = "invalid_token"
        new_password = "new_secure_password"

        db_mock = AsyncMock()

        try:
            await confirm_password_reset(token=test_token, new_password=new_password, db=db_mock)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(exc.detail, "Invalid token")
            mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])
            return

        self.fail("HTTPException not raised")

    # Test for confirm_password_reset in case of user not found
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.jwt.decode", return_value={"sub": "saruman@shire.com"})
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_password_reset_user_not_found(self, mock_jwt_decode, mock_get_user_by_email):
        test_token = "mock_token"
        test_email = "saruman@shire.com"
        new_password = "new_secure_password"

        mock_get_user_by_email.return_value = None  # User not found

        db_mock = AsyncMock()

        try:
            await confirm_password_reset(token=test_token, new_password=new_password, db=db_mock)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(exc.detail, "User not found")
            mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])
            mock_get_user_by_email.assert_called_once_with(db_mock, test_email)
            return

        self.fail("HTTPException was not raised")

    @patch("app.main.crud.create_contact", new_callable=AsyncMock)
    async def test_create_contact(self, mock_create_contact):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_contact_data = ContactCreate(
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@dune.com",
            phone="123456789",
            birthday="1980-03-25",
            additional_info="Mother of Kwisatz Haderach",
        )

        test_contact_result = ContactInDB(
            id=1,
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@dune.com",
            phone="123456789",
            birthday="1980-03-25",
            additional_info="Mother of Kwisatz Haderach",
            owner_id=test_user.id,
        )

        mock_create_contact.return_value = test_contact_result

        db_mock = AsyncMock()
        result = await create_contact(contact=test_contact_data, db=db_mock, current_user=test_user)

        # Checks
        self.assertEqual(result, test_contact_result)  # if expected result is returned
        mock_create_contact.assert_called_once_with(
            db=db_mock, contact=test_contact_data, owner_id=test_user.id
        )

    @patch("app.main.crud.get_contacts", new_callable=AsyncMock)
    async def test_read_contacts(self, mock_get_contacts):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_contacts = [
            ContactInDB(
                id=1,
                first_name="Jessica",
                last_name="Atreides",
                email="jessica@dune.com",
                phone="123456789",
                birthday="1980-03-25",
                additional_info="Mother of Kwisatz Haderach",
                owner_id=test_user.id,
            ),
            ContactInDB(
                id=2,
                first_name="Leto",
                last_name="Atreides",
                email="leto@dune.com",
                phone="987654321",
                birthday="2000-01-01",
                additional_info="Duke of Arrakis",
                owner_id=test_user.id,
            ),
        ]

        mock_get_contacts.return_value = test_contacts

        db_mock = AsyncMock()
        result = await read_contacts(db=db_mock, current_user=test_user)

        # Checks
        self.assertEqual(result, test_contacts)
        mock_get_contacts.assert_called_once_with(
            db=db_mock, owner_id=test_user.id
        )

    # Test for read_contact in case of success
    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    async def test_read_contact_success(self, mock_get_contact):
        test_user = User(
            id=1,
            email="chani@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )
        # Test contact with SQLAlchemy model (Contact)
        test_contact = Contact(
            id=1,
            first_name="Alia",
            last_name="Atreides",
            email="alia@dune.com",
            phone_number="987654321",
            birthday="1990-03-19",
            additional_info="Sister of Kwisatz Haderach",
            owner_id=test_user.id,
        )

        mock_get_contact.return_value = test_contact

        db_mock = AsyncMock()
        result = await read_contact(contact_id=1, db=db_mock, current_user=test_user)

        # Checks
        self.assertEqual(result, test_contact)
        mock_get_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)

    # Test for read_contact in case of contact not found
    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    async def test_read_contact_not_found(self, mock_get_contact):
        test_user = User(
            id=1,
            email="stilgar@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        mock_get_contact.return_value = None  # Contact not found

        db_mock = AsyncMock()
        with self.assertRaises(HTTPException) as exc:
            await read_contact(contact_id=1, db=db_mock, current_user=test_user)

        self.assertEqual(exc.exception.status_code, 404)
        self.assertEqual(exc.exception.detail, "Contact not found or access denied")
        mock_get_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)

    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    @patch("app.main.crud.update_contact", new_callable=AsyncMock)
    async def test_update_contact_success(self, mock_update_contact, mock_get_contact):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        existing_contact = Contact(
            id=1,
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@dune.com",
            phone_number="123456789",
            birthday="1980-03-25",
            additional_info="Mother of Kwisatz Haderach",
            owner_id=test_user.id,
        )

        updated_contact_data = ContactUpdate(
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@caladan.com",
            phone="987654321",
            birthday="1980-03-25",
            additional_info="Duchess of Caladan",
        )

        updated_contact = ContactInDB(
            id=1,
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@caladan.com",
            phone="987654321",
            birthday="1980-03-25",
            additional_info="Duchess of Caladan",
            owner_id=test_user.id,
        )

        mock_get_contact.return_value = existing_contact
        mock_update_contact.return_value = updated_contact

        db_mock = AsyncMock()
        result = await update_contact(
            contact_id=1,
            contact=updated_contact_data,
            db=db_mock,
            current_user=test_user,
        )

        # Checks
        self.assertEqual(result, updated_contact)
        mock_get_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)
        mock_update_contact.assert_called_once_with(
            db=db_mock, contact_id=1, contact=updated_contact_data, owner_id=test_user.id
        )

    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    async def test_update_contact_not_found(self, mock_get_contact):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        mock_get_contact.return_value = None

        db_mock = AsyncMock()
        try:
            await update_contact(
                contact_id=1,
                contact=ContactUpdate(
                    first_name="Jessica",
                    last_name="Atreides",
                    email="jessica@caladan.com",
                    phone="987654321",
                    birthday="1980-03-25",
                    additional_info="Duchess of Caladan",
                ),
                db=db_mock,
                current_user=test_user,
            )
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            self.assertEqual(exc.detail, "Contact not found or access denied")
        else:
            self.fail("HTTPException not raised")

        mock_get_contact.assert_called_once_with(
            db=db_mock, contact_id=1, owner_id=test_user.id
        )

    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    @patch("app.main.crud.delete_contact", new_callable=AsyncMock)
    async def test_delete_contact_success(self, mock_delete_contact, mock_get_contact):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_contact = Contact(
            id=1,
            first_name="Jessica",
            last_name="Atreides",
            email="jessica@dune.com",
            phone_number="123456789",
            birthday="1980-03-25",
            additional_info="Mother of Kwisatz Haderach",
            owner_id=test_user.id,
        )

        mock_get_contact.return_value = test_contact
        mock_delete_contact.return_value = ContactInDB(
            id=test_contact.id,
            first_name=test_contact.first_name,
            last_name=test_contact.last_name,
            email=test_contact.email,
            phone_number=test_contact.phone_number,
            birthday=test_contact.birthday,
            additional_info=test_contact.additional_info,
            owner_id=test_contact.owner_id,
        )

        db_mock = AsyncMock()
        result = await delete_contact(contact_id=1, db=db_mock, current_user=test_user)

        # Checks
        self.assertEqual(result.id, test_contact.id)
        self.assertEqual(result.email, test_contact.email)
        mock_get_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)
        mock_delete_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)

    @patch("app.main.crud.get_contact", new_callable=AsyncMock)
    async def test_delete_contact_not_found(self, mock_get_contact):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        mock_get_contact.return_value = None

        db_mock = AsyncMock()
        try:
            await delete_contact(contact_id=1, db=db_mock, current_user=test_user)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            self.assertEqual(exc.detail, "Contact not found or access denied")
        else:
            self.fail("HTTPException not raised")

        mock_get_contact.assert_called_once_with(db=db_mock, contact_id=1, owner_id=test_user.id)

    @patch("app.main.crud.search_contacts", new_callable=AsyncMock)
    async def test_search_contacts(self, mock_search_contacts):
        test_user = User(
            id=1,
            email="leto@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_query = "Jess"
        test_contacts = [
            ContactInDB(
                id=1,
                first_name="Jessica",
                last_name="Atreides",
                email="jessica@dune.com",
                phone_number="123456789",
                birthday="1980-03-25",
                additional_info="Mother of Kwisatz Haderach",
                owner_id=test_user.id,
            ),
            ContactInDB(
                id=2,
                first_name="Alia",
                last_name="Atreides",
                email="alia@dune.com",
                phone_number="987654321",
                birthday="1990-03-19",
                additional_info="Sister of Kwisatz Haderach",
                owner_id=test_user.id,
            ),
        ]

        mock_search_contacts.return_value = test_contacts

        db_mock = AsyncMock()
        result = await search_contacts(query=test_query, db=db_mock, current_user=test_user)

        self.assertEqual(result, test_contacts)
        mock_search_contacts.assert_called_once_with(db=db_mock, query=test_query, owner_id=test_user.id)

    @patch("app.main.crud.get_upcoming_birthdays", new_callable=AsyncMock)
    async def test_get_upcoming_birthdays(self, mock_get_upcoming_birthdays):
        test_user = User(
            id=1,
            email="paul@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_contacts = [
            ContactInDB(
                id=1,
                first_name="Jessica",
                last_name="Atreides",
                email="jessica@dune.com",
                phone_number="123456789",
                birthday="1980-03-25",
                additional_info="Mother of Kwisatz Haderach",
                owner_id=test_user.id,
            ),
            ContactInDB(
                id=2,
                first_name="Alia",
                last_name="Atreides",
                email="alia@dune.com",
                phone_number="987654321",
                birthday="1990-03-19",
                additional_info="Sister of Kwisatz Haderach",
                owner_id=test_user.id,
            ),
        ]

        mock_get_upcoming_birthdays.return_value = test_contacts

        db_mock = AsyncMock()
        result = await get_upcoming_birthdays(db=db_mock, current_user=test_user)

        self.assertEqual(result, test_contacts)
        mock_get_upcoming_birthdays.assert_called_once_with(db=db_mock, owner_id=test_user.id)

    @patch("app.main.jwt.decode", return_value={"sub": "chani@dune.com"})
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_email_success(self, mock_get_user_by_email, mock_jwt_decode):
        test_token = "mock_token"
        test_email = "chani@dune.com"

        test_user = User(
            id=1,
            email=test_email,
            hashed_password="hashed_password",
            is_verified=False,
            is_active=False,
        )

        mock_get_user_by_email.return_value = test_user

        db_mock = AsyncMock()
        db_mock.commit = AsyncMock()
        result = await confirm_email(token=test_token, db=db_mock)

        # Checks
        self.assertEqual(result, {"message": "Email confirmed"})
        self.assertTrue(test_user.is_verified)
        self.assertTrue(test_user.is_active)
        mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])
        mock_get_user_by_email.assert_called_once_with(db_mock, test_email)
        db_mock.commit.assert_awaited_once()

    @patch("app.main.jwt.decode", side_effect=JWTError)
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_email_invalid_token(self, mock_jwt_decode):
        test_token = "invalid_token"

        db_mock = AsyncMock()

        with self.assertRaises(HTTPException) as exc:
            await confirm_email(token=test_token, db=db_mock)

        self.assertEqual(exc.exception.status_code, 400)
        self.assertEqual(exc.exception.detail, "Invalid token")
        mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])

    @patch("app.main.jwt.decode", return_value={"sub": "unknown@dune.com"})
    @patch("app.main.crud.get_user_by_email", new_callable=AsyncMock)
    @patch("app.main.SECRET_KEY", "mock_secret")
    @patch("app.main.ALGORITHM", "mock_algorithm")
    async def test_confirm_email_user_not_found(self, mock_get_user_by_email, mock_jwt_decode):
        test_token = "mock_token"
        test_email = "unknown@dune.com"

        mock_get_user_by_email.return_value = None

        db_mock = AsyncMock()
        with self.assertRaises(HTTPException) as exc:
            await confirm_email(token=test_token, db=db_mock)

        self.assertEqual(exc.exception.status_code, 404)
        self.assertEqual(exc.exception.detail, "User not found")
        mock_jwt_decode.assert_called_once_with(test_token, "mock_secret", algorithms=["mock_algorithm"])
        mock_get_user_by_email.assert_called_once_with(db_mock, test_email)

    @patch("app.main.cloudinary.uploader.upload", return_value={"secure_url": "mock_url"})
    @patch("app.main.crud.update_avatar", new_callable=AsyncMock)
    async def test_update_avatar_success(self, mock_update_avatar, mock_cloudinary_upload):
        test_user = User(
            id=1,
            email="shaddam@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        updated_user = UserInDB(
            id=test_user.id,
            email=test_user.email,
            hashed_password=test_user.hashed_password,
            is_verified=test_user.is_verified,
            is_active=test_user.is_active,
            avatar="mock_url",
        )

        mock_update_avatar.return_value = updated_user

        test_file = MagicMock(spec=UploadFile)
        test_file.file = MagicMock()

        db_mock = AsyncMock()
        result = await update_avatar(file=test_file, current_user=test_user, db=db_mock)

        # Checks
        self.assertEqual(result, updated_user)
        mock_cloudinary_upload.assert_called_once_with(
            test_file.file,
            public_id=f"PD_REST_API_contacts/{test_user.email}",
            overwrite=True,
        )  # Cloudinary call check
        mock_update_avatar.assert_called_once_with(
            db=db_mock, email=test_user.email, avatar_url="mock_url"
        )  # Updated avatar check

    @patch("app.main.cloudinary.uploader.upload", return_value={})
    async def test_update_avatar_upload_failure(self, mock_cloudinary_upload):
        test_user = User(
            id=1,
            email="ghanima@dune.com",
            hashed_password="hashed_password",
            is_verified=True,
            is_active=True,
        )

        test_file = MagicMock(spec=UploadFile)
        test_file.file = MagicMock()

        db_mock = AsyncMock()
        with self.assertRaises(HTTPException) as exc:
            await update_avatar(file=test_file, current_user=test_user, db=db_mock)

        self.assertEqual(exc.exception.status_code, 500)
        self.assertEqual(exc.exception.detail, "Failed to upload avatar")
        mock_cloudinary_upload.assert_called_once_with(
            test_file.file,
            public_id=f"PD_REST_API_contacts/{test_user.email}",
            overwrite=True,
        )


if __name__ == "__main__":
    unittest.main()

# python3 -m unittest tests.test_main
