import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.app.controllers.bank_accounts.models import BankAccount
from ppgc_backend.tests.auth.test_user_creation import create_test_user, UserRegistrationSchema


@pytest.mark.asyncio
async def test_create_and_list_bank_account(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create user and get token
    created_user = await create_test_user(test_db)
    guest_user = await create_test_user(test_db,UserRegistrationSchema(
        email="new@example.com",
        pin="password123",
        first_name="John",
        last_name="Doe",
    ))
    token = fetch_access_token(created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    guest_token = fetch_access_token(guest_user)["access_token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}

    payload = {
        "account_number": "1234567890",
        "account_name": "John Doe",
        "bank_name": "Test Bank",
        "bank_code": "TB01",
        "currency": "NGN"
    }

    #------------------------------
    # Create bank account
    #------------------------------
    response = await httpx_client.post(
        "/bank-accounts/", 
        json=payload, 
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert 'id' in data
    id = data['id']
    assert data["account_number"] == payload["account_number"]
    assert data["bank_name"] == payload["bank_name"]

    #------------------------------
    # Get bank account
    #------------------------------
    response = await httpx_client.get(
        f"/bank-accounts/{id}/", 
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_number"] == payload["account_number"]
    assert data["bank_name"] == payload["bank_name"]

    #------------------------------
    # Make same request with guest details 
    #------------------------------
    response = await httpx_client.get(
        f"/bank-accounts/{id}/", 
        headers=guest_headers
    )
    assert response.status_code == 403

    #------------------------------
    # List bank accounts for user
    #------------------------------
    response = await httpx_client.get(
        "/bank-accounts/", 
        headers=headers
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert any(acc["account_number"] == payload["account_number"] for acc in result)


    #------------------------------
    # Upload with host details
    #------------------------------
    update_payload = {
        "bank_name": "Owner Bank Updated", 
        "account_number": "5556667778", 
        "currency": "USD"
    }
    response = await httpx_client.patch(
        f"/bank-accounts/{id}/", 
        json=update_payload,
        headers=headers
    )
    assert response.status_code == 200
    result = response.json()
    result["account_number"] == update_payload["account_number"]

    #------------------------------
    # Upload with guest details
    #------------------------------
    response = await httpx_client.patch(
        f"/bank-accounts/{id}/", 
        json=update_payload,
        headers=guest_headers
    )
    assert response.status_code == 403

    #------------------------------
    # delete with guest details
    #------------------------------
    response = await httpx_client.delete(
        f"/bank-accounts/{id}/", 
        headers=guest_headers
    )
    assert response.status_code == 403

    #------------------------------
    # delete with host details
    #------------------------------
    response = await httpx_client.delete(
        f"/bank-accounts/{id}/", 
        headers=headers
    )
    assert response.status_code == 204
    assert not await test_db.get(BankAccount, id)