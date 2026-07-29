import pytest

from examples.travel_agent.travel_agent_sut import TravelAgentSUT


@pytest.mark.anyio
async def test_travel_agent_sut_booking_flow():
    agent = TravelAgentSUT()
    trajectory = await agent.run(
        "Book a flight from JFK to LAX on 2026-08-01 for user U101 in Economy"
    )

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
    # Booking business class on a short flight (6 hours) violates policy
    trajectory = await agent.run(
        "Book a business flight from JFK to LAX on 2026-08-01 for user U101"
    )

    assert len(trajectory.steps) == 5
    assert trajectory.final_response is not None
    assert "violates travel guidelines" in trajectory.final_response


@pytest.mark.anyio
async def test_travel_agent_sut_weather():
    agent = TravelAgentSUT()
    trajectory = await agent.run("What is the weather forecast for Paris on 2026-08-05?")

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
    trajectory = await agent.run("Convert 200 EUR to USD")

    assert len(trajectory.steps) == 2
    assert trajectory.final_response is not None
    assert "217.39" in trajectory.final_response  # 200 / 0.92 = 217.39

    tool_calls = trajectory.all_tool_calls
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "convert_currency"


@pytest.mark.anyio
async def test_travel_agent_sut_attractions():
    agent = TravelAgentSUT()
    trajectory = await agent.run("What attractions can I visit in CDG?")

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
    assert "cannot identify the travel category" in trajectory.final_response
    assert len(trajectory.all_tool_calls) == 0
