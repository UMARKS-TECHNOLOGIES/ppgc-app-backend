# Two-Factor Authentication (2FA) Module

## Overview
Complete implementation of Time-based One-Time Password (TOTP) two-factor authentication with backup code recovery support.

## Components

### 1. **Models** (`models.py`)

#### `TwoFactorAuth`
Stores 2FA settings for each user:
- `id`: Primary key
- `user_id`: Foreign key to User
- `is_enabled`: Boolean flag for 2FA activation status
- `secret_key`: Base32 encoded TOTP secret
- `backup_codes`: Comma-separated backup codes
- `method`: Authentication method (currently "totp")
- `phone_number`: Optional phone number for SMS (future use)
- `verified`: Boolean indicating successful setup verification
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

#### `TwoFactorAuthLog`
Audit log for 2FA activities:
- `id`: Primary key
- `user_id`: Foreign key to User
- `attempt_type`: Type of attempt (setup, verify, disable, failed_attempt)
- `success`: Boolean indicating success/failure
- `ip_address`: IP address of the request
- `user_agent`: Browser/client user agent
- `created_at`: Timestamp of the attempt

### 2. **Schemas** (`schemas.py`)

#### Request Schemas
- **Enable2FARequest**: Method selection (totp, optional phone)
- **Verify2FARequest**: 6-digit TOTP code
- **Disable2FARequest**: Password confirmation
- **GenerateBackupCodesRequest**: Password confirmation

#### Response Schemas
- **Setup2FAResponse**: 
  - `secret`: Base32 encoded TOTP secret
  - `qr_code_url`: Base64 encoded QR code image
  - `backup_codes`: List of 10 backup codes
  - `method`: "totp"

- **Verify2FAResponse**:
  - `verified`: Boolean status
  - `message`: Response message

- **TwoFactorAuthSchema**: Complete 2FA status information

### 3. **Services** (`services.py`)

#### Core Functions

**`generate_totp_secret()`**
- Generates random TOTP secret
- Returns: Base32 encoded string

**`generate_backup_codes(count=10)`**
- Creates recovery codes
- Returns: List of hex-encoded strings

**`generate_qr_code(secret, email, app_name="PPGC")`**
- Creates QR code for TOTP setup
- Returns: Base64 encoded PNG image

**`setup_totp_2fa(user_id, session, email)`**
- Initializes 2FA for user
- Generates secret and backup codes
- Returns: Setup2FAResponse

**`verify_totp_code(user_id, code, session, ip_address, user_agent)`**
- Verifies 6-digit TOTP code
- Allows 30-second window tolerance
- Logs verification attempt
- Returns: Verify2FAResponse

**`verify_backup_code(user_id, code, session, ip_address, user_agent)`**
- Verifies and consumes backup code
- Removes used code from storage
- Returns: Verify2FAResponse

**`disable_2fa(user_id, password, session)`**
- Disables 2FA with password confirmation
- Clears secret and backup codes
- Returns: Status message

**`regenerate_backup_codes(user_id, password, session)`**
- Generates new backup codes
- Requires password confirmation
- Returns: New backup codes list

**`get_2fa_status(user_id, session)`**
- Retrieves current 2FA settings
- Returns: TwoFactorAuthSchema

**`get_user_2fa_settings(user_id, session)`**
- Helper to fetch 2FA record from DB
- Returns: TwoFactorAuth model or None

### 4. **Routes** (`routes.py`)

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/2fa/setup` | Initialize TOTP 2FA setup |
| `POST` | `/2fa/verify` | Verify TOTP code |
| `POST` | `/2fa/verify-backup` | Verify backup code for recovery |
| `GET` | `/2fa/status` | Get current 2FA status |
| `POST` | `/2fa/disable` | Disable 2FA (password required) |
| `POST` | `/2fa/regenerate-backup-codes` | Generate new backup codes (password required) |

#### Endpoint Details

**POST `/2fa/setup`**
```json
Request:
{
  "method": "totp"
}

Response:
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_code_url": "data:image/png;base64,...",
  "backup_codes": [
    "a1b2c3d4",
    "e5f6g7h8",
    ...
  ],
  "method": "totp"
}
```

**POST `/2fa/verify`**
```json
Request:
{
  "code": "123456"
}

Response:
{
  "verified": true,
  "message": "2FA code verified successfully"
}
```

**POST `/2fa/verify-backup`**
```json
Request:
{
  "code": "a1b2c3d4"
}

Response:
{
  "verified": true,
  "message": "Backup code verified and consumed"
}
```

**GET `/2fa/status`**
```json
Response:
{
  "id": 1,
  "user_id": 123,
  "is_enabled": true,
  "method": "totp",
  "verified": true,
  "phone_number": null,
  "created_at": "2025-12-09T10:30:00Z",
  "updated_at": "2025-12-09T10:35:00Z"
}
```

**POST `/2fa/disable`**
```json
Request:
{
  "password": "user_password"
}

Response:
{
  "message": "2FA disabled successfully"
}
```

**POST `/2fa/regenerate-backup-codes`**
```json
Request:
{
  "password": "user_password"
}

Response:
{
  "message": "Backup codes regenerated successfully",
  "backup_codes": [
    "new_code_1",
    "new_code_2",
    ...
  ]
}
```

## Security Features

✅ **TOTP Compliance**
- RFC 6238 compliant
- 30-second time window with 1-time step tolerance
- Base32 encoded secrets

✅ **Backup Codes**
- One-time use backup codes
- Hex-encoded 32-bit values
- Automatically consumed after use
- 10 codes generated per setup

✅ **Password Protection**
- Disable 2FA requires password confirmation
- Regenerate codes requires password confirmation
- Additional security layer for critical operations

✅ **Audit Logging**
- All 2FA activities logged
- IP address and user agent captured
- Success/failure tracking
- Activity timestamp recording

✅ **Error Handling**
- Detailed error messages
- Proper HTTP status codes
- Transaction rollback on failure
- Input validation

## QR Code Generation

The system automatically generates QR codes for easy TOTP setup:
- Standard TOTP provisioning URI format
- Compatible with Google Authenticator, Authy, Microsoft Authenticator
- Base64 encoded for API transmission
- PNG format with error correction

## Installation Requirements

```bash
pip install pyotp qrcode pillow
```

## Usage Flow

### Setup 2FA
1. User calls `POST /2fa/setup`
2. System generates secret and backup codes
3. QR code generated for authenticator app
4. User scans QR code and receives secret
5. User enters verification code

### Verify Setup
1. User calls `POST /2fa/verify` with 6-digit code
2. System validates TOTP code
3. 2FA marked as verified and enabled
4. User receives confirmation

### Daily Authentication
1. User provides username/password
2. System prompts for TOTP code
3. User calls `POST /2fa/verify` with current code
4. Access granted if code is valid

### Recovery with Backup Codes
1. User provides username/password
2. System prompts for TOTP code
3. User calls `POST /2fa/verify-backup` with backup code
4. Access granted and backup code consumed

### Disable 2FA
1. User calls `POST /2fa/disable` with password
2. System verifies password
3. 2FA settings cleared
4. Access no longer requires TOTP

## Status Codes

| Code | Meaning |
|------|---------|
| 201 | 2FA setup successful |
| 200 | Request successful |
| 400 | Invalid input or 2FA already enabled |
| 401 | Invalid code or password |
| 404 | 2FA not found |
| 500 | Server error |

## Notes

- TOTP codes are time-based and change every 30 seconds
- System tolerates time skew with 1-step window (±30 seconds)
- Backup codes are single-use and must be stored securely by user
- All timestamps use UTC timezone
- Password verification uses bcrypt hashing
- QR codes remain valid for the lifetime of the secret
