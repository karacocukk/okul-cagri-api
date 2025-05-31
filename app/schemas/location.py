from pydantic import BaseModel, Field
from typing import Optional

class LocationConfig(BaseModel):
    """
    Okul konumu ve maksimum mesafe bilgisini içeren şema.
    Bu bilgiler mobil uygulamanın öğrenci çağırma özelliği için kullanılır.
    """
    school_latitude: float = Field(..., description="Okulun enlem koordinatı")
    school_longitude: float = Field(..., description="Okulun boylam koordinatı")
    max_distance_meters: int = Field(..., description="Maksimum uzaklık (metre cinsinden)")

    class Config:
        json_schema_extra = {
            "example": {
                "school_latitude": 41.0082,
                "school_longitude": 28.9784,
                "max_distance_meters": 200
            }
        } 