import pytest
from httpx import AsyncClient
from ppgc_backend.app.models import Investment, InvestmentTransaction
from ppgc_backend.app.controllers.auth import (
    fetched_access_token,
    create_user,
)
from ppgc_backend.app.schemas.auth_schemas import UserRegistrationSchema


@pytest.mark.asyncio
async def test_create_roi(client__fixture):
    async for fixture_obj in client__fixture:
        test_db = fixture_obj.get("db")
        client: AsyncClient = fixture_obj.get("http_client")
        break

    # Step 1: Create a test user
    user_data = UserRegistrationSchema(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    created_user = await create_user(test_db, user_data)

    # Step 2: Generate authentication token
    token_obj = fetched_access_token(user=created_user)
    token = token_obj["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Test deposit without investment_id (should create a new investment)
    deposit_data = {"investment_id": None, "amount": 500.0}
    response = await client.post("/roi/deposit", json=deposit_data, headers=headers)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["investment_amount"] == 500.0
    investment_id = response_json["id"]  # Capture the newly created investment ID

    # Step 4: Validate database records
    investment = await test_db.get(Investment, investment_id)
    assert investment is not None
    assert investment.investment_amount == 500.0

    transaction = await test_db.execute(
        InvestmentTransaction.__table__.select().where(
            InvestmentTransaction.investment_id == investment_id
        )
    )
    transaction = transaction.fetchone()
    assert transaction is not None
    assert transaction.amount == 500.0
    assert transaction.transaction_type == "deposit"

    # Step 5: Test deposit into an existing investment
    deposit_data = {"investment_id": investment_id, "amount": 300.0}
    response = await client.post("/roi/deposit", json=deposit_data, headers=headers)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["investment_amount"] == 800.0  # 500 + 300

    # Validate updated investment balance
    updated_investment = await test_db.get(Investment, investment_id)
    assert updated_investment.investment_amount == 800.0

    # Step 6: Validate transaction history
    transaction = await test_db.execute(
        InvestmentTransaction.__table__.select().where(
            InvestmentTransaction.investment_id == investment_id
        )
    )
    transactions = transaction.fetchall()
    assert len(transactions) == 2  # Two transactions (500 deposit + 300 deposit)

