"""
Google Calendar Tool
- Check availability between dates
- Block calendar with travel event
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("[Warning] Google API libraries not installed. Calendar features disabled.")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def _get_calendar_service():
    """Authenticate using Service Account (cloud) or OAuth (local)."""
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("Google API libraries not installed.")

    # Option 1: Service Account JSON from Streamlit secrets or env (cloud)
    service_account_json = None
    try:
        import streamlit as st
        service_account_json = st.secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    except:
        pass
    if not service_account_json:
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        try:
            from google.oauth2 import service_account
            info = json.loads(service_account_json)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            print(f"[Calendar] Service account failed: {e}")

    # Option 2: OAuth token (local)
    try:
        creds = None
        token_path = os.getenv("GOOGLE_TOKEN_PATH", "./config/token.json")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./config/credentials.json")
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError("No credentials found.")
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"All auth methods failed: {e}")


def check_calendar_availability(start_date: str, end_date: str) -> dict:
    """
    Check if the user is free between start_date and end_date.
    
    Args:
        start_date: ISO format date string (YYYY-MM-DD)
        end_date: ISO format date string (YYYY-MM-DD)
    
    Returns:
        dict with 'available' bool and 'conflicts' list
    """
    try:
        service = _get_calendar_service()
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

        # Convert to RFC3339 format
        start_dt = datetime.fromisoformat(start_date).replace(
            hour=0, minute=0, second=0, tzinfo=timezone.utc
        )
        end_dt = datetime.fromisoformat(end_date).replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        conflicts = []

        for event in events:
            # Skip all-day events that are just reminders
            if event.get("transparency") == "transparent":
                continue
            conflicts.append({
                "summary": event.get("summary", "Busy"),
                "start": event["start"].get("dateTime", event["start"].get("date")),
                "end": event["end"].get("dateTime", event["end"].get("date")),
            })

        return {
            "available": len(conflicts) == 0,
            "conflicts": conflicts,
            "message": f"Found {len(conflicts)} conflicting event(s)" if conflicts else "Calendar is free for the travel dates!",
        }

    except FileNotFoundError as e:
        return {"available": None, "conflicts": [], "message": str(e), "error": True}
    except Exception as e:
        return {"available": None, "conflicts": [], "message": f"Calendar check failed: {str(e)}", "error": True}


def block_calendar(
    destination: str,
    start_date: str,
    end_date: str,
    description: str = "",
) -> dict:
    """
    Block Google Calendar with a travel event.
    
    Args:
        destination: Name of the destination
        start_date: ISO format date (YYYY-MM-DD)
        end_date: ISO format date (YYYY-MM-DD)
        description: Optional event description / itinerary summary
    
    Returns:
        dict with 'success' bool and 'event_link'
    """
    try:
        service = _get_calendar_service()
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

        event = {
            "summary": f"✈️ Travel to {destination}",
            "description": description or f"Trip to {destination}\nManaged by Travel AI Agent",
            "start": {"date": start_date},
            "end": {"date": end_date},
            "colorId": "9",  # Blueberry
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},  # 1 day before
                    {"method": "popup", "minutes": 60},
                ],
            },
        }

        created_event = service.events().insert(
            calendarId=calendar_id, body=event
        ).execute()

        return {
            "success": True,
            "event_id": created_event["id"],
            "event_link": created_event.get("htmlLink", ""),
            "message": f"✅ Calendar blocked for trip to {destination} ({start_date} → {end_date})",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to block calendar: {str(e)}",
            "error": True,
        }
