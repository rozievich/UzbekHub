import requests
from geopy.distance import geodesic
from accounts.models import Location


def get_my_location(lat: str, long: str) -> dict:
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={long}&format=json&addressdetails=1"
    headers = {"User-Agent": "MyApp/1.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        address = data['address']
        if address:
            return address
        return None
    return None


def get_nearby_users(user, radius_km=10):
    user_loc = (float(user.location.lat), float(user.location.long))
    nearby = []

    for loc in Location.objects.exclude(owner=user):
        target = (float(loc.lat), float(loc.long))
        distance = geodesic(user_loc, target).km
        if distance <= radius_km:
            loc.owner.distance = round(distance, 2)
            nearby.append(loc.owner)

    return nearby
