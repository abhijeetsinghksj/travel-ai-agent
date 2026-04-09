"""
FastAPI Backend for Travel AI Agent
Exposes REST endpoints for the Streamlit UI and direct API access
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Travel AI Agent API",
    description="AI-powered travel planning with Google Calendar integration and flight search",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (use Redis in production)
jobs: dict = {}


class TravelRequest(BaseModel):
    destination: str = Field(..., example="Goa")
    start_date: str = Field(..., example="2025-12-20", description="YYYY-MM-DD")
    end_date: str = Field(..., example="2025-12-25", description="YYYY-MM-DD")


class CalendarCheckRequest(BaseModel):
    start_date: str
    end_date: str


class FlightSearchRequest(BaseModel):
    destination: str
    departure_date: str
    return_date: Optional[str] = None


@app.get("/")
def root():
    return {
        "name": "Travel AI Agent",
        "status": "running",
        "endpoints": [
            "/plan-trip",
            "/check-calendar",
            "/search-flights",
            "/job/{job_id}",
            "/docs",
        ]
    }


@app.post("/plan-trip")
async def plan_trip(request: TravelRequest, background_tasks: BackgroundTasks):
    """
    Start full travel planning workflow:
    1. Validate inputs
    2. Check & block Google Calendar
    3. Generate itinerary
    4. Search flights
    """
    # Validate dates
    try:
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = datetime.strptime(request.end_date, "%Y-%m-%d")
        if end <= start:
            raise HTTPException(status_code=400, detail="End date must be after start date")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Create job
    job_id = f"trip_{request.destination.lower().replace(' ', '_')}_{request.start_date}"
    jobs[job_id] = {"status": "running", "result": None}

    # Run in background
    background_tasks.add_task(_run_crew_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Planning your trip to {request.destination}. Poll /job/{job_id} for results.",
        "poll_url": f"/job/{job_id}",
    }


@app.post("/plan-trip/sync")
def plan_trip_sync(request: TravelRequest):
    """
    Synchronous version - waits for full result (may take 2-5 min with LLM).
    Use this for testing.
    """
    try:
        from agents.travel_crew import run_travel_crew
        result = run_travel_crew(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return {"status": "completed", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Poll for job status and result."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.post("/check-calendar")
def check_calendar(request: CalendarCheckRequest):
    """Check Google Calendar availability for given dates."""
    from tools.calendar_tool import check_calendar_availability
    result = check_calendar_availability(request.start_date, request.end_date)
    return result


@app.post("/search-flights")
def search_flights_endpoint(request: FlightSearchRequest):
    """Search for available flights."""
    from tools.flight_tool import search_flights
    home_city = os.getenv("HOME_CITY", "Delhi")
    result = search_flights(
        origin=home_city,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
    )
    return result


async def _run_crew_job(job_id: str, request: TravelRequest):
    """Background task to run the crew."""
    try:
        from agents.travel_crew import run_travel_crew
        result = run_travel_crew(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        jobs[job_id] = {"status": "completed", "result": result}
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
    )
