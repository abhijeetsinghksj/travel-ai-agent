"""
Travel AI Agent - Main Entry Point
Run modes:
  python main.py                    → Interactive CLI
  python main.py --ui               → Streamlit UI
  python main.py --api              → FastAPI server
  python main.py --demo             → Demo run with sample trip
"""
import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()


def run_cli():
    """Interactive CLI for travel planning."""
    print("\n" + "="*60)
    print("  ✈️  TRAVEL AI AGENT - Powered by CrewAI + Open Source LLM")
    print("="*60 + "\n")

    destination = input("🌍 Where do you want to travel? ").strip()
    if not destination:
        print("Destination cannot be empty.")
        return

    start_date = input("📅 Start date (YYYY-MM-DD): ").strip()
    end_date = input("📅 End date   (YYYY-MM-DD): ").strip()

    try:
        from datetime import datetime
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Please use YYYY-MM-DD")
        return

    print(f"\n🚀 Starting AI agents for your trip to {destination}...\n")

    from agents.travel_crew import run_travel_crew
    result = run_travel_crew(destination, start_date, end_date)

    print("\n" + "="*60)
    print("  ✅ TRAVEL PLANNING COMPLETE")
    print("="*60)
    
    outputs = result.get("task_outputs", {})
    
    print("\n📋 TRIP SUMMARY:")
    print("-" * 40)
    print(outputs.get("validation", "N/A"))
    
    print("\n📅 CALENDAR STATUS:")
    print("-" * 40)
    print(outputs.get("calendar", "N/A"))
    
    print("\n🗺️ ITINERARY:")
    print("-" * 40)
    print(outputs.get("itinerary", "N/A"))
    
    print("\n✈️ FLIGHTS:")
    print("-" * 40)
    print(outputs.get("flights", "N/A"))


def run_streamlit():
    """Launch Streamlit UI."""
    import subprocess
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    print("🌐 Starting Streamlit UI at http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path])


def run_api():
    """Launch FastAPI server."""
    import uvicorn
    print("🌐 Starting FastAPI server at http://localhost:8000")
    print("📖 API docs at http://localhost:8000/docs")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


def run_demo():
    """Demo run with pre-configured trip."""
    print("\n🎯 Running DEMO: 5-day trip to Goa")
    from agents.travel_crew import run_travel_crew
    result = run_travel_crew("Goa", "2025-12-20", "2025-12-25")
    
    print("\n=== DEMO RESULT ===")
    print(result.get("result", "No output"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Travel AI Agent")
    parser.add_argument("--ui", action="store_true", help="Launch Streamlit UI")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI server")
    parser.add_argument("--demo", action="store_true", help="Run demo trip")
    args = parser.parse_args()

    if args.ui:
        run_streamlit()
    elif args.api:
        run_api()
    elif args.demo:
        run_demo()
    else:
        run_cli()
