import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from ppgc_backend.config.settings import (
    SUPER_ADMIN_PASSWORD,
    SUPER_ADMIN_EMAIL_ADDRESS,
)
from ppgc_backend.app.controllers.auth.models import RoleBasedToken, RoleChoice
from ppgc_backend.app.controllers.auth.services import (
    generate_staff_invite_link,
    validate_and_use_role_token,
)
from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.app.controllers.auth.services import initialize_admin
from ppgc_backend.tests.auth.test_user_creation import create_test_user, UserRegistrationSchema
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice


@pytest.mark.asyncio
async def test_generate_staff_link_admin_only(client__fixture):
    """Test that only admins can generate staff links"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Create regular user
    regular_user = await create_test_user(test_db)
    user_data = UserRegistrationSchema(
        email=regular_user.email,
        password="password123",
        first_name="Regular"
    )
    access_token = await signin_for_access_token(user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    payload = {
        'role': 'staff',
        'expires_in_days': 3
    }
    resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_generate_staff_link_success(client__fixture):
    """Test successfully generating a staff invite link as admin"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Initialize admin
    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    payload = {
        'role': 'staff',
        'email': 'newstaff@example.com',
        'expires_in_days': 7
    }

    resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['role'] == 'staff'
    assert data['token']
    assert data['expires_at']
    assert 'detail' in data


@pytest.mark.asyncio
async def test_generate_staff_link_invalid_role(client__fixture):
    """Test generating link with invalid role"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    payload = {
        'role': 'invalid_role',
        'expires_in_days': 7
    }

    resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_generate_staff_link_expiry_validation(client__fixture):
    """Test expiry days validation (1-90 range)"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    # Test expires_in_days > 90
    payload = {
        'role': 'staff',
        'expires_in_days': 100
    }

    resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_role_token_validation_success(client__fixture):
    """Test successful role token validation"""
    test_db: AsyncSession = client__fixture['db']

    admin = await initialize_admin(test_db)

    # Generate token
    result = await generate_staff_invite_link(
        role=UserRoleChoice.staff,
        db=test_db,
        admin_user=admin,
        email='newstaff@example.com',
        expires_in_days=7
    )

    plain_token = result['token']

    # Validate token
    role = await validate_and_use_role_token(plain_token, test_db)
    assert role == 'staff'

    # Verify token is marked as used
    from sqlalchemy.future import select
    token_record = (await test_db.execute(
        select(RoleBasedToken).where(RoleBasedToken.is_used == True)
    )).scalars().first()
    assert token_record is not None
    assert token_record.is_used is True


@pytest.mark.asyncio
async def test_role_token_validation_invalid_token(client__fixture):
    """Test validation with invalid token"""
    test_db: AsyncSession = client__fixture['db']

    role = await validate_and_use_role_token('invalid_token_12345', test_db)
    assert role is None


@pytest.mark.asyncio
async def test_role_token_validation_expired(client__fixture):
    """Test validation with expired token"""
    test_db: AsyncSession = client__fixture['db']

    from ppgc_backend.app.controllers.auth.services import hash_token

    # Create expired token
    expired_token = RoleBasedToken(
        role=UserRoleChoice.staff,
        token_hash=hash_token('expired_token_123'),
        email='test@example.com',
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        is_used=False
    )
    test_db.add(expired_token)
    await test_db.commit()

    # Try to validate - should fail
    role = await validate_and_use_role_token('expired_token_123', test_db)
    assert role is None


@pytest.mark.asyncio
async def test_role_token_cannot_be_reused(client__fixture):
    """Test that a token can only be used once"""
    test_db: AsyncSession = client__fixture['db']

    admin = await initialize_admin(test_db)

    # Generate token
    result = await generate_staff_invite_link(
        role=UserRoleChoice.staff,
        db=test_db,
        admin_user=admin,
        expires_in_days=7
    )

    plain_token = result['token']

    # First validation should succeed
    role1 = await validate_and_use_role_token(plain_token, test_db)
    assert role1 == 'staff'

    # Second validation should fail (already used)
    role2 = await validate_and_use_role_token(plain_token, test_db)
    assert role2 is None


@pytest.mark.asyncio
async def test_admin_can_generate_multiple_links(client__fixture):
    """Test that admin can generate multiple staff links"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    # Generate multiple links
    tokens = []
    for i in range(3):
        payload = {
            'role': 'staff',
            'email': f'staff{i}@example.com',
            'expires_in_days': 7
        }

        resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
        assert resp.status_code == 201
        tokens.append(resp.json()['token'])

    # Verify all tokens are unique
    assert len(set(tokens)) == 3, "All tokens should be unique"

    # Verify all links are in database
    from sqlalchemy.future import select
    result = await test_db.execute(select(RoleBasedToken).where(RoleBasedToken.is_used == False))
    db_tokens = result.scalars().all()
    assert len(db_tokens) == 3


@pytest.mark.asyncio
async def test_token_has_timestamp_component(client__fixture):
    """Test that generated tokens include timestamp for uniqueness"""
    test_db: AsyncSession = client__fixture['db']

    admin = await initialize_admin(test_db)

    # Generate two tokens in quick succession
    result1 = await generate_staff_invite_link(
        role=UserRoleChoice.staff,
        db=test_db,
        admin_user=admin,
        expires_in_days=7
    )

    result2 = await generate_staff_invite_link(
        role=UserRoleChoice.staff,
        db=test_db,
        admin_user=admin,
        expires_in_days=7
    )

    token1 = result1['token']
    token2 = result2['token']

    # Tokens should be different (due to timestamp component)
    assert token1 != token2, "Tokens generated at different times should be unique"

    # Both tokens should contain a dot separator (random.timestamp format)
    assert '.' in token1, "Token should contain timestamp separator"
    assert '.' in token2, "Token should contain timestamp separator"


@pytest.mark.asyncio
async def test_generate_link_for_different_roles(client__fixture):
    """Test generating invite links for different roles"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, http_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    roles = ['staff', 'agent']

    for role in roles:
        payload = {
            'role': role,
            'expires_in_days': 7
        }

        resp = await http_client.post('/auth/generate-staff-link/', json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data['role'] == role