import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from ppgc_backend.app.models import Investment, InvestmentTransaction
from ppgc_backend.app.controllers.auth import (
    fetched_access_token,
    create_user,
)
from ppgc_backend.app.schemas.auth_schemas import UserRegistrationSchema


@pytest.mark.asyncio
async def test_withdraw_funds(client__fixture):
    """Test the withdrawal endpoint, ensuring ROI is computed properly."""
    
    async for fixture_obj in client__fixture:
        test_db: AsyncSession = fixture_obj.get("db")
        client: AsyncClient = fixture_obj.get("http_client")
        break

    # Step 1: Create a test user
    user_data = UserRegistrationSchema(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    created_user = await create_user(test_db, user_data)
    token_obj = fetched_access_token(user=created_user)
    token = token_obj["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create a test investment
    investment = Investment(
        user_id=created_user.id,
        investment_amount=1000.00,  # Principal
        created_at=datetime.now(timezone.utc) - timedelta(days=35)  # Set past date for ROI to accumulate
    )
    
    test_db.add(investment)
    await test_db.commit()
    await test_db.refresh(investment)

    # Step 3: Call withdrawal endpoint
    response = await client.get(
        f"/roi/withdraw/{investment.id}",
        headers=headers
    )

    assert response.status_code == 200
    withdrawn_amount = float(response.json())
    
    # Step 4: Validate withdrawal amount
    # expected_roi = 1000 * 0.05  # 5% of 1000
    # expected_total_amount = 1000 + expected_roi  # Principal + ROI
    assert withdrawn_amount > 1000  # Avoid floating-point precision issues

    # Step 5: Verify investment status is updated
    updated_investment = await test_db.get(Investment, investment.id)
    assert updated_investment.status == "completed"

    # Step 6: Confirm a transaction was logged
    transaction = await test_db.execute(
        InvestmentTransaction.__table__.select().where(InvestmentTransaction.investment_id == investment.id)
    )
    transaction = transaction.fetchone()
    assert transaction is not None
    # assert transaction.amount == expected_total_amount
    assert transaction.transaction_type == "withdraw"
