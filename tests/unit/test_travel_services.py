import pytest

from examples.travel_agent.services import (
    AttractionsService,
    BookingPolicyService,
    CurrencyService,
    FlightService,
    HotelService,
    UserProfileService,
    WeatherService,
)


def test_flight_service():
    service = FlightService()
    results = service.search_flights("JFK", "LAX", "2026-08-01")
    assert len(results) == 2
    assert results[0]["flight_number"] == "UA100"
    assert results[0]["price"] == 250.00
    assert results[1]["flight_number"] == "UA101"
    assert results[1]["cabin_class"] == "Business"

    # Case insensitivity
    results_lower = service.search_flights("jfk", "lax", "2026-08-01")
    assert len(results_lower) == 2

    # Non-matching
    no_results = service.search_flights("JFK", "HND", "2026-08-01")
    assert len(no_results) == 0


def test_hotel_service():
    service = HotelService()
    results = service.search_hotels("LAX")
    assert len(results) == 2

    # Price filter
    cheap_hotels = service.search_hotels("LAX", max_price=150.0)
    assert len(cheap_hotels) == 1
    assert cheap_hotels[0]["name"] == "LA Cozy Inn"

    # Rating filter
    top_hotels = service.search_hotels("LAX", min_rating=4.5)
    assert len(top_hotels) == 1
    assert top_hotels[0]["name"] == "The Beverly Plaza"

    # Amenity filter
    pool_hotels = service.search_hotels("LAX", required_amenity="pool")
    assert len(pool_hotels) == 1
    assert pool_hotels[0]["name"] == "The Beverly Plaza"


def test_weather_service():
    service = WeatherService()
    weather = service.get_weather("LAX", "2026-08-01")
    assert weather["condition"] == "Sunny"
    assert weather["temp_c"] == 28.0

    # Fallback
    fallback = service.get_weather("SFO", "2026-08-01")
    assert fallback["condition"] == "Clear"
    assert fallback["temp_c"] == 22.0


def test_currency_service():
    service = CurrencyService()
    amount_usd = service.convert_currency(100.0, "EUR", "USD")
    # 100 EUR = 100 / 0.92 = 108.70 USD
    assert amount_usd == pytest.approx(108.70, rel=1e-2)

    amount_jpy = service.convert_currency(100.0, "USD", "JPY")
    # 100 USD = 100 * 155.0 = 15500 JPY
    assert amount_jpy == 15500.0

    with pytest.raises(ValueError):
        service.convert_currency(100.0, "XYZ", "USD")


def test_attractions_service():
    service = AttractionsService()
    attractions = service.get_attractions("CDG")
    assert len(attractions) == 3
    names = [a["name"] for a in attractions]
    assert "Eiffel Tower" in names


def test_booking_policy_service():
    service = BookingPolicyService()
    # Good booking
    res = service.validate_booking(
        flight_price=300.0,
        hotel_price_per_night=150.0,
        cabin_class="Economy",
        flight_duration_hours=2.5,
    )
    assert res["approved"] is True
    assert len(res["reasons"]) == 0

    # Violates business class flight duration limit
    res_biz = service.validate_booking(
        flight_price=800.0,
        hotel_price_per_night=150.0,
        cabin_class="Business",
        flight_duration_hours=5.0,
    )
    assert res_biz["approved"] is False
    assert any("Business class cabin not permitted" in r for r in res_biz["reasons"])

    # Violates all policies
    res_fail = service.validate_booking(
        flight_price=1600.0,
        hotel_price_per_night=300.0,
        cabin_class="Business",
        flight_duration_hours=2.0,
    )
    assert res_fail["approved"] is False
    assert len(res_fail["reasons"]) == 3


def test_user_profile_service():
    service = UserProfileService()
    profile = service.get_profile("U101")
    assert profile is not None
    assert profile["name"] == "Alice Smith"
    assert profile["max_flight_budget"] == 500.0

    missing = service.get_profile("U999")
    assert missing is None
