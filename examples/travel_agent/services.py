import logging
from typing import Any

logger = logging.getLogger("evaluation.infrastructure.travel_simulation.services")


class FlightService:
    """Deterministic simulation of a flight search catalog."""

    def __init__(self) -> None:
        self.flights: list[dict[str, Any]] = [
            # Flights from JFK
            {
                "flight_number": "UA100",
                "origin": "JFK",
                "destination": "LAX",
                "date": "2026-08-01",
                "price": 250.00,
                "cabin_class": "Economy",
                "duration_hours": 6.0,
            },
            {
                "flight_number": "UA101",
                "origin": "JFK",
                "destination": "LAX",
                "date": "2026-08-01",
                "price": 850.00,
                "cabin_class": "Business",
                "duration_hours": 6.0,
            },
            {
                "flight_number": "AF015",
                "origin": "JFK",
                "destination": "CDG",
                "date": "2026-08-05",
                "price": 600.00,
                "cabin_class": "Economy",
                "duration_hours": 7.5,
            },
            {
                "flight_number": "AF016",
                "origin": "JFK",
                "destination": "CDG",
                "date": "2026-08-05",
                "price": 1800.00,
                "cabin_class": "Business",
                "duration_hours": 7.5,
            },
            # Flights from LHR
            {
                "flight_number": "BA200",
                "origin": "LHR",
                "destination": "HND",
                "date": "2026-08-10",
                "price": 950.00,
                "cabin_class": "Economy",
                "duration_hours": 12.0,
            },
            {
                "flight_number": "BA201",
                "origin": "LHR",
                "destination": "HND",
                "date": "2026-08-10",
                "price": 3200.00,
                "cabin_class": "Business",
                "duration_hours": 12.0,
            },
            # Cheap flight for test cases
            {
                "flight_number": "EZ045",
                "origin": "CDG",
                "destination": "LHR",
                "date": "2026-08-15",
                "price": 80.00,
                "cabin_class": "Economy",
                "duration_hours": 1.5,
            },
        ]

    def search_flights(self, origin: str, destination: str, date: str) -> list[dict[str, Any]]:
        """Searches for flights matching origin, destination, and date (case-insensitive)."""
        origin_upper = origin.strip().upper()
        destination_upper = destination.strip().upper()

        results = []
        for flight in self.flights:
            if (
                flight["origin"] == origin_upper
                and flight["destination"] == destination_upper
                and flight["date"] == date
            ):
                results.append(flight.copy())
        logger.debug(
            f"Flight search {origin_upper} -> {destination_upper} on {date}: "
            f"found {len(results)} flights"
        )
        return results


class HotelService:
    """Deterministic simulation of a hotel search database."""

    def __init__(self) -> None:
        self.hotels: list[dict[str, Any]] = [
            {
                "hotel_id": "H-LAX-01",
                "city": "LAX",
                "name": "LA Cozy Inn",
                "price_per_night": 120.00,
                "rating": 4.1,
                "amenities": ["WiFi", "Parking"],
            },
            {
                "hotel_id": "H-LAX-02",
                "city": "LAX",
                "name": "The Beverly Plaza",
                "price_per_night": 350.00,
                "rating": 4.8,
                "amenities": ["WiFi", "Pool", "Gym", "Spa"],
            },
            {
                "hotel_id": "H-CDG-01",
                "city": "CDG",
                "name": "Parisian Boutique Hotel",
                "price_per_night": 220.00,
                "rating": 4.5,
                "amenities": ["WiFi", "Breakfast Included"],
            },
            {
                "hotel_id": "H-CDG-02",
                "city": "CDG",
                "name": "Gare du Nord Hostel",
                "price_per_night": 70.00,
                "rating": 3.7,
                "amenities": ["WiFi"],
            },
            {
                "hotel_id": "H-HND-01",
                "city": "HND",
                "name": "Tokyo Capsule Suites",
                "price_per_night": 55.00,
                "rating": 4.2,
                "amenities": ["WiFi", "Sauna"],
            },
            {
                "hotel_id": "H-HND-02",
                "city": "HND",
                "name": "Shibuya Grand Tower",
                "price_per_night": 400.00,
                "rating": 4.9,
                "amenities": ["WiFi", "Pool", "Gym", "Sky Lounge"],
            },
        ]

    def search_hotels(
        self,
        city: str,
        max_price: float | None = None,
        min_rating: float | None = None,
        required_amenity: str | None = None,
    ) -> list[dict[str, Any]]:
        """Searches for hotels in a city filtering by price, rating, and amenities."""
        city_upper = city.strip().upper()

        results = []
        for hotel in self.hotels:
            if hotel["city"] == city_upper:
                # Filter by max price
                if max_price is not None and hotel["price_per_night"] > max_price:
                    continue
                # Filter by min rating
                if min_rating is not None and hotel["rating"] < min_rating:
                    continue
                # Filter by required amenity
                if required_amenity is not None:
                    amenities_lower = [a.lower() for a in hotel["amenities"]]
                    if required_amenity.lower() not in amenities_lower:
                        continue
                results.append(hotel.copy())

        logger.debug(
            f"Hotel search in {city_upper} "
            f"(max_price={max_price}, min_rating={min_rating}): "
            f"found {len(results)} hotels"
        )
        return results


