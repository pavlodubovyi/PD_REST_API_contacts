Utilities
=========

This project includes several utility files located in the `utils/` directory. These utilities provide additional functionality, including testing CORS, manually creating database tables, generating secret keys, and testing JWT tokens.

CORS Test Page
--------------
**File**: `utils/CORS_test_page.html`

This HTML file is used to test CORS (Cross-Origin Resource Sharing) functionality for the Contact List API. It includes a button that triggers a GET request to the `/contacts/` endpoint to verify if the CORS settings allow access from a web browser on a different origin.

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Test CORS</title>
   </head>
   <body>
       <h1>Test CORS</h1>
       <button onclick="testCors()">Send Request</button>

       <script>
           function testCors() {
               fetch("http://127.0.0.1:8000/contacts/", {
                   method: "GET",
                   headers: {
                       "Content-Type": "application/json",
                       "Authorization": "Bearer " // Add your token here
                   }
               })
               .then(response => response.json())
               .then(data => console.log(data))
               .catch(error => console.error("Error:", error));
           }
       </script>
   </body>
   </html>

The file includes a placeholder ("Add your token here") for the Authorization token, which should be populated to test CORS functionality effectively.


Python Utilities
----------------

The following Python utility files in the `utils/` directory perform additional project functions:

**File**: `utils/create_tables.py`
This Python script can be used to manually create tables in the database, if necessary. It initializes the database by creating all tables defined in the `app.models` module.

**File**: `utils/secret_key_generator.py`
This script generates a secure, random secret key using Python’s `secrets` module. The generated key can be used for setting the `SECRET_KEY` in your `.env` file for JWT token encryption.

**File**: `utils/token_test.py`
This script is a utility for creating and decoding JSON Web Tokens (JWTs). It demonstrates how to encode data into a JWT token and then decode it for verification purposes.


.. automodule:: utils.create_tables
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. automodule:: utils.secret_key_generator
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. automodule:: utils.token_test
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
