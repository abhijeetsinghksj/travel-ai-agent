"""
Travel AI Agents - Built with CrewAI
4 specialized agents working together to plan your trip
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent, Task, Crew, Process
try:
    from crewai import tool
except ImportError:
    try:
        from crewai.tools import tool
    except ImportError:
        from langchain_core.tools import tool
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
        max_iter=25,
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
        max_iter=25,
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
        max_iter=25,
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
        max_iter=25,
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
    description=f"Trip details: Destination={destination}, Start={start_date}, End={end_date}. Calculate duration in days and write a 2-sentence overview of the destination. Do this directly without using any tools.",
    expected_output="Trip duration in days and 2-sentence destination overview.",
    agent=input_agent,
)
    

    # Task 2: Check calendar & block dates
    task_calendar = Task(
    description=f"Use Check_Calendar tool ONCE for dates {start_date} to {end_date}. Then use Block_Calendar tool ONCE to block dates for {destination}. Stop after both tool calls.",
    expected_output="Calendar check result and confirmation of blocked dates.",
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
    description=f"Write a {trip_days}-day itinerary for {destination}. Include 3 activities per day and one food recommendation. Do not use any tools, write directly from your knowledge.",
    expected_output=f"A {trip_days}-day itinerary with activities and food.",
    agent=itinerary_agent,
    context=[task_validate],
)

    # Task 4: Search flights
    task_flights = Task(
    description=f"Use Search_Flights tool ONCE with destination={destination}, departure_date={start_date}. Then immediately write your recommendation based on results. Do not call the tool again.",
    expected_output="Top 3 flight options and one recommendation.",
    agent=flight_agent,
    context=[task_validate],
)

    return [task_validate, task_calendar, task_itinerary, task_flights]


# ─────────────────────────────────────────────
#  Main Crew Runner
# ─────────────────────────────────────────────

def run_travel_crew(destination: str, start_date: str, end_date: str) -> dict:
    import datetime
    from langchain_groq import ChatGroq
    import os

    trip_days = (
        datetime.datetime.strptime(end_date, "%Y-%m-%d") -
        datetime.datetime.strptime(start_date, "%Y-%m-%d")
    ).days + 1

    llm = ChatGroq(
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # Agent 1: Validate
    validation = llm.invoke(f"You are a travel expert. Summarize this trip: Destination={destination}, Start={start_date}, End={end_date}, Duration={trip_days} days. Write 3 sentences about what to expect.").content

    # Agent 2: Calendar
    from tools.calendar_tool import check_calendar_availability, block_calendar
    cal_check = check_calendar_availability(start_date, end_date)
    if cal_check.get("available"):
        cal_block = block_calendar(destination, start_date, end_date, validation)
        calendar_output = f"✅ Calendar is free! Blocked dates for {destination}.\n{cal_block.get('message', '')}"
    else:
        calendar_output = f"⚠️ Calendar has conflicts: {cal_check.get('message', '')}"

    # Agent 3: Itinerary
    itinerary = llm.invoke(f"Create a detailed {trip_days}-day travel itinerary for {destination} from {start_date} to {end_date}. Include morning, afternoon, evening activities, food recommendations, and daily budget in INR for each day.").content

    # Agent 4: Flights
    from tools.flight_tool import search_flights
    home_city = os.getenv("HOME_CITY", "Delhi")
    flight_results = search_flights(home_city, destination, start_date, end_date)
    flights_text = f"Flights from {home_city} to {destination}:\n"
    for i, f in enumerate(flight_results.get("flights", [])[:3], 1):
        seg = f["itineraries"][0]["segments"][0]
        price = f["price"]
        flights_text += f"{i}. {seg['carrier']}{seg['flight_number']} | {seg['departure']} → {seg['arrival']} | {price['currency']} {price['total']}\n"
    flight_recommendation = llm.invoke(f"Based on these flights:\n{flights_text}\nWhich is the best option and why? Keep it brief.").content

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "result": itinerary,
        "task_outputs": {
            "validation": validation,
            "calendar": calendar_output,
            "itinerary": itinerary,
            "flights": flights_text + "\n" + flight_recommendation,
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
