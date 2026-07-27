import uuid
from datetime import datetime

from pydantic import BaseModel


class ManufacturerOut(BaseModel):
    """Manufacturer response."""

    id: uuid.UUID
    name: str
    product_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
