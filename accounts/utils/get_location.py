import requests


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
