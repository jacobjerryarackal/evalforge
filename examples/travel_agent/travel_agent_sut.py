import logging
import re
import time
from typing import Any

from examples.travel_agent.services import (
    AttractionsService,
    BookingPolicyService,
    CurrencyService,
    FlightService,
    HotelService,
    UserProfileService,
    WeatherService,
)
from src.domain.entities.trajectory import Step, ToolCall, Trajectory
from src.domain.interfaces.sut import AgentSUT
from src.domain.value_objects import Cost, Latency, TokenUsage

logger = logging.getLogger("evaluation.infrastructure.mock_sut.travel_agent_sut")


class TravelAgentSUT(AgentSUT):
    """A mock Travel Agent SUT exposing travel services through tool calls."""

    def __init__(
        self,
        flight_service: FlightService | None = None,
        hotel_service: HotelService | None = None,
        weather_service: WeatherService | None = None,
        currency_service: CurrencyService | None = None,
        attractions_service: AttractionsService | None = None,
        booking_policy_service: BookingPolicyService | None = None,
        user_profile_service: UserProfileService | None = None,
        agent_version: str = "v1.2.0",
    ):
        self._flight_service = flight_service or FlightService()
        self._hotel_service = hotel_service or HotelService()
        self._weather_service = weather_service or WeatherService()
        self._currency_service = currency_service or CurrencyService()
        self._attractions_service = attractions_service or AttractionsService()
        self._booking_policy_service = booking_policy_service or BookingPolicyService()
        self._user_profile_service = user_profile_service or UserProfileService()
        self._version = agent_version

    @property
    def version(self) -> str:
        return self._version

    def _calculate_step_metrics(
        self, prompt_len: int, completion_len: int, duration_sec: float
    ) -> tuple[TokenUsage, Cost, Latency]:
        """Simulates token counts and costs based on input and output lengths."""
        # Assume roughly 4 characters per token
        prompt_tokens = max(10, prompt_len // 4)
        completion_tokens = max(10, completion_len // 4)
        total_tokens = prompt_tokens + completion_tokens
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        # Standard pricing: e.g. $0.015 per 1k input tokens, $0.03 per 1k output tokens
        input_cost = (prompt_tokens / 1000) * 0.015
        output_cost = (completion_tokens / 1000) * 0.03
        cost = Cost(amount=round(input_cost + output_cost, 6), currency="USD")

        latency = Latency(seconds=duration_sec)
        return token_usage, cost, latency

    async def run(self, input_query: str) -> Trajectory:
        """Parses query, determines a plan, invokes tools, and builds trajectory."""
        logger.info(f"TravelAgentSUT running query: {input_query}")
        trajectory = Trajectory()
        query_lower = input_query.lower()

        # Extract values using simple regex pattern matchings
        user_id_match = re.search(r"user\s*id\s*([a-zA-Z0-9]+)", query_lower)
        user_id = user_id_match.group(1).upper() if user_id_match else "U101"

        # ---------------------------------------------------------
        # Scenario 1: Booking Flow (Flights + Hotels + Policy validation)
        # ---------------------------------------------------------
        if "flight" in query_lower or "hotel" in query_lower or "book" in query_lower:
            # Parse parameters
            origin = "JFK"
            if "from jfk" in query_lower:
                origin = "JFK"
            elif "from lhr" in query_lower:
                origin = "LHR"
            elif "from cdg" in query_lower:
                origin = "CDG"

            destination = "LAX"
            if "to lax" in query_lower:
                destination = "LAX"
            elif "to cdg" in query_lower:
                destination = "CDG"
            elif "to hnd" in query_lower:
                destination = "HND"

            date = "2026-08-01"
            date_match = re.search(r"on\s*(\d{4}-\d{2}-\d{2})", query_lower)
            if date_match:
                date = date_match.group(1)

            # Step 1: User Profile Retrieval
            start_time = time.perf_counter()
            profile = self._user_profile_service.get_profile(user_id)
            duration = time.perf_counter() - start_time
            thought = (
                f"Received request to book travel. First I will fetch the profile "
                f"for user {user_id} to check budgets and preferences."
            )
            tool_call = ToolCall(
                tool_name="get_profile", arguments={"user_id": user_id}, success=profile is not None
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                len(input_query) + 20, len(str(profile)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=1,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation=profile or {"error": "User profile not found"},
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 2: Flight Search
            start_time = time.perf_counter()
            flights = self._flight_service.search_flights(origin, destination, date)
            duration = time.perf_counter() - start_time
            thought = (
                f"User profile loaded. Searching for flights "
                f"from {origin} to {destination} on {date}."
            )
            tool_call = ToolCall(
                tool_name="search_flights",
                arguments={"origin": origin, "destination": destination, "date": date},
                success=True,
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                100, len(str(flights)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=2,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation={"flights": flights},
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 3: Hotel Search
            start_time = time.perf_counter()
            hotels = self._hotel_service.search_hotels(destination)
            duration = time.perf_counter() - start_time
            thought = (
                f"Flights fetched. Now searching for hotels in the destination city {destination}."
            )
            tool_call = ToolCall(
                tool_name="search_hotels", arguments={"city": destination}, success=True
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                100, len(str(hotels)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=3,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation={"hotels": hotels},
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Select flight and hotel
            selected_flight: dict[str, Any] = (
                flights[0]
                if flights
                else {
                    "price": 1000.0,
                    "flight_number": "UNK",
                    "cabin_class": "Economy",
                    "duration_hours": 2.0,
                }
            )
            selected_hotel: dict[str, Any] = (
                hotels[0] if hotels else {"price_per_night": 200.0, "name": "UNK"}
            )

            # Overrides based on query preferences
            # Business cabin check
            cabin_class = "Economy"
            if "business" in query_lower:
                cabin_class = "Business"
                # Select business flight if available
                business_flights = [f for f in flights if f.get("cabin_class") == "Business"]
                if business_flights:
                    selected_flight = business_flights[0]
                    cabin_class = "Business"

            # Step 4: Policy Check
            start_time = time.perf_counter()
            policy_check = self._booking_policy_service.validate_booking(
                flight_price=float(selected_flight["price"]),
                hotel_price_per_night=float(selected_hotel["price_per_night"]),
                cabin_class=cabin_class,
                flight_duration_hours=float(selected_flight.get("duration_hours", 2.0)),
            )
            duration = time.perf_counter() - start_time
            thought = "Validating travel booking combination against corporate policy constraints."
            tool_call = ToolCall(
                tool_name="validate_booking",
                arguments={
                    "flight_price": selected_flight["price"],
                    "hotel_price_per_night": selected_hotel["price_per_night"],
                    "cabin_class": cabin_class,
                    "flight_duration_hours": selected_flight.get("duration_hours", 2.0),
                },
                success=True,
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                120, len(str(policy_check)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=4,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation=policy_check,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 5: Final Response
            start_time = time.perf_counter()
            if policy_check["approved"]:
                resp = (
                    f"Planned trip successfully. Flight {selected_flight['flight_number']} "
                    f"({selected_flight['cabin_class']}) costing ${selected_flight['price']} and "
                    f"hotel {selected_hotel['name']} at "
                    f"${selected_hotel['price_per_night']}/night. "
                    f"Approved under guidelines."
                )
            else:
                reasons = ", ".join(policy_check["reasons"])
                resp = (
                    f"Booking violates travel guidelines: {reasons}. "
                    f"Please revise your selections."
                )

            duration = time.perf_counter() - start_time
            thought = "Generating the final itinerary recommendations response for the traveler."
            token_usage, cost, latency = self._calculate_step_metrics(100, len(resp) + 30, duration)

            trajectory.add_step(
                Step(
                    step_number=5,
                    thought=thought,
                    response=resp,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

        # ---------------------------------------------------------
        # Scenario 2: Weather Info Flow
        # ---------------------------------------------------------
        elif "weather" in query_lower or "forecast" in query_lower:
            city = "LAX"
            if "lax" in query_lower:
                city = "LAX"
            elif "paris" in query_lower or "cdg" in query_lower:
                city = "CDG"
            elif "tokyo" in query_lower or "hnd" in query_lower:
                city = "HND"
            elif "london" in query_lower or "lhr" in query_lower:
                city = "LHR"

            date = "2026-08-01"
            date_match = re.search(r"on\s*(\d{4}-\d{2}-\d{2})", query_lower)
            if date_match:
                date = date_match.group(1)

            start_time = time.perf_counter()
            weather = self._weather_service.get_weather(city, date)
            duration = time.perf_counter() - start_time
            thought = f"Fetching weather information for {city} on {date}."
            tool_call = ToolCall(
                tool_name="get_weather", arguments={"city": city, "date": date}, success=True
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                100, len(str(weather)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=1,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation=weather,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 2: Response
            start_time = time.perf_counter()
            resp = (
                f"The weather forecast for {city} on {date} is {weather['condition']} "
                f"with {weather['temp_c']}°C and rain probability {weather['rain_prob'] * 100}%."
            )
            duration = time.perf_counter() - start_time
            thought = "Synthesizing weather data and generating response."
            token_usage, cost, latency = self._calculate_step_metrics(100, len(resp) + 30, duration)

            trajectory.add_step(
                Step(
                    step_number=2,
                    thought=thought,
                    response=resp,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

        # ---------------------------------------------------------
        # Scenario 3: Currency Exchange Flow
        # ---------------------------------------------------------
        elif "convert" in query_lower or "currency" in query_lower or "exchange" in query_lower:
            amount = 100.0
            amount_match = re.search(r"(\d+(\.\d+)?)", query_lower)
            if amount_match:
                amount = float(amount_match.group(1))

            from_curr = "EUR"
            if "eur" in query_lower:
                from_curr = "EUR"
            elif "gbp" in query_lower:
                from_curr = "GBP"
            elif "jpy" in query_lower:
                from_curr = "JPY"
            elif "usd" in query_lower:
                from_curr = "USD"

            to_curr = "USD"
            if "to usd" in query_lower:
                to_curr = "USD"
            elif "to eur" in query_lower:
                to_curr = "EUR"
            elif "to gbp" in query_lower:
                to_curr = "GBP"
            elif "to jpy" in query_lower:
                to_curr = "JPY"

            start_time = time.perf_counter()
            converted = self._currency_service.convert_currency(amount, from_curr, to_curr)
            duration = time.perf_counter() - start_time
            thought = f"Performing currency conversion for {amount} {from_curr} to {to_curr}."
            tool_call = ToolCall(
                tool_name="convert_currency",
                arguments={"amount": amount, "from_currency": from_curr, "to_currency": to_curr},
                success=True,
            )
            token_usage, cost, latency = self._calculate_step_metrics(100, 30, duration)

            trajectory.add_step(
                Step(
                    step_number=1,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation={"converted_amount": converted, "currency": to_curr},
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 2: Response
            start_time = time.perf_counter()
            resp = (
                f"The converted amount is {converted} {to_curr} "
                f"for the initial {amount} {from_curr}."
            )
            duration = time.perf_counter() - start_time
            thought = "Completed conversion logic. Formulating response."
            token_usage, cost, latency = self._calculate_step_metrics(100, len(resp) + 30, duration)

            trajectory.add_step(
                Step(
                    step_number=2,
                    thought=thought,
                    response=resp,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

        # ---------------------------------------------------------
        # Scenario 4: Attractions Flow
        # ---------------------------------------------------------
        elif "attraction" in query_lower or "visit" in query_lower or "sightseeing" in query_lower:
            city = "LAX"
            if "lax" in query_lower or "los angeles" in query_lower:
                city = "LAX"
            elif "paris" in query_lower or "cdg" in query_lower:
                city = "CDG"
            elif "tokyo" in query_lower or "hnd" in query_lower:
                city = "HND"

            start_time = time.perf_counter()
            attractions = self._attractions_service.get_attractions(city)
            duration = time.perf_counter() - start_time
            thought = f"Retrieving local attractions list for {city}."
            tool_call = ToolCall(
                tool_name="get_attractions", arguments={"city": city}, success=True
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                100, len(str(attractions)) + 30, duration
            )

            trajectory.add_step(
                Step(
                    step_number=1,
                    thought=thought,
                    tool_calls=[tool_call],
                    observation={"attractions": attractions},
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

            # Step 2: Response
            start_time = time.perf_counter()
            names = [a["name"] for a in attractions]
            resp = f"Top attractions to visit in {city} include: " + ", ".join(names)
            duration = time.perf_counter() - start_time
            thought = "Synthesizing list of tourist attractions."
            token_usage, cost, latency = self._calculate_step_metrics(100, len(resp) + 30, duration)

            trajectory.add_step(
                Step(
                    step_number=2,
                    thought=thought,
                    response=resp,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

        # ---------------------------------------------------------
        # Fallback Scenario (Unknown request type)
        # ---------------------------------------------------------
        else:
            start_time = time.perf_counter()
            resp = (
                "I cannot identify the travel category for your query. "
                "How can I assist you with flights, hotels, weather, attractions, or exchange?"
            )
            duration = time.perf_counter() - start_time
            thought = (
                "Query does not match travel categories. "
                "Generating standard fallback help response."
            )
            token_usage, cost, latency = self._calculate_step_metrics(
                len(input_query), len(resp), duration
            )

            trajectory.add_step(
                Step(
                    step_number=1,
                    thought=thought,
                    response=resp,
                    token_usage=token_usage,
                    cost=cost,
                    latency=latency,
                )
            )

        logger.info(f"TravelAgentSUT execution completed. Steps: {len(trajectory.steps)}")
        return trajectory
