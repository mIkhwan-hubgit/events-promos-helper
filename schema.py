from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Channel(str, Enum):
    in_store = "in_store"
    online = "online"
    both = "both"


class Promo(BaseModel):
    title: str
    details: Optional[str]      # discount or short description
    start_date: Optional[str]   # YYYY-MM-DD
    end_date: Optional[str]     # YYYY-MM-DD
    location: Optional[str]
    channel: Optional[Channel]  # only these three values, or null
    link: Optional[str]         # link to this specific promo, if given