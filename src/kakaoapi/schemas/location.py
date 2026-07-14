# pknu_summerboard/src/kakaoapi/schemas/location.py
from pydantic import BaseModel

class UserLocation(BaseModel):
    longitude: float
    latitude: float