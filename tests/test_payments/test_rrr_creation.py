import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.test_auth import signin_for_access_token
from ppgc_backend.tests.test_auth.test_user_creation import create_test_user, user_data
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.app.controllers.transactions.enums import TRXType
from sqlalchemy.future import select


@pytest.mark.asyncio
async def test_create_rrr_endpoint(client_fixture, monkeypatch):
    test_db: AsyncSession = client_fixture["db"]
    httpx_client: AsyncClient = client_fixture["http_client"]

    # Create user and authenticate
    created_user = await create_test_user(test_db)
    token = await signin_for_access_token(user_data, httpx_client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "amount": 123.45,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "0123456789",
    }

    response = await httpx_client.post(
        "/payments/rrr/",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    json_resp = response.json()
    assert "remita" in json_resp
    assert "transaction" in json_resp
    assert json_resp["transaction"]["trx_id"] == "RRR123"

    # Validate that the transaction was persisted
    from ppgc_backend.app.controllers.transactions.models import Transaction

    query = await test_db.execute(
        select(Transaction).where(Transaction.trx_id == "RRR123")
    )
    trx = query.scalars().first()
    assert trx is not None
    assert trx.trx_type == TRXType.deposit
