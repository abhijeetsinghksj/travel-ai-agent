"""
Travel AI Agents - Built with CrewAI
4 specialized agents working together to plan your trip
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from config.llm_config import get_crewai_llm
from tools.calendar_tool import check_calendar_availability, block_calendar
from tools.flight_tool import search_flights, get_iata_code
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
#  CrewAI Tool Wrappers
# ─────────────────────────────────────────────

@tool("Check Google Calendar Availability")
def check_calendar_tool(start_date: str, end_date: str) -> str:
    """
    Check if the user's Google Calendar is free between the given dates.
    Input: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    Returns availability status and any conflicts.
    """
    result = check_calendar_availability(start_date, end_date)
    if result.get("available"):
        return f"✅ Calendar is FREE from {start_date} to {end_date}. No conflicts found."
    elif result.get("available") is False:
        conflicts_text = "\n".join(
            [f"  - {c['summary']} ({c['start']})" for c in result["conflicts"]]
        )
        return f"⚠️ Calendar has {len(result['conflicts'])} conflict(s):\n{conflicts_text}"
    else:
        return f"ℹ️ {result['message']}"


@tool("Block Google Calendar for Travel")
def block_calendar_tool(destination: str, start_date: str, end_date: str, description: str = "") -> str:
    """
    Block the user's Google Calendar for the travel dates.
    Input: destination (city name), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), description (optional)
    Returns confirmation of the calendar event created.
    """
    result = block_calendar(destination, start_date, end_date, description)
    if result["success"]:
        return f"✅ {result['message']}\nEvent link: {result.get('event_link', 'N/A')}"
    else:
        return f"❌ {result['message']}"


@tool("Search Available Flights")
def search_flights_tool(destination: str, departure_date: str, return_date: str = None) -> str:
    """
    Search for available flights to the destination.
    Input: destination (city name), departure_date (YYYY-MM-DD), return_date (YYYY-MM-DD, optional)
    Returns list of available flights with prices.
    """
    home_city = os.getenv("HOME_CITY", "Delhi")
    result = search_flights(
        origin=home_city,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        max_results=5,
    )

    if not result["flights"]:
        return f"No flights found from {home_city} to {destination}."

    output = [f"✈️ Available flights from {home_city} to {destination}:"]
    if result.get("note"):
        output.append(f"ℹ️ Note: {result['note']}\n")

    for i, flight in enumerate(result["flights"], 1):
        price = flight["price"]
        itin = flight["itineraries"][0]
        seg = itin["segments"][0]
        output.append(
            f"\n{i}. {seg['carrier']}{seg['flight_number']} | "
            f"Departs: {seg['departure']} | "
            f"Arrives: {seg['arrival']} | "
            f"Stops: {seg['stops']} | "
            f"Duration: {itin['duration']} | "
            f"Price: {price['currency']} {price['total']}"
        )

    return "\n".join(output)


# ─────────────────────────────────────────────
#  Agent Definitions
# ─────────────────────────────────────────────

def create_agents(llm_config: dict):
    """Create all 4 travel agents."""

    # Agent 1: Travel Input Processor
    input_agent = Agent(
        role="Travel Request Processor",
        goal="Validate and process travel requests, extract destination and date information accurately",
        backstory=(
            "You are an expert travel consultant who specializes in understanding "
            "travel requests. You extract key information like destination, travel dates, "
            "and preferences, then validate them for completeness before passing to other agents."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_config,
    )

    # Agent 2: Calendar Manager
    calendar_agent = Agent(
        role="Calendar Manager",
        goal="Check Google Calendar for conflicts and block travel dates if the user is available",
        backstory=(
            "You are a personal assistant specializing in schedule management. "
            "You check the user's calendar for availability and create travel events "
            "to block the dates. You are thorough about checking conflicts and always "
            "confirm before blocking dates."
        ),
        tools=[check_calendar_tool, block_calendar_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm_config,
    )

    # Agent 3: Itinerary Planner
    itinerary_agent = Agent(
        role="Expert Travel Itinerary Planner",
        goal="Create detailed, day-by-day travel itineraries with local insights and recommendations",
        backstory=(
            "You are a seasoned travel expert with deep knowledge of destinations worldwide. "
            "You create personalized, practical itineraries that balance tourist attractions "
            "with authentic local experiences. You consider travel time, opening hours, "
            "cuisine, culture, and budget to craft memorable trips."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_config,
    )

    # Agent 4: Flight Search Specialist
    flight_agent = Agent(
        role="Flight Search Specialist",
        goal="Find the best available flights for the user's travel dates and summarize options clearly",
        backstory=(
            "You are a flight booking expert who knows how to find the best deals. "
            "You search for available flights, compare prices and timings, and present "
            "clear recommendations based on cost, convenience, and travel time."
        ),
        tools=[search_flights_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm_config,
    )

    return input_agent, calendar_agent, itinerary_agent, flight_agent


# ─────────────────────────────────────────────
#  Task Definitions
# ─────────────────────────────────────────────

def create_tasks(agents, destination: str, start_date: str, end_date: str):
    input_agent, calendar_agent, itinerary_agent, flight_agent = agents

    # Task 1: Validate & process the travel request
    task_validate = Task(
        description=(
            f"Process this travel request:\n"
            f"- Destination: {destination}\n"
            f"- Start Date: {start_date}\n"
            f"- End Date: {end_date}\n\n"
            f"Validate the dates are in the future and make sense. "
            f"Calculate the trip duration in days. "
            f"Identify the destination type (beach, mountain, city, historical, etc.) "
            f"and provide a brief summary of what the user can expect."
        ),
        expected_output=(
            "A structured trip summary with: validated dates, trip duration in days, "
            "destination type, and a 2-3 sentence overview of the destination."
        ),
        agent=input_agent,
    )

    # Task 2: Check calendar & block dates
    task_calendar = Task(
        description=(
            f"Check the user's Google Calendar for availability from {start_date} to {end_date}. "
            f"If the calendar is free (no conflicts), block these dates with a travel event for {destination}. "
            f"If there are conflicts, report them clearly without blocking. "
            f"Use the trip summary from the previous task as the event description."
        ),
        expected_output=(
            "A clear report stating: (1) whether the calendar was checked, "
            "(2) if there are conflicts, (3) whether the dates were blocked or not, "
            "and (4) any relevant event details."
        ),
        agent=calendar_agent,
        context=[task_validate],
    )

    # Task 3: Create itinerary
    trip_days = (
        (lambda d2, d1: (d2 - d1).days + 1)(
            __import__("datetime").datetime.strptime(end_date, "%Y-%m-%d"),
            __import__("datetime").datetime.strptime(start_date, "%Y-%m-%d"),
        )
    )

    task_itinerary = Task(
        description=(
            f"Create a detailed day-by-day itinerary for a {trip_days}-day trip to {destination} "
            f"from {start_date} to {end_date}.\n\n"
            f"Include for each day:\n"
            f"- Morning, afternoon, and evening activities\n"
            f"- Must-see attractions with brief descriptions\n"
            f"- Local food recommendations (breakfast, lunch, dinner spots)\n"
            f"- Practical tips (best time to visit, travel within city, etc.)\n"
            f"- Estimated budget per day in INR\n\n"
            f"Make it authentic, practical and exciting!"
        ),
        expected_output=(
            f"A complete {trip_days}-day itinerary with day-by-day activities, "
            "food recommendations, practical tips, and estimated daily budget in INR."
        ),
        agent=itinerary_agent,
        context=[task_validate],
    )

    # Task 4: Search flights
    task_flights = Task(
        description=(
            f"Search for available flights from the user's home city to {destination}.\n"
            f"- Outbound: {start_date}\n"
            f"- Return: {end_date}\n\n"
            f"Find and present the top flight options showing:\n"
            f"1. Flight details (airline, timing, duration, stops)\n"
            f"2. Price in INR\n"
            f"3. Your top recommendation with reasoning\n"
            f"4. Tips for getting the best deal"
        ),
        expected_output=(
            "A flight search summary with top available options, "
            "prices, and a clear recommendation for the best flight choice."
        ),
        agent=flight_agent,
        context=[task_validate],
    )

    return [task_validate, task_calendar, task_itinerary, task_flights]


# ─────────────────────────────────────────────
#  Main Crew Runner
# ─────────────────────────────────────────────

def run_travel_crew(destination: str, start_date: str, end_date: str) -> dict:
    """
    Run the full Travel AI Crew for a given trip.
    
    Args:
        destination: Travel destination (city/country)
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
    
    Returns:
        dict with results from all agents
    """
    print(f"\n{'='*60}")
    print(f"🚀 TRAVEL AI CREW STARTING")
    print(f"📍 Destination: {destination}")
    print(f"📅 Dates: {start_date} → {end_date}")
    print(f"{'='*60}\n")

    llm_config = get_crewai_llm()
    agents = create_agents(llm_config)
    tasks = create_tasks(agents, destination, start_date, end_date)

    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,  # Tasks run in order
        verbose=True,
    )

    result = crew.kickoff()

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "result": str(result),
        "task_outputs": {
            "validation": str(tasks[0].output) if tasks[0].output else "",
            "calendar": str(tasks[1].output) if tasks[1].output else "",
            "itinerary": str(tasks[2].output) if tasks[2].output else "",
            "flights": str(tasks[3].output) if tasks[3].output else "",
        }
    }


if __name__ == "__main__":
    # Quick test
    result = run_travel_crew(
        destination="Goa",
        start_date="2025-12-20",
        end_date="2025-12-25",
    )
    print("\n\n=== FINAL RESULT ===")
    print(result["result"])
