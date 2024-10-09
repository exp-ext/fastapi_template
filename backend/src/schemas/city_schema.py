from pydantic import BaseModel
from typing import Optional


class CityBase(BaseModel):
    name: str
    subject: str
    district: str
    population: int
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class CityCreate(CityBase):
    pass


class CityUpdate(CityBase):
    name: Optional[str] = None
    subject: Optional[str] = None
    district: Optional[str] = None
    population: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
