import pytest

from examples.travel_agent.travel_agent_sut import TravelAgentSUT, normalize_query


@pytest.mark.anyio
async def test_travel_agent_sut_booking_flow():
    agent = TravelAgentSUT()
    
    # Pre-populate golden_cases for test query
    q = "Book a flight from JFK to LAX on 2026-08-01 for user U101 in Economy"
    agent.golden_cases[normalize_query(q)] = {
        "expected_tool_calls": [
            {"service": "UserProfileService", "method": "get_profile", "parameters": {"user_id": "U101"}},
            {"service": "FlightService", "method": "search_flights", "parameters": {"origin": "JFK", "destination": "LAX", "date": "2026-08-01"}},
            {"service": "HotelService", "method": "search_hotels", "parameters": {"city": "LAX"}},
            {"service": "BookingPolicyService", "method": "validate_booking", "parameters": {"flight_price": 250.0, "hotel_price_per_night": 120.0, "cabin_class": "Economy", "flight_duration_hours": 6.0}}
        ],
        "expected_answer": "Flight UA100 and Hotel LA Cozy Inn booked successfully.",
        "retrieved_context": "Mock retrieved context for booking flow"
    }

    trajectory = await agent.run(q)

    assert len(trajectory.steps) == 5
    assert trajectory.final_response is not None
    assert "UA100" in trajectory.final_response
    assert "LA Cozy Inn" in trajectory.final_response

    # Verify tool calls are recorded
    tool_calls = trajectory.all_tool_calls
    assert len(tool_calls) == 4
    tool_names = [tc.tool_name for tc in tool_calls]
    assert "get_profile" in tool_names
    assert "search_flights" in tool_names
    assert "search_hotels" in tool_names
    assert "validate_booking" in tool_names

    # Check metrics are aggregated
    assert trajectory.total_token_usage.total_tokens > 0
    assert trajectory.total_cost.amount > 0
    assert trajectory.total_latency.seconds >= 0


@pytest.mark.anyio
async def test_travel_agent_sut_booking_policy_violation():
    agent = TravelAgentSUT()
    
    # Pre-populate golden_cases for test query
    q = "Book a business flight from JFK to LAX on 2026-08-01 for user U101"
    agent.golden_cases[normalize_query(q)] = {
        "expected_tool_calls": [
            {"service": "UserProfileService", "method": "get_profile", "parameters": {"user_id": "U101"}},
            {"service": "FlightService", "method": "search_flights", "parameters": {"origin": "JFK", "destination": "LAX", "date": "2026-08-01"}},
            {"service": "HotelService", "method": "search_hotels", "parameters": {"city": "LAX"}},
            {"service": "BookingPolicyService", "method": "validate_booking", "parameters": {"flight_price": 850.0, "hotel_price_per_night": 120.0, "cabin_class": "Business", "flight_duration_hours": 6.0}}
        ],
        "expected_answer": "Booking violates travel guidelines (Business class not allowed for flights under 6 hours).",
        "retrieved_context": "Mock retrieved context for policy violation"
    }

    trajectory = await agent.run(q)

    assert len(trajectory.steps) == 5
    assert trajectory.final_response is not None
    assert "violates travel guidelines" in trajectory.final_response


@pytest.mark.anyio
async def test_travel_agent_sut_weather():
    agent = TravelAgentSUT()
    
    # Pre-populate golden_cases for test query
    q = "What is the weather forecast for Paris on 2026-08-05?"
    agent.golden_cases[normalize_query(q)] = {
        "expected_tool_calls": [
            {"service": "WeatherService", "method": "get_weather", "parameters": {"city": "Paris", "date": "2026-08-05"}}
        ],
        "expected_answer": "The weather forecast for Paris on 2026-08-05 is Partly Cloudy with a high of 24 degrees.",
        "retrieved_context": "Mock weather context"
    }

    trajectory = await agent.run(q)

    assert len(trajectory.steps) == 2
    assert trajectory.final_response is not None
    assert "Partly Cloudy" in trajectory.final_response
    assert "24" in trajectory.final_response

    tool_calls = trajectory.all_tool_calls
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "get_weather"


@pytest.mark.anyio
async def test_travel_agent_sut_currency():
    agent = TravelAgentSUT()
    
    # Pre-populate golden_cases for test query
    q = "Convert 200 EUR to USD"
    agent.golden_cases[normalize_query(q)] = {
        "expected_tool_calls": [
            {"service": "CurrencyService", "method": "convert_currency", "parameters": {"amount": 200.0, "from_currency": "EUR", "to_currency": "USD"}}
        ],
        "expected_answer": "The converted amount is 217.39 USD.",
        "retrieved_context": "Mock currency context"
    }

    trajectory = await agent.run(q)

    assert len(trajectory.steps) == 2
    assert trajectory.final_response is not None
    assert "217.39" in trajectory.final_response  # 200 / 0.92 = 217.39

    tool_calls = trajectory.all_tool_calls
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "convert_currency"


@pytest.mark.anyio
async def test_travel_agent_sut_attractions():
    agent = TravelAgentSUT()
    
    # Pre-populate golden_cases for test query
    q = "What attractions can I visit in CDG?"
    agent.golden_cases[normalize_query(q)] = {
        "expected_tool_calls": [
            {"service": "AttractionsService", "method": "get_attractions", "parameters": {"city": "CDG"}}
        ],
        "expected_answer": "In CDG, you can visit the Eiffel Tower.",
        "retrieved_context": "Mock attractions context"
    }

    trajectory = await agent.run(q)

    assert len(trajectory.steps) == 2
    assert trajectory.final_response is not None
    assert "Eiffel Tower" in trajectory.final_response

    tool_calls = trajectory.all_tool_calls
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "get_attractions"


@pytest.mark.anyio
async def test_travel_agent_sut_fallback():
    agent = TravelAgentSUT()
    trajectory = await agent.run("Hello there, how are you?")

    assert len(trajectory.steps) == 1
    assert trajectory.final_response is not None
    assert "I have processed your request" in trajectory.final_response
    assert len(trajectory.all_tool_calls) == 0
