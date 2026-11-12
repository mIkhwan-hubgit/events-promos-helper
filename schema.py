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

class Topic(str, Enum):
    ai = "AI"
    web_mobile = "Web & Mobile"
    cloud_devops = "Cloud & DevOps"
    data = "Data"
    security = "Security"
    design = "Design"
    startup = "Startup"
    other = "Other tech"

class TechPick(BaseModel):
    index: int
    topic: Topic

class EventItem(Promo):
    topic: Optional[str]  # events have a topic; bookstore promos don't
    category: Optional[str]  # set when one source feeds several tabs (e.g. CloudJoi)

class EventKind(str, Enum):
    orchestra = "orchestra"
    workshop = "workshop"

class EventPick(BaseModel):
    index: int
    kind: EventKind