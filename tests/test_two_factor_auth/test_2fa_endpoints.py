"""
Test suite for two-factor authentication endpoints.
"""
import pytest
import pyotp
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ppgc_backend.app.models import User
from ppgc_backend.app.controllers.two_factor_auth.models import TwoFactorAuth, TwoFactorAuthLog
from ppgc_backend.app.controllers.auth.services import (
    create_user,
    fetch_access_token,
)
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema


async def create_test_user(
    db: AsyncSession,
    email: str = "test_2fa@example.com",
    first_name: str = "Test2FA",
):
    """Helper function to create a test user"""
    user_data = UserRegistrationSchema(
        email=email,
        pin="password123",
        first_name=first_name,
        last_name="User",
    )
    return await create_user(db, user_data)

@pytest.mark.asyncio
async def test_setup_2fa_already_enabled(client_fixture):
    """Test setting up 2FA when already enabled"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA first time
    setup_data = {"method": "totp"}
    response1 = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    assert response1.status_code == 201
    secret = response1.json()['secret']

    # Verify the setup to enable 2FA
    verify_data = {"code": pyotp.TOTP(secret).now()}
    response_verify = await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )
    assert response_verify.status_code == 200

    # Try to setup again
    response2 = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    assert response2.status_code == 400
    assert "already enabled" in response2.json()['detail']


@pytest.mark.asyncio
async def test_verify_2fa_invalid_code(client_fixture):
    """Test verifying invalid TOTP code"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    assert setup_response.status_code == 201

    # Try invalid code
    verify_data = {"code": "000000"}
    response = await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    assert response.status_code == 401
    assert "Invalid 2FA code" in response.json()['detail']


@pytest.mark.asyncio
async def test_verify_backup_code_invalid(client_fixture):
    """Test verifying invalid backup code"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    assert setup_response.status_code == 201
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    # Try invalid backup code
    invalid_backup = {"code": "invalid_code"}
    response = await httpx_client.post(
        "/2fa/verify-backup",
        json=invalid_backup,
        headers=headers
    )

    assert response.status_code == 401
    assert "Invalid backup code" in response.json()['detail']


@pytest.mark.asyncio
async def test_backup_code_one_time_use(client_fixture):
    """Test that backup codes can only be used once"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    backup_codes = setup_response.json()['backup_codes']
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    # Use backup code first time
    first_use = {"code": backup_codes[0]}
    response1 = await httpx_client.post(
        "/2fa/verify-backup",
        json=first_use,
        headers=headers
    )
    assert response1.status_code == 200

    # Try to use same backup code again
    response2 = await httpx_client.post(
        "/2fa/verify-backup",
        json=first_use,
        headers=headers
    )
    assert response2.status_code == 401
    assert "Invalid backup code" in response2.json()['detail']


@pytest.mark.asyncio
async def test_disable_2fa_wrong_password(client_fixture):
    """Test disabling 2FA with wrong password"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    # Try to disable with wrong password
    disable_data = {"password": "wrong_password"}
    response = await httpx_client.post(
        "/2fa/disable",
        json=disable_data,
        headers=headers
    )

    assert response.status_code == 401
    assert "Invalid password" in response.json()['detail']


@pytest.mark.asyncio
async def test_regenerate_backup_codes_wrong_password(client_fixture):
    """Test regenerating backup codes with wrong password"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    # Try to regenerate with wrong password
    regen_data = {"password": "wrong_password"}
    response = await httpx_client.post(
        "/2fa/regenerate-backup-codes",
        json=regen_data,
        headers=headers
    )

    assert response.status_code == 401
    assert "Invalid password" in response.json()['detail']


@pytest.mark.asyncio
async def test_unauthorized_access(client_fixture):
    """Test accessing 2FA endpoints without authentication"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Try to setup without token
    setup_data = {"method": "totp"}
    response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_without_setup(client_fixture):
    """Test verifying 2FA without setting it up first"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try to verify without setup
    verify_data = {"code": "123456"}
    response = await httpx_client.post(
        "/2fa/verify",
        json=verify_data,
        headers=headers
    )

    assert response.status_code == 400
    assert "not set up" in response.json()['detail']


@pytest.mark.asyncio
async def test_2fa_audit_logging(client_fixture):
    """Test that 2FA attempts are logged"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup and verify
    setup_response = await httpx_client.post(
        "/2fa/setup",
        json={"method": "totp"},
        headers=headers
    )
    secret = setup_response.json()['secret']

    verify_code = pyotp.TOTP(secret).now()
    await httpx_client.post(
        "/2fa/verify",
        json={"code": verify_code},
        headers=headers
    )

    # Check logs in database
    query = select(TwoFactorAuthLog).where(TwoFactorAuthLog.user_id == user.id)
    result = await test_db.execute(query)
    logs = result.scalars().all()

    assert len(logs) > 0
    assert any(log.attempt_type == "verify" for log in logs)


@pytest.mark.asyncio
async def test_qr_code_generation(client_fixture):
    """Test that QR code is generated correctly"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    response = await httpx_client.post(
        "/2fa/setup",
        json={"method": "totp"},
        headers=headers
    )

    assert response.status_code == 201
    json_response = response.json()
    qr_code_url = json_response['qr_code_url']
    
    # Check QR code format
    assert qr_code_url.startswith("data:image/png;base64,")
    assert len(qr_code_url) > 100  # Reasonable length for encoded image


@pytest.mark.asyncio
async def test_multiple_users_2fa_isolation(client_fixture):
    """Test that 2FA settings are isolated between users"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create two users
    user1 = await create_test_user(test_db, email="user1_2fa@example.com")
    user2 = await create_test_user(test_db, email="user2_2fa@example.com")

    token1 = fetch_access_token(user=user1)['access_token']
    token2 = fetch_access_token(user=user2)['access_token']
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User1 setup 2FA
    response1 = await httpx_client.post(
        "/2fa/setup",
        json={"method": "totp"},
        headers=headers1
    )
    secret1 = response1.json()['secret']

    # User2 setup 2FA
    response2 = await httpx_client.post(
        "/2fa/setup",
        json={"method": "totp"},
        headers=headers2
    )
    secret2 = response2.json()['secret']

    # Verify User1 with their own code
    verify_data1 = {"code": pyotp.TOTP(secret1).now()}
    response = await httpx_client.post(
        "/2fa/verify",
        json=verify_data1,
        headers=headers1
    )
    assert response.status_code == 200

    # User1's status should be verified
    status1 = await httpx_client.get("/2fa/status", headers=headers1)
    assert status1.json()['verified'] is True

    # User2's status should still be unverified
    status2 = await httpx_client.get("/2fa/status", headers=headers2)
    assert status2.json()['verified'] is False
