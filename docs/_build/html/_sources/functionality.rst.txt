Functionality
=============

Refer to `/docs` (Swagger UI) for detailed API functionality.

Here’s an overview:

- **POST** `/register` - Register a new user
- **POST** `/login` - Login to receive access and refresh tokens
- **POST** `/contacts/` - Create a new contact (rate limited)
- **GET** `/contacts/` - Retrieve all contacts
- **GET** `/contacts/{contact_id}` - Retrieve a contact by ID
- **PUT** `/contacts/{contact_id}` - Update a contact by ID
- **DELETE** `/contacts/{contact_id}` - Delete a contact by ID
- **GET** `/contacts/search/` - Search contacts by query
- **GET** `/contacts/birthdays/` - Retrieve contacts with birthdays in the next 7 days
- **POST** `/request-password-reset/` - Request a password reset link
- **POST** `/confirm-password-reset/{token}` - Reset password with the token
- **PATCH** `/avatar` - Upload or update avatar
