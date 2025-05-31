from geopy.distance import geodesic
from app.core.config import settings

def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the distance in meters between two GPS coordinates.
    """
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return geodesic(point1, point2).meters

def is_within_school_area(veli_latitude: float, veli_longitude: float) -> bool:
    """
    Checks if the parent's location is within the defined maximum distance from the school.
    Uses school coordinates and max distance from settings.
    """
    if not veli_latitude or not veli_longitude:
        return False # Konum bilgisi yoksa okul bölgesinde değil kabul edelim
        
    distance = calculate_distance_meters(
        settings.SCHOOL_LATITUDE, 
        settings.SCHOOL_LONGITUDE, 
        veli_latitude, 
        veli_longitude
    )
    return distance <= settings.MAX_DISTANCE_METERS 