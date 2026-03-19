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


------------------------------------------------------------
Monitoring + Scheduler API Tests

Base URL
- http://127.0.0.1:8000
- Monitoring router prefix: /api/v1

Auth
- All monitoring/scheduler endpoints require: `Authorization: Bearer <access_token>`
- Reuse the login flow from the Auth section above to get `access_token`.

Notes / Validation rules (important)
- `interval_seconds` must be between **30** and **1800**.
- Optional `duration_seconds`:
  - must be **>= interval_seconds**
  - must be **<= 7 days** (604800 seconds)
- Payload rules:
  - For GET/DELETE/HEAD/etc, do NOT send/store a payload.
  - For POST/PUT/PATCH, if `payload` is provided then `payload_type` is required.
  - Allowed `payload_type`: `json`, `form`, `raw`.

Windows CMD quick setup
```bat
set BASE_URL=http://127.0.0.1:8000
set TOKEN=<paste_access_token_here>
```

PowerShell quick setup
```powershell
$env:BASE_URL = "http://127.0.0.1:8000"
$env:TOKEN = "<paste_access_token_here>"
```

1) Register an API to monitor

Example: GET API (no payload)

CMD:
```bat
curl -X POST "%BASE_URL%/api/v1/monitor/apis" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Example GET\",\"url\":\"https://httpbin.org/get\",\"method\":\"GET\",\"description\":\"basic GET\"}"
```

PowerShell:
```powershell
curl -X POST "$env:BASE_URL/api/v1/monitor/apis" `
  -H "Authorization: Bearer $env:TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"name":"Example GET","url":"https://httpbin.org/get","method":"GET","description":"basic GET"}'
```

Expected: 201 Created
- Save the response `id` as `API_ID`.

2) List APIs

CMD:
```bat
curl -X GET "%BASE_URL%/api/v1/monitor/apis" -H "Authorization: Bearer %TOKEN%"
```

3) Get API by ID

CMD:
```bat
set API_ID=<paste_api_id_here>
curl -X GET "%BASE_URL%/api/v1/monitor/apis/%API_ID%" -H "Authorization: Bearer %TOKEN%"
```

4) Test-run an API once (creates an APILog row)

CMD:
```bat
curl -X POST "%BASE_URL%/api/v1/monitor/apis/%API_ID%/test" -H "Authorization: Bearer %TOKEN%"
```

Expected: 200 OK with a log entry including `status_code`, `response_time_ms`, `success`.

5) Create a schedule for an API

Run indefinitely:

CMD:
```bat
curl -X POST "%BASE_URL%/api/v1/monitor/apis/%API_ID%/schedule" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"interval_seconds\":30}"
```

Run for a fixed duration (example: 2 minutes):

CMD:
```bat
curl -X POST "%BASE_URL%/api/v1/monitor/apis/%API_ID%/schedule" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"interval_seconds\":30,\"duration_seconds\":120}"
```

Expected: 200 OK with schedule fields like `enabled`, `next_run`, and optional `end_at`.

6) Verify scheduler is actually running (wait + fetch logs)

- Wait ~35-70 seconds (depending on interval_seconds) so that at least 1 run happens.

CMD:
```bat
curl -X GET "%BASE_URL%/api/v1/monitor/apis/%API_ID%/logs" -H "Authorization: Bearer %TOKEN%"
```

Expected: 200 OK with an array of logs (most recent first).

7) Optional: Test a POST with JSON payload (payload_type required)

Create API:

CMD:
```bat
curl -X POST "%BASE_URL%/api/v1/monitor/apis" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Example POST\",\"url\":\"https://httpbin.org/post\",\"method\":\"POST\",\"payload_type\":\"json\",\"payload\":\"{\\\"hello\\\":\\\"world\\\"}\"}"
```

Then schedule/test it as in steps 4-6.

Known limitation (current code)

8) Delete schedules for an API (does NOT delete the API)

CMD:
```bat
curl -X DELETE "%BASE_URL%/api/v1/monitor/apis/%API_ID%/schedules" -H "Authorization: Bearer %TOKEN%"
```

Expected: 204 No Content

9) Delete an API (also deletes any schedule rows for it)

CMD:
```bat
curl -X DELETE "%BASE_URL%/api/v1/monitor/apis/%API_ID%" -H "Authorization: Bearer %TOKEN%"
```

Expected: 204 No Content

Notes
- Scheduling continues via the background loop in `app/main.py` for any rows in `api_schedules` where `enabled = true`.
- When deleting an API, schedules are removed as well (defensive delete in service + FK cascade in DB).

End of scheduler tests.

Postman templates
- Import these files into Postman:
  - `postman/APIMonitor-Scheduler.postman_collection.json`
  - `postman/APIMonitor.postman_environment.json`
- Then select the environment **APIMonitor Local** and run requests in this order:
  1) Auth - Login (sets tokens)
  2) Monitor - Register API (sets api_id)
  3) Scheduler - Create Schedule
  4) Wait ~35-70 seconds
  5) Scheduler - Get Logs
