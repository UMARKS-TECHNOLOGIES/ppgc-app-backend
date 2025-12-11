"""
Test suite for the savings endpoints.
Tests for creating and retrieving daily savings with various period filters.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta

from ppgc_backend.app.models import User
from ppgc_backend.app.controllers.savings.models import DailySavings
from ppgc_backend.app.controllers.auth.services import (
    create_user,
    fetch_access_token,
)
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema


async def create_test_user(
    db: AsyncSession,
    email: str = "test_user@example.com",
    first_name: str = "Test",
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
async def test_create_daily_saving(client_fixture):
    """Test creating a new daily saving"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create a test user
    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a daily saving
    saving_data = {
        "name": "Monthly Savings",
        "amount": 500.0
    }

    response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )

    assert response.status_code == 201
    json_response = response.json()
    assert json_response['name'] == "Monthly Savings"
    assert json_response['amount'] == 500.0
    assert json_response['user_id'] == user.id
    assert 'id' in json_response
    assert 'created_at' in json_response


@pytest.mark.asyncio
async def test_create_multiple_daily_savings(client_fixture):
    """Test creating multiple daily savings"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create multiple savings
    savings_list = [
        {"name": "Week 1 Savings", "amount": 100.0},
        {"name": "Week 2 Savings", "amount": 150.0},
        {"name": "Week 3 Savings", "amount": 200.0},
    ]

    for saving_data in savings_list:
        response = await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )
        assert response.status_code == 201
        json_response = response.json()
        assert json_response['amount'] == saving_data['amount']


@pytest.mark.asyncio
async def test_get_savings_this_week(client_fixture):
    """Test retrieving savings for this week"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a saving for this week
    saving_data = {
        "name": "This Week Saving",
        "amount": 250.0
    }

    create_response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )
    assert create_response.status_code == 201

    # Retrieve savings for this week
    response = await httpx_client.get(
        "/savings/period?period=this_week",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_week"
    assert json_response['total_amount'] == 250.0
    assert json_response['transaction_count'] == 1
    assert len(json_response['transactions']) == 1
    assert json_response['transactions'][0]['amount'] == 250.0


@pytest.mark.asyncio
async def test_get_savings_this_month(client_fixture):
    """Test retrieving savings for this month"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create multiple savings
    savings_list = [
        {"name": "Saving 1", "amount": 100.0},
        {"name": "Saving 2", "amount": 200.0},
        {"name": "Saving 3", "amount": 150.0},
    ]

    for saving_data in savings_list:
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve savings for this month
    response = await httpx_client.get(
        "/savings/period?period=this_month",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_month"
    assert json_response['total_amount'] == 450.0
    assert json_response['transaction_count'] == 3
    assert len(json_response['transactions']) == 3


@pytest.mark.asyncio
async def test_get_savings_this_year(client_fixture):
    """Test retrieving savings for this year"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create savings
    for i in range(5):
        saving_data = {
            "name": f"Saving {i+1}",
            "amount": float((i+1) * 100)
        }
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve savings for this year
    response = await httpx_client.get(
        "/savings/period?period=this_year",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_year"
    assert json_response['transaction_count'] == 5
    assert json_response['total_amount'] == 1500.0  # 100 + 200 + 300 + 400 + 500


@pytest.mark.asyncio
async def test_get_savings_last_six_months(client_fixture):
    """Test retrieving savings for the last six months"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create savings
    saving_data = {
        "name": "Last 6 Months Saving",
        "amount": 750.0
    }

    await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )

    # Retrieve savings for last 6 months
    response = await httpx_client.get(
        "/savings/period?period=last_six_months",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "last_six_months"
    assert json_response['total_amount'] == 750.0
    assert json_response['transaction_count'] == 1


@pytest.mark.asyncio
async def test_get_all_savings_with_pagination(client_fixture):
    """Test retrieving all savings with pagination"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create 10 savings
    for i in range(10):
        saving_data = {
            "name": f"Saving {i+1}",
            "amount": float((i+1) * 50)
        }
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve all savings with limit
    response = await httpx_client.get(
        "/savings/all?limit=5&offset=0",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 5
    assert json_response[0]['amount'] == 500.0  # Most recent (10 * 50)

    # Retrieve next page
    response = await httpx_client.get(
        "/savings/all?limit=5&offset=5",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 5
    assert json_response[0]['amount'] == 250.0  # (5 * 50)


@pytest.mark.asyncio
async def test_invalid_period(client_fixture):
    """Test retrieving savings with invalid period"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try with invalid period
    response = await httpx_client.get(
        "/savings/period?period=invalid_period",
        headers=headers
    )

    assert response.status_code == 400
    json_response = response.json()
    assert "Invalid period" in json_response['detail']


@pytest.mark.asyncio
async def test_empty_savings_list(client_fixture):
    """Test retrieving savings when no records exist"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Retrieve savings without creating any
    response = await httpx_client.get(
        "/savings/period?period=this_week",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_week"
    assert json_response['total_amount'] == 0.0
    assert json_response['transaction_count'] == 0
    assert len(json_response['transactions']) == 0


@pytest.mark.asyncio
async def test_unauthorized_access(client_fixture):
    """Test accessing savings endpoints without authentication"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Try to access without token
    saving_data = {
        "name": "Unauthorized Saving",
        "amount": 100.0
    }

    response = await httpx_client.post(
        "/savings/create",
        json=saving_data
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_isolation(client_fixture):
    """Test that users can only see their own savings"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create two users
    user1 = await create_test_user(test_db, email="user1@example.com")
    user2 = await create_test_user(test_db, email="user2@example.com")

    token1 = fetch_access_token(user=user1)['access_token']
    token2 = fetch_access_token(user=user2)['access_token']
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates savings
    saving_data = {
        "name": "User 1 Saving",
        "amount": 100.0
    }

    await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers1
    )

    # User 2 creates savings
    saving_data2 = {
        "name": "User 2 Saving",
        "amount": 200.0
    }

    await httpx_client.post(
        "/savings/create",
        json=saving_data2,
        headers=headers2
    )

    # User 1 retrieves their savings
    response1 = await httpx_client.get(
        "/savings/period?period=this_month",
        headers=headers1
    )

    assert response1.status_code == 200
    json_response1 = response1.json()
    assert json_response1['total_amount'] == 100.0
    assert json_response1['transaction_count'] == 1

    # User 2 retrieves their savings
    response2 = await httpx_client.get(
        "/savings/period?period=this_month",
        headers=headers2
    )

    assert response2.status_code == 200
    json_response2 = response2.json()
    assert json_response2['total_amount'] == 200.0
    assert json_response2['transaction_count'] == 1


@pytest.mark.asyncio
async def test_create_saving_with_decimal_amount(client_fixture):
    """Test creating savings with decimal amounts"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create saving with decimal amount
    saving_data = {
        "name": "Decimal Saving",
        "amount": 123.45
    }

    response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )

    assert response.status_code == 201
    json_response = response.json()
    assert json_response['amount'] == 123.45


@pytest.mark.asyncio
async def test_create_saving_with_zero_amount(client_fixture):
    """Test creating savings with zero amount (edge case)"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create saving with zero amount
    saving_data = {
        "name": "Zero Saving",
        "amount": 0.0
    }

    response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )

    # Should still succeed
    assert response.status_code == 201
    json_response = response.json()
    assert json_response['amount'] == 0.0


@pytest.mark.asyncio
async def test_pagination_with_large_offset(client_fixture):
    """Test pagination with offset larger than total records"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create 5 savings
    for i in range(5):
        saving_data = {
            "name": f"Saving {i+1}",
            "amount": float((i+1) * 100)
        }
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve with large offset
    response = await httpx_client.get(
        "/savings/all?limit=10&offset=100",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 0  # Should return empty list
