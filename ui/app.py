"""
Streamlit UI for Travel AI Agent
Run: streamlit run ui/app.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Travel AI Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;500&display=swap');
    
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        color: #fff;
        text-align: center;
        text-shadow: 0 0 30px rgba(255,200,100,0.5);
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        text-align: center;
        color: #aaa;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }
    .agent-card h4 { color: #ffd700; margin: 0 0 0.3rem 0; font-size: 0.9rem; }
    .agent-card p { color: #ccc; margin: 0; font-size: 0.8rem; }
    .result-box {
        background: rgba(255,255,255,0.05);
        border-left: 4px solid #ffd700;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #eee;
        white-space: pre-wrap;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .status-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-running { background: #1a3a5c; color: #4fc3f7; }
    .badge-done { background: #1a3a1a; color: #81c784; }
    .badge-error { background: #3a1a1a; color: #e57373; }
    
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #f7971e, #ffd200);
        color: #1a1a1a;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        padding: 0.6rem 2rem;
        width: 100%;
        transition: all 0.2s;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255,200,0,0.3);
    }
</style>
""", unsafe_allow_html=True)


def run_travel_planning(destination, start_date, end_date):
    """Run the full travel crew and stream results."""
    from agents.travel_crew import run_travel_crew
    return run_travel_crew(
        destination=destination,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )


# ─── Header ───────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">✈️ Travel AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">AI-powered trip planning • Calendar blocking • Flight search</p>', unsafe_allow_html=True)

