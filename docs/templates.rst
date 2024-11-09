Templates
=========

This project includes several HTML templates located in the `app/templates/` directory. These templates are used for email notifications and user interactions. Here are the templates and their purposes:

Email Verification Template
---------------------------
**File**: `app/templates/email_template.html`

This template is used for sending email verification links to users who have registered for the service.

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="utf-8">
       <title>Email Verification</title>
   </head>
   <body>
   <p>Hi {{username}},</p>
   <p>Thank you for signing up for our service.</p>
   <p>Please click the following link to verify your email address:</p>
   <p>
       <a href="{{host}}/auth/confirm_email/{{token}}">
           Verification
       </a>
   </p>
   <p>If you did not sign up for our service, please ignore this email.</p>
   <p>Thanks,</p>
   <p>Our Great Team</p>
   </body>
   </html>

This template includes placeholders for `username`, `host`, and `token` which are dynamically populated when the email is sent.


Password Reset Email Template
-----------------------------
**File**: `app/templates/reset_pass_email.html`

This template is used for sending a password reset link to users who request it.

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="utf-8">
       <title>Password Reset</title>
   </head>
   <body>
   <p>Hi {{username}},</p>
   <p>We received a request to reset your password for your account.</p>
   <p>Please click the following link to reset your password:</p>
   <p>
       <a href="{{host}}/reset-password-form/{{token}}">
           Reset Password
       </a>
   </p>
   <p>If you did not request a password reset, please ignore this email.</p>
   <p>Thanks,</p>
   <p>Our Great Team</p>
   </body>
   </html>

This template includes placeholders for `username`, `host`, and `token` to personalize the message and generate a unique reset link.


Password Reset Form Template
----------------------------
**File**: `app/templates/reset_pass_form.html`

This template provides a form where users can enter a new password. It is accessed by following the link in the password reset email.

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="utf-8">
       <title>Reset Password</title>
   </head>
   <body>
   <h2>Reset Password</h2>
   <form action="/confirm-password-reset/{{token}}" method="post">
       <label for="new_password">New Password:</label>
       <input type="password" name="new_password" required>
       <button type="submit">Reset Password</button>
   </form>
   </body>
   </html>

This template includes a form field for `new_password` and uses the `token` to verify the request.

Each template is tailored to provide the user with a smooth and secure experience while interacting with the Contact List API.
