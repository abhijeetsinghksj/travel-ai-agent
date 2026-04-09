"""
Flight Search Tool
Uses Amadeus API (free tier) to search for available flights.
"""
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from amadeus import Client as AmadeusClient, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False
    print("[Warning] Amadeus library not installed. Flight search disabled.")

# IATA code cache for common cities
CITY_TO_IATA = {
    "delhi": "DEL", "new delhi": "DEL",
    "mumbai": "BOM", "bombay": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR",
    "hyderabad": "HYD", "chennai": "MAA",
    "kolkata": "CCU", "pune": "PNQ",
    "goa": "GOI", "ahmedabad": "AMD",
    "jaipur": "JAI", "kochi": "COK",
    "new york": "JFK", "nyc": "JFK",
    "london": "LHR", "paris": "CDG",
    "dubai": "DXB", "singapore": "SIN",
    "bangkok": "BKK", "tokyo": "NRT",
    "bali": "DPS", "sydney": "SYD",
    "toronto": "YYZ", "amsterdam": "AMS",
    "rome": "FCO", "barcelona": "BCN",
    "istanbul": "IST", "zurich": "ZRH",
    "hong kong": "HKG", "kuala lumpur": "KUL",
    "maldives": "MLE", "male": "MLE",
    "colombo": "CMB", "kathmandu": "KTM",
    "phuket": "HKT", "chiang mai": "CNX",
    "lisbon": "LIS", "madrid": "MAD",
    "berlin": "BER", "vienna": "VIE",
    "prague": "PRG", "budapest": "BUD",
}


def get_iata_code(city_name: str) -> Optional[str]:
    """Convert city name to IATA airport code."""
    city_lower = city_name.lower().strip()
    
    # Direct lookup
    if city_lower in CITY_TO_IATA:
        return CITY_TO_IATA[city_lower]
    
    # Check if already an IATA code (3 letters)
    if len(city_lower) == 3 and city_lower.isalpha():
        return city_lower.upper()
    
    # Partial match
    for key, code in CITY_TO_IATA.items():
        if city_lower in key or key in city_lower:
            return code
    
    return None


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    max_results: int = 5,
) -> dict:
    """
    Search for available flights using Amadeus API.
    
    Args:
        origin: Origin city or IATA code
        destination: Destination city or IATA code
        departure_date: YYYY-MM-DD
        return_date: YYYY-MM-DD (optional, for round trip)
        adults: Number of passengers
        max_results: Max number of results to return
    
    Returns:
        dict with flight offers
    """
    if not AMADEUS_AVAILABLE:
        return _mock_flight_data(origin, destination, departure_date, return_date)

    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not client_id or client_id == "your_amadeus_client_id":
        print("[Flight] Amadeus credentials not set. Using mock data.")
        return _mock_flight_data(origin, destination, departure_date, return_date)

    try:
        amadeus = AmadeusClient(
            client_id=client_id,
            client_secret=client_secret,
            hostname=os.getenv("AMADEUS_HOSTNAME", "test"),
        )

        # Resolve IATA codes
        origin_code = get_iata_code(origin) or origin.upper()[:3]
        dest_code = get_iata_code(destination) or destination.upper()[:3]

        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": dest_code,
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results,
            "currencyCode": "INR",
        }

        if return_date:
            params["returnDate"] = return_date

        response = amadeus.shopping.flight_offers_search.get(**params)
        offers = response.data

        flights = []
        for offer in offers[:max_results]:
            itineraries = offer.get("itineraries", [])
            price = offer.get("price", {})

            flight_info = {
                "id": offer.get("id"),
                "price": {
                    "total": price.get("grandTotal"),
                    "currency": price.get("currency", "INR"),
                },
                "itineraries": [],
            }

            for itin in itineraries:
                segments = itin.get("segments", [])
                itin_info = {
                    "duration": itin.get("duration"),
                    "segments": [],
                }
                for seg in segments:
                    dep = seg.get("departure", {})
                    arr = seg.get("arrival", {})
                    itin_info["segments"].append({
                        "carrier": seg.get("carrierCode"),
                        "flight_number": seg.get("number"),
                        "from": dep.get("iataCode"),
                        "to": arr.get("iataCode"),
                        "departure": dep.get("at"),
                        "arrival": arr.get("at"),
                        "duration": seg.get("duration"),
                        "stops": seg.get("numberOfStops", 0),
                    })
                flight_info["itineraries"].append(itin_info)

            flights.append(flight_info)

        return {
            "success": True,
            "origin": origin_code,
            "destination": dest_code,
            "departure_date": departure_date,
            "return_date": return_date,
            "flights": flights,
            "count": len(flights),
        }

    except ResponseError as e:
        return {
            "success": False,
            "message": f"Amadeus API error: {e.response.result}",
            "flights": _mock_flight_data(origin, destination, departure_date, return_date)["flights"],
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Flight search error: {str(e)}",
            "flights": _mock_flight_data(origin, destination, departure_date, return_date)["flights"],
        }


def _mock_flight_data(origin: str, destination: str, departure_date: str, return_date: Optional[str]) -> dict:
    """Returns mock flight data when API is not configured."""
    origin_code = get_iata_code(origin) or origin.upper()[:3]
    dest_code = get_iata_code(destination) or destination.upper()[:3]
    
    return {
        "success": True,
        "note": "Mock data - Configure Amadeus API for real results",
        "origin": origin_code,
        "destination": dest_code,
        "departure_date": departure_date,
        "return_date": return_date,
        "flights": [
            {
                "id": "mock-1",
                "price": {"total": "12500.00", "currency": "INR"},
                "itineraries": [{
                    "duration": "PT2H30M",
                    "segments": [{
                        "carrier": "AI",
                        "flight_number": "101",
                        "from": origin_code,
                        "to": dest_code,
                        "departure": f"{departure_date}T06:00:00",
                        "arrival": f"{departure_date}T08:30:00",
                        "stops": 0,
                    }]
                }]
            },
            {
                "id": "mock-2",
                "price": {"total": "8900.00", "currency": "INR"},
                "itineraries": [{
                    "duration": "PT4H15M",
                    "segments": [{
                        "carrier": "6E",
                        "flight_number": "234",
                        "from": origin_code,
                        "to": dest_code,
                        "departure": f"{departure_date}T10:00:00",
                        "arrival": f"{departure_date}T14:15:00",
                        "stops": 1,
                    }]
                }]
            },
            {
                "id": "mock-3",
                "price": {"total": "15200.00", "currency": "INR"},
                "itineraries": [{
                    "duration": "PT2H15M",
                    "segments": [{
                        "carrier": "UK",
                        "flight_number": "891",
                        "from": origin_code,
                        "to": dest_code,
                        "departure": f"{departure_date}T18:00:00",
                        "arrival": f"{departure_date}T20:15:00",
                        "stops": 0,
                    }]
                }]
            },
        ],
        "count": 3,
    }
