API Tests for Auth Endpoints

Base URL
- http://127.0.0.1:8000
- Auth router prefix: /api/v1/auth

Notes
- Start the server before testing. If you used the project's .venv, run:

```powershell
E:/os/apimonitor/backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Use the `Authorization: Bearer <access_token>` header for protected endpoints.
- Save `access_token` and `refresh_token` from the login response as Postman environment variables.

1) Register
- Method: POST
- URL: /api/v1/auth/register
- Body (JSON):
  {
    "email": "alice@example.com",
    "username": "alice",
    "password": "Password123",
    "first_name": "Alice",
    "last_name": "Example"
  }
- Expected: 201 Created
- Sample response: User object with `id`, `email`, `username`, `is_verified` (false)

2) Login
- Method: POST
- URL: /api/v1/auth/login
- Body (JSON):
  {
    "email": "alice@example.com",
    "password": "Password123"
  }
- Expected: 200 OK
- Sample response:
  {
    "access_token": "<jwt>",
    "refresh_token": "<jwt>",
    "token_type": "bearer"
  }
- Postman: save `access_token` and `refresh_token` as environment vars.

3) Get current user
- Method: GET
- URL: /api/v1/auth/me
- Headers: `Authorization: Bearer {{access_token}}`
- Expected: 200 OK
- Response: User object

4) Refresh token
- Method: POST
- URL options:
  - Query param: /api/v1/auth/refresh?refresh_token={{refresh_token}}
  - or POST body (x-www-form-urlencoded) key `refresh_token` with value `{{refresh_token}}`
- Expected: 200 OK
- Response: new `access_token` and `refresh_token` (persisted server-side)

5) Verify email
- Method: POST
- URL: /api/v1/auth/verify-email
- Body (JSON):
  {
    "token": "<verification_token_from_email_or_db>"
  }
- Expected: 200 OK
- Response: { "message": "Email verified successfully" }

6) Resend verification
- Method: POST
- URL: /api/v1/auth/resend-verification
- Headers: `Authorization: Bearer {{access_token}}`
- Expected: 200 OK
- Response: { "message": "Verification email sent successfully" }

7) Forgot password
- Method: POST
- URL: /api/v1/auth/forgot-password
- Body (JSON):
  { "email": "alice@example.com" }
- Expected: 200 OK (always returns success message for security)
- Response: { "message": "If your email is registered, you will receive a password reset link" }

8) Reset password
- Method: POST
- URL: /api/v1/auth/reset-password
- Body (JSON):
  {
    "token": "<password_reset_token>",
    "new_password": "NewPassword123"
  }
- Expected: 200 OK
- Response: { "message": "Password reset successfully" }

9) Logout
- Method: POST
- URL: /api/v1/auth/logout
- Headers: `Authorization: Bearer {{access_token}}`
- Expected: 200 OK
- Response: { "message": "Logged out successfully" }

10) Delete / deactivate account
- Method: DELETE
- URL: /api/v1/auth/account
- Headers: `Authorization: Bearer {{access_token}}`
- Expected: 200 OK
- Response: { "message": "Account deactivated successfully" }

Tips
- If verification or reset tokens are not received via email during testing, read them from the `users` table (`verification_token` / `password_reset_token`).
- Use Postman's "Tests" to store tokens automatically:
  - After login:
    ```javascript
    pm.environment.set("access_token", pm.response.json().access_token);
    pm.environment.set("refresh_token", pm.response.json().refresh_token);
    ```

End of file.
