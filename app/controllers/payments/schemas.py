from pydantic import BaseModel


class PaymentRequestSchema(BaseModel):
    amount: float
    name: str
    email: str | None = None
    phone: str | None = None


class WebhookPayload(BaseModel):
    payload: dict
