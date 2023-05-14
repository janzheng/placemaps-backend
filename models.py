from pydantic import BaseModel
from typing import List, Optional


class PlaceModel(BaseModel):
  name: str
  location: str
  category: Optional[str]
  description: Optional[str]
  highlights: Optional[List[str]]
  rating: Optional[float]
  external_links: Optional[List[str]] = []
  keywords: Optional[List[str]]


class EventModel(BaseModel):
  name: str
  date: str
  description: str
  location: str
  link: Optional[str]
  time: Optional[str]
  keywords: Optional[List[str]]
