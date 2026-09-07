"""Small server-side Google Places API client for company search."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GOOGLE_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.location",
    ]
)


def _api_key():
    return os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()


def _address_component(place, component_type):
    for component in place.get("addressComponents", []):
        if component_type in component.get("types", []):
            return component.get("longText") or component.get("shortText")
    return None


def _parse_place(place):
    display_name = place.get("displayName") or {}
    name = display_name.get("text")
    if not name:
        return None

    location = place.get("location") or {}
    return {
        "name": name,
        "address": place.get("formattedAddress"),
        "street": " ".join(
            value
            for value in [
                _address_component(place, "route"),
                _address_component(place, "street_number"),
            ]
            if value
        ) or None,
        "city": _address_component(place, "locality")
        or _address_component(place, "postal_town"),
        "postcode": _address_component(place, "postal_code"),
        "phone": place.get("nationalPhoneNumber")
        or place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        # Google Places Text Search does not provide company email addresses.
        "email": None,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "google_place_id": place.get("id"),
    }


def search_places(name, city=None):
    """Search Google Places Text Search for a German company."""
    api_key = _api_key()
    if not api_key:
        raise RuntimeError(
            "Google Places ist nicht konfiguriert. "
            "Bitte GOOGLE_PLACES_API_KEY setzen."
        )

    text_query = name.strip()
    if city:
        text_query = f"{text_query}, {city.strip()}, Deutschland"
    else:
        text_query = f"{text_query}, Deutschland"

    request_body = json.dumps(
        {
            "textQuery": text_query,
            "languageCode": "de",
            "regionCode": "DE",
            "pageSize": 20,
        }
    ).encode("utf-8")
    request_object = Request(
        GOOGLE_PLACES_URL,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": GOOGLE_FIELD_MASK,
        },
        method="POST",
    )

    try:
        with urlopen(request_object, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            detail = error.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        raise RuntimeError(
            f"Google Places API HTTP {error.code}"
            + (f": {detail[:300]}" if detail else "")
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Google Places API request failed: {error}") from error

    results = []
    seen_ids = set()
    for place in payload.get("places", []):
        result = _parse_place(place)
        if result and result["google_place_id"] not in seen_ids:
            seen_ids.add(result["google_place_id"])
            results.append(result)
    return results