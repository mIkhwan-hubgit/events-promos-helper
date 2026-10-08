from typing import Optional
from pydantic import BaseModel


class Promo(BaseModel):
    title: str
    details: Optional[str]      # discount or short description
    start_date: Optional[str]   # YYYY-MM-DD
    end_date: Optional[str]     # YYYY-MM-DD
    location: Optional[str]
    channel: Optional[str]      # "in_store", "online" or "both"