# ─── Sidebar - Config Info ─────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 Agent Pipeline")
    agents_info = [
        ("📋", "Input Processor", "Validates destination & dates"),
        ("📅", "Calendar Manager", "Checks & blocks Google Calendar"),
        ("🗺️", "Itinerary Planner", "Creates day-by-day travel plan"),
        ("✈️", "Flight Specialist", "Finds best available flights"),
    ]
    for icon, name, desc in agents_info:
        st.markdown(f"""
        <div class="agent-card">
            <h4>{icon} {name}</h4>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "")
    
    if groq_key and groq_key != "your_groq_api_key_here":
        model = os.getenv("LLM_MODEL", "llama3-70b-8192")
        st.success(f"🟢 LLM: Groq ({model})")
    elif ollama_url:
        model = os.getenv("OLLAMA_MODEL", "llama3")
        st.success(f"🟢 LLM: Ollama ({model})")
    else:
        st.warning("⚠️ LLM not configured\nSet GROQ_API_KEY in .env")

    gcal_creds = os.path.exists(os.getenv("GOOGLE_CREDENTIALS_PATH", "./config/credentials.json"))
    if gcal_creds:
        st.success("🟢 Google Calendar: Ready")
    else:
        st.warning("⚠️ Google Calendar: Not configured")

    amadeus_id = os.getenv("AMADEUS_CLIENT_ID", "")
    if amadeus_id and amadeus_id != "your_amadeus_client_id":
        st.success("🟢 Flights: Amadeus API")
    else:
        st.info("🔵 Flights: Mock data (demo)")


# ─── Main Form ─────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    destination = st.text_input(
        "🌍 Destination",
        placeholder="e.g., Goa, Paris, Bali, Tokyo...",
        help="Enter city or country name"
    )

with col2:
    start_date = st.date_input(
        "📅 Start Date",
        value=date.today() + timedelta(days=30),
        min_value=date.today(),
    )

with col3:
    end_date = st.date_input(
        "📅 End Date",
        value=date.today() + timedelta(days=35),
        min_value=date.today() + timedelta(days=1),
    )

# Validation
if destination and start_date and end_date:
    if end_date <= start_date:
        st.error("⚠️ End date must be after start date")
    else:
        trip_days = (end_date - start_date).days + 1
        st.info(f"🗓️ Trip duration: **{trip_days} days** | {start_date.strftime('%d %b')} → {end_date.strftime('%d %b %Y')}")

st.markdown("---")

# ─── Action Button ─────────────────────────────────────────────
if st.button("🚀 Plan My Trip with AI Agents"):
    if not destination:
        st.error("Please enter a destination!")
    elif end_date <= start_date:
        st.error("Please fix the dates!")
    else:
        # Status tracking
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🤖 Agents at Work...")
            
            agent_status = {
                "Input Processor": ("🔄", "running"),
                "Calendar Manager": ("⏳", "waiting"),
                "Itinerary Planner": ("⏳", "waiting"),
                "Flight Specialist": ("⏳", "waiting"),
            }
            
            def show_agent_status():
                cols = st.columns(4)
                icons = {"running": "🔄", "waiting": "⏳", "done": "✅", "error": "❌"}
                colors = {"running": "#4fc3f7", "waiting": "#888", "done": "#81c784", "error": "#e57373"}
                for i, (name, (icon, status)) in enumerate(agent_status.items()):
                    with cols[i]:
                        color = colors[status]
                        st.markdown(
                            f'<div style="text-align:center; padding:8px; border:1px solid {color}; border-radius:8px; color:{color}">'
                            f'{icons[status]} {name}</div>',
                            unsafe_allow_html=True
                        )
            
            status_placeholder = st.empty()
            
            with status_placeholder.container():
                show_agent_status()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⚙️ Initializing AI agents...")
                progress_bar.progress(10)
                
                # Run the crew
                with st.spinner("AI agents are planning your trip... (this may take 1-3 minutes)"):
                    result = run_travel_planning(destination, start_date, end_date)
                
                progress_bar.progress(100)
                agent_status = {k: ("✅", "done") for k in agent_status}
                with status_placeholder.container():
                    show_agent_status()
                
                st.success("🎉 Trip planning complete!")
                
                # Show results in tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📋 Trip Summary", "📅 Calendar", "🗺️ Itinerary", "✈️ Flights"
                ])
                
                outputs = result.get("task_outputs", {})
                
                with tab1:
                    st.markdown("### 📋 Trip Validation & Summary")
                    val_output = outputs.get("validation", "")
                    if val_output:
                        st.markdown(f'<div class="result-box">{val_output}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Trip details validated successfully.")
                
                with tab2:
                    st.markdown("### 📅 Calendar Status")
                    cal_output = outputs.get("calendar", "")
                    if cal_output:
                        st.markdown(f'<div class="result-box">{cal_output}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Calendar check completed.")
                
                with tab3:
                    st.markdown("### 🗺️ Your Itinerary")
                    itin_output = outputs.get("itinerary", "")
                    if itin_output:
                        st.markdown(f'<div class="result-box">{itin_output}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Itinerary generated. Check the full result below.")
                
                with tab4:
                    st.markdown("### ✈️ Available Flights")
                    flight_output = outputs.get("flights", "")
                    if flight_output:
                        st.markdown(f'<div class="result-box">{flight_output}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Flight search completed.")
                
                # Full output
                with st.expander("📄 Full Agent Output"):
                    st.markdown(f'<div class="result-box">{result.get("result", "")}</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                agent_status = {k: ("❌", "error") for k in agent_status}
                with status_placeholder.container():
                    show_agent_status()
                st.error(f"❌ Error: {str(e)}")
                with st.expander("Debug Info"):
                    st.exception(e)


# ─── Demo Mode ─────────────────────────────────────────────────
with st.expander("🧪 Test Individual Tools"):
    tool_col1, tool_col2 = st.columns(2)
    
    with tool_col1:
        st.markdown("**Check Calendar**")
        cal_start = st.date_input("Check from", value=date.today() + timedelta(days=7), key="cal_start")
        cal_end = st.date_input("Check to", value=date.today() + timedelta(days=10), key="cal_end")
        if st.button("Check Calendar Only"):
            from tools.calendar_tool import check_calendar_availability
            result = check_calendar_availability(
                cal_start.strftime("%Y-%m-%d"),
                cal_end.strftime("%Y-%m-%d")
            )
            st.json(result)
    
    with tool_col2:
        st.markdown("**Search Flights**")
        flight_dest = st.text_input("Flight destination", value="Goa", key="flight_dest")
        flight_date = st.date_input("Departure", value=date.today() + timedelta(days=30), key="flight_date")
        if st.button("Search Flights Only"):
            from tools.flight_tool import search_flights
            home_city = os.getenv("HOME_CITY", "Delhi")
            result = search_flights(home_city, flight_dest, flight_date.strftime("%Y-%m-%d"))
            st.json(result)
