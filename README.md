# ✈️ Travel AI Agent
**Multi-Agent AI Trip Planner** built with **CrewAI** + **Open-Source LLMs** (Llama3 via Groq/Ollama)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   TRAVEL AI CREW                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │   Agent 1    │    │   Agent 2    │                  │
│  │   Input      │───▶│  Calendar    │                  │
│  │  Processor   │    │  Manager     │                  │
│  └──────────────┘    └──────┬───────┘                  │
│                             │                           │
│                    ┌────────┴────────┐                  │
│                    │                 │                  │
│             ┌──────▼──────┐  ┌──────▼──────┐           │
│             │   Agent 3   │  │   Agent 4   │           │
│             │  Itinerary  │  │   Flight    │           │
│             │  Planner    │  │  Specialist │           │
│             └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────┘
         │                │                  │
   Google Calendar   Amadeus API      LLM (Groq/Ollama)
```

## 🤖 The 4 AI Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Input Processor** | Validates destination & dates, identifies trip type | LLM reasoning |
| **Calendar Manager** | Checks Google Calendar, blocks travel dates | Google Calendar API |
| **Itinerary Planner** | Creates day-by-day travel plan with food & activities | LLM reasoning |
| **Flight Specialist** | Finds available flights, compares prices | Amadeus Flight API |

---

## ⚡ Quick Start

### 1. Clone & Install
```bash
git clone <repo>
cd travel-ai-agent
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Set Up LLM (Choose ONE)

**Option A: Groq (Recommended - Free, Fast)**
```bash
# Get free API key at: https://console.groq.com/
# Add to .env:
GROQ_API_KEY=your_key_here
LLM_MODEL=llama3-70b-8192
```

**Option B: Ollama (Fully Local, No API Key)**
```bash
# Install Ollama: https://ollama.ai/
ollama pull llama3
# Add to .env:
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 4. Set Up Google Calendar
```bash
# Follow the guide:
python config/setup_google_auth.py

# Then authenticate:
python config/setup_google_auth.py --authenticate
```

### 5. Set Up Flight Search (Optional)
```bash
# Free API at: https://developers.amadeus.com/
# Register → My Apps → Create App → Get Client ID & Secret
# Add to .env:
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
# NOTE: Without this, mock flight data is used (works for demo)
```

---

## 🚀 Running the Agent

### Option 1: Streamlit UI (Recommended)
```bash
streamlit run ui/app.py
# Opens at: http://localhost:8501
```

### Option 2: Interactive CLI
```bash
python main.py
```

### Option 3: FastAPI Server
```bash
python main.py --api
# API docs at: http://localhost:8000/docs
```

### Option 4: Demo Run
```bash
python main.py --demo
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/plan-trip` | Start async trip planning |
| `POST` | `/plan-trip/sync` | Synchronous trip planning |
| `GET`  | `/job/{job_id}` | Poll for async job result |
| `POST` | `/check-calendar` | Check calendar availability |
| `POST` | `/search-flights` | Search available flights |
| `GET`  | `/docs` | Interactive API docs |

### Example API Call
```bash
curl -X POST http://localhost:8000/plan-trip/sync \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "start_date": "2025-12-20",
    "end_date": "2025-12-25"
  }'
```

---

## 📁 Project Structure

```
travel-ai-agent/
├── agents/
│   └── travel_crew.py      # CrewAI agents & tasks
├── tools/
│   ├── calendar_tool.py    # Google Calendar integration
│   └── flight_tool.py      # Amadeus flight search
├── config/
│   ├── llm_config.py       # LLM setup (Groq/Ollama)
│   ├── setup_google_auth.py # Google OAuth helper
│   └── credentials.json    # (you create this)
├── ui/
│   └── app.py              # Streamlit UI
├── api.py                  # FastAPI backend
├── main.py                 # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Agent Framework** | CrewAI |
| **LLM (Cloud)** | Groq API → Llama3-70B / Mixtral |
| **LLM (Local)** | Ollama → Llama3 / Mistral |
| **Calendar** | Google Calendar API v3 |
| **Flights** | Amadeus for Developers API |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **Config** | python-dotenv |

---

## 🔒 Notes

- Google Calendar requires OAuth 2.0 (one-time browser auth)
- Amadeus free tier works on test environment (real-ish data)
- Without Amadeus credentials, mock flight data is used
- Groq free tier: 14,400 tokens/min (plenty for this app)
- All LLMs used are fully open-source (Llama3, Mixtral)

---

## 📝 Sample Output

```
🚀 TRAVEL AI CREW STARTING
📍 Destination: Goa
📅 Dates: 2025-12-20 → 2025-12-25

[Agent 1] ✅ 5-day beach vacation identified. Goa in December is peak season...

[Agent 2] ✅ Calendar checked. No conflicts found.
          ✅ Calendar blocked: ✈️ Travel to Goa (Dec 20-25)

[Agent 3] 🗺️ Day 1: Arrive in Goa, check into North Goa hotel...
          Day 2: Calangute → Baga → Anjuna flea market...
          [Full 5-day itinerary]

[Agent 4] ✈️ Top flights from Delhi:
          1. Air India AI-101 | 06:00 → 08:30 | ₹12,500
          2. IndiGo 6E-234 | 10:00 → 14:15 | ₹8,900
          Recommendation: Option 2 best value...
```
