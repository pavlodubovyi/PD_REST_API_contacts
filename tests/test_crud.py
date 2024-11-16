import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from app import schemas, models
from app.crud import (
    create_contact,
    get_contacts,
    get_contact,
    update_contact,
    delete_contact,
    search_contacts,
    get_upcoming_birthdays,
    get_user_by_email,
    create_user,
    update_avatar
)
from datetime import date


class TestCRUD(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mocking the AsyncSession
        self.session = MagicMock()
        self.session.add = MagicMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()
        self.session.execute = AsyncMock()
        self.owner_id = 1

    async def test_create_contact(self):
        # Data for creating a contact
        contact_data = schemas.ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            birthday=date(1990, 1, 1),
            phone_number="123456789",
            additional_info="Test contact"
        )
        owner_id = 1

        # Expected result
        expected_contact = models.Contact(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            birthday=date(1990, 1, 1),
            phone_number="123456789",
            additional_info="Test contact",
            owner_id=owner_id
        )
        self.session.refresh = AsyncMock(return_value=None)  # Mock refresh operation
        result = await create_contact(self.session, contact_data, owner_id)

        # Checks
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)
        self.assertEqual(result.first_name, expected_contact.first_name)
        self.assertEqual(result.last_name, expected_contact.last_name)
        self.assertEqual(result.email, expected_contact.email)
        self.assertEqual(result.birthday, expected_contact.birthday)
        self.assertEqual(result.phone_number, expected_contact.phone_number)
        self.assertEqual(result.additional_info, expected_contact.additional_info)
        self.assertEqual(result.owner_id, expected_contact.owner_id)

    async def test_get_contacts(self):
        # creating a mock list of contacts
        mock_contacts = [
            models.Contact(
                id=1,
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone_number="1234567890",
                birthday=None,
                additional_info="Friend",
                owner_id=self.owner_id
            ),
            models.Contact(
                id=2,
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone_number="0987654321",
                birthday=None,
                additional_info="Colleague",
                owner_id=self.owner_id
            ),
        ]
        # Configuring the output of self.session.execute
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_contacts
        self.session.execute.return_value.scalars = MagicMock(return_value=mock_scalars)

        # Calling the function
        result = await get_contacts(self.session, self.owner_id)

        # Checks
        self.assertEqual(result, mock_contacts)
        self.session.execute.assert_called_once()

    async def test_get_contact(self):
        mock_contact = models.Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="1234567890",
            birthday=None,
            additional_info="Friend",
            owner_id=self.owner_id
        )

        # Configuring the output of self.session.execute
        self.session.execute.return_value.scalar_one_or_none = MagicMock(return_value=mock_contact)

        # Calling the function
        result = await get_contact(self.session, contact_id=1, owner_id=self.owner_id)

        # Checks
        self.assertEqual(result, mock_contact)
        self.session.execute.assert_called_once()

    @patch("app.crud.get_contact")
    async def test_update_contact(self, mock_get_contact):
        existing_contact = models.Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="1234567890",
            birthday=None,
            additional_info="Friend",
            owner_id=self.owner_id,
        )

        updated_data = schemas.ContactUpdate(
            first_name="Jane",
            last_name="Smith",
            phone_number="0987654321",
        )

        expected_contact = models.Contact(
            id=1,
            first_name="Jane",
            last_name="Smith",
            email="john.doe@example.com",
            phone_number="0987654321",
            birthday=None,
            additional_info="Friend",
            owner_id=self.owner_id,
        )

        mock_get_contact.return_value = existing_contact

        # Calling the function
        result = await update_contact(self.session, contact_id=1, contact=updated_data, owner_id=self.owner_id)

        # Checks
        self.assertEqual(result.first_name, expected_contact.first_name)
        self.assertEqual(result.last_name, expected_contact.last_name)
        self.assertEqual(result.phone_number, expected_contact.phone_number)
        self.assertEqual(result.email, expected_contact.email)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(existing_contact)

    @patch("app.crud.get_contact")
    async def test_delete_contact(self, mock_get_contact):
        contact_to_delete = models.Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="1234567890",
            birthday=None,
            additional_info="Friend",
            owner_id=self.owner_id,
        )

        mock_get_contact.return_value = contact_to_delete
        self.session.delete = AsyncMock()
        self.session.commit = AsyncMock()

        # Calling the function
        result = await delete_contact(self.session, contact_id=1, owner_id=self.owner_id)

        # Checks
        self.session.delete.assert_called_once_with(contact_to_delete)  # Check if delete method was called with contact
        self.session.commit.assert_called_once()
        self.assertEqual(result, contact_to_delete)

    async def test_search_contacts(self):
        contact1 = models.Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="1234567890",
            birthday=None,
            additional_info="Friend",
            owner_id=self.owner_id,
        )
        contact2 = models.Contact(
            id=2,
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone_number="0987654321",
            birthday=None,
            additional_info="Colleague",
            owner_id=self.owner_id,
        )

        # Mock for scalars().all()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [contact1, contact2]

        # Mock for result of execute()
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        # Mock for session.execute()
        self.session.execute = AsyncMock(return_value=mock_result)

        # Calling the function
        query = "Doe"
        result = await search_contacts(self.session, query=query, owner_id=self.owner_id)

        # Checks
        self.session.execute.assert_called_once()
        self.assertEqual(result, [contact1, contact2])

    @patch("app.crud.datetime")
    async def test_get_upcoming_birthdays(self, mock_datetime):
        mock_contacts = [
            models.Contact(
                id=1,
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone_number="1234567890",
                birthday=date(1990, 11, 20),
                additional_info="Friend",
                owner_id=self.owner_id,
            ),
            models.Contact(
                id=2,
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone_number="0987654321",
                birthday=date(1990, 11, 18),
                additional_info="Colleague",
                owner_id=self.owner_id,
            ),
        ]

        # Mock datetime.today().date()
        mock_today = date(2024, 11, 15)
        mock_datetime.today.return_value = MagicMock(date=MagicMock(return_value=mock_today))

        mock_execute_result = MagicMock()
        self.session.execute.return_value = mock_execute_result

        mock_scalars_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result

        mock_scalars_result.all.return_value = mock_contacts
        result = await get_upcoming_birthdays(self.session, owner_id=self.owner_id)

        # Checks
        self.assertEqual(len(result), 2)
        self.assertIn(mock_contacts[0], result)
        self.assertIn(mock_contacts[1], result)
        # self.session.execute.assert_called_once()
        # mock_execute_result.scalars.assert_called_once()
        # mock_scalars_result.all.assert_called_once()

    @patch("app.crud.AsyncSession")
    async def test_get_user_by_email(self, mock_async_session):
        mock_user = models.User(
            id=1,
            email="john.doe@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True,
        )

        # Mocking the database interaction
        mock_execute_result = MagicMock()
        mock_session = AsyncMock()
        mock_async_session.return_value = mock_session
        mock_session.execute.return_value = mock_execute_result
        mock_execute_result.scalar_one_or_none.return_value = mock_user

        # Calling the tested function
        result = await get_user_by_email(mock_session, email="john.doe@example.com")

        # Checks
        self.assertEqual(result, mock_user)  # if the user is correct
        self.assertIn(result.email, "john.doe@example.com")  # if the email is correct

    @patch("app.crud.AsyncSession")
    async def test_create_user(self, mock_async_session):
        mock_user = models.User(
            id=1,
            email="john.doe@example.com",
            hashed_password="hashed_password",
            is_active=False,
            is_verified=False,
        )

        # Mocking the database interaction
        mock_session = AsyncMock()
        mock_async_session.return_value = mock_session
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Calling the tested function
        result = await create_user(mock_session, mock_user.email, mock_user.hashed_password)

        # Checks
        mock_session.add.assert_called_once()  # if user was added to DB
        mock_session.commit.assert_called_once()  # if data were committed to DB
        mock_session.refresh.assert_called_once()  # if data were refreshed
        self.assertEqual(result.email, "john.doe@example.com")  # if newly-added user has this email
        self.assertIsInstance(result, models.User)  # if the result is a User object

    #
    @patch("app.crud.get_user_by_email")
    @patch("app.crud.AsyncSession")
    async def test_update_avatar(self, mock_async_session, mock_get_user_by_email):
        mock_user = models.User(
            id=1,
            email="john.doe@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True,
            avatar=None
        )

        new_avatar_url = "https://new.avatar.url/avatar.png"

        # Mocking the get_user_by_email function
        mock_get_user_by_email.return_value = mock_user

        # Mocking the database interaction
        mock_session = AsyncMock()
        mock_async_session.return_value = mock_session
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        # mock_session.refresh = AsyncMock()

        # Calling the tested function
        result = await update_avatar(mock_session, email="john.doe@example.com", avatar_url=new_avatar_url)

        # Checks
        self.assertEqual(result.avatar, new_avatar_url)  # Avatar URL was updated
        mock_get_user_by_email.assert_called_once_with(mock_session,
                                                       "john.doe@example.com")  # Check if get_user_by_email was called
        mock_session.add.assert_called_once_with(mock_user)  # if updated user data were added to DB
        mock_session.commit.assert_called_once()  # if commit was called


if __name__ == "__main__":
    unittest.main()
