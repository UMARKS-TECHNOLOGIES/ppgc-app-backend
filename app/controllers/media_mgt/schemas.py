from typing import List
from pydantic import BaseModel, ConfigDict


class UploadResponseItem(BaseModel):
    public_id: str
    secure_url: str

    model_config = ConfigDict(extra="allow")


class DeleteRequest(BaseModel):
    public_ids: List[str]


class DeleteResponse(BaseModel):
    deleted: dict