class WeatherService:
    """Deterministic simulation of weather conditions."""

    def __init__(self) -> None:
        # Default weather forecasts for cities
        self.weather_db = {
            ("LAX", "2026-08-01"): {"condition": "Sunny", "temp_c": 28.0, "rain_prob": 0.0},
            ("LAX", "2026-08-02"): {"condition": "Sunny", "temp_c": 29.5, "rain_prob": 0.0},
            ("CDG", "2026-08-05"): {"condition": "Partly Cloudy", "temp_c": 24.0, "rain_prob": 0.1},
            ("CDG", "2026-08-06"): {"condition": "Rainy", "temp_c": 19.0, "rain_prob": 0.8},
            ("HND", "2026-08-10"): {"condition": "Humid / Sunny", "temp_c": 32.0, "rain_prob": 0.2},
            ("LHR", "2026-08-15"): {"condition": "Overcast", "temp_c": 17.5, "rain_prob": 0.4},
        }

    def get_weather(self, city: str, date: str) -> dict[str, Any]:
        """Gets weather condition for a city and date."""
        city_upper = city.strip().upper()
        key = (city_upper, date)
        if key in self.weather_db:
            return self.weather_db[key].copy()
        # Generic fallback
        return {"condition": "Clear", "temp_c": 22.0, "rain_prob": 0.15}


class CurrencyService:
    """Deterministic simulation of currency exchange rates."""

    def __init__(self) -> None:
        # Base currency is USD
        self.rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.78,
            "JPY": 155.0,
        }

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Converts currency based on static deterministic rates."""
        f_curr = from_currency.strip().upper()
        t_curr = to_currency.strip().upper()

        if f_curr not in self.rates or t_curr not in self.rates:
            raise ValueError(f"Unsupported currency: {f_curr} or {t_curr}")

        # Convert to USD base first, then to target
        amount_usd = amount / self.rates[f_curr]
        target_amount = amount_usd * self.rates[t_curr]
        return round(target_amount, 2)


class AttractionsService:
    """Deterministic simulation of local tourist attractions."""

    def __init__(self) -> None:
        self.attractions = {
            "LAX": [
                {"name": "Griffith Observatory", "ticket_price_usd": 0.0, "rating": 4.7},
                {"name": "Universal Studios Hollywood", "ticket_price_usd": 120.0, "rating": 4.6},
                {"name": "Santa Monica Pier", "ticket_price_usd": 0.0, "rating": 4.5},
            ],
            "CDG": [
                {"name": "Eiffel Tower", "ticket_price_usd": 28.0, "rating": 4.8},
                {"name": "Louvre Museum", "ticket_price_usd": 22.0, "rating": 4.7},
                {"name": "Notre-Dame Cathedral", "ticket_price_usd": 0.0, "rating": 4.6},
            ],
            "HND": [
                {"name": "Senso-ji Temple", "ticket_price_usd": 0.0, "rating": 4.7},
                {"name": "Tokyo Skytree", "ticket_price_usd": 20.0, "rating": 4.6},
                {"name": "Meiji Jingu Shrine", "ticket_price_usd": 0.0, "rating": 4.8},
            ],
        }

    def get_attractions(self, city: str) -> list[dict[str, Any]]:
        """Gets tourist attractions for a specific city."""
        city_upper = city.strip().upper()
        return self.attractions.get(city_upper, []).copy()


class BookingPolicyService:
    """Deterministic policy rules validation for corporate travel booking."""

    def validate_booking(
        self,
        flight_price: float,
        hotel_price_per_night: float,
        cabin_class: str,
        flight_duration_hours: float,
    ) -> dict[str, Any]:
        """Validates booking requests against company booking policy.

        Policy constraints:
        - Flights costing > $1500 are rejected.
        - Hotels costing > $250 per night are rejected.
        - Business class is only permitted for flights with a duration > 7 hours.
        """
        rejections = []

        if flight_price > 1500.00:
            rejections.append(f"Flight price ${flight_price} exceeds limit of $1500")

        if hotel_price_per_night > 250.00:
            rejections.append(f"Hotel rate ${hotel_price_per_night}/night exceeds limit of $250")

        if cabin_class.strip().lower() == "business" and flight_duration_hours <= 7.0:
            rejections.append(
                f"Business class cabin not permitted for flight duration of "
                f"{flight_duration_hours}h (must be > 7h)"
            )

        if rejections:
            return {"approved": False, "reasons": rejections}
        return {"approved": True, "reasons": []}


class UserProfileService:
    """Deterministic simulation of traveler profiles."""

    def __init__(self) -> None:
        self.profiles = {
            "U101": {
                "user_id": "U101",
                "name": "Alice Smith",
                "home_city": "JFK",
                "preferred_airline": "United Airlines",
                "loyalty_member": "UA-99812",
                "max_flight_budget": 500.0,
                "max_hotel_budget": 200.0,
            },
            "U102": {
                "user_id": "U102",
                "name": "Bob Johnson",
                "home_city": "LHR",
                "preferred_airline": "British Airways",
                "loyalty_member": "BA-11202",
                "max_flight_budget": 1000.0,
                "max_hotel_budget": 300.0,
            },
        }

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Fetches traveler profile by ID."""
        profile = self.profiles.get(user_id)
        return profile.copy() if profile else None
