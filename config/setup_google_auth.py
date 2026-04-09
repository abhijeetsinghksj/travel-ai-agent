"""
Google Calendar Setup Helper
Run this script to authenticate with Google Calendar
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def setup_google_calendar():
    print("\n📅 GOOGLE CALENDAR SETUP")
    print("="*50)
    print("""
STEP 1: Create Google Cloud Project
  1. Go to: https://console.cloud.google.com/
  2. Create a new project (or use existing)
  3. Enable "Google Calendar API":
     APIs & Services → Enable APIs → Search "Google Calendar API" → Enable

STEP 2: Create OAuth Credentials
  1. Go to: APIs & Services → Credentials
  2. Click "Create Credentials" → "OAuth client ID"
  3. Application type: "Desktop app"
  4. Download the JSON file
  5. Save it as: ./config/credentials.json

STEP 3: Run this script to authenticate
  python config/setup_google_auth.py --authenticate
""")

    if "--authenticate" in sys.argv:
        print("🔐 Starting OAuth authentication flow...")
        
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./config/credentials.json")
        token_path = os.getenv("GOOGLE_TOKEN_PATH", "./config/token.json")
        
        if not os.path.exists(creds_path):
            print(f"❌ Credentials file not found at: {creds_path}")
            print("Please follow STEP 2 above first.")
            return
        
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            SCOPES = [
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/calendar.events",
            ]
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            
            print(f"\n✅ Authentication successful!")
            print(f"Token saved to: {token_path}")
            print("\nYou can now run the Travel AI Agent!")
            
        except ImportError:
            print("❌ google-auth-oauthlib not installed.")
            print("Run: pip install google-auth-oauthlib")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
    else:
        print("ℹ️  To authenticate, run:")
        print("   python config/setup_google_auth.py --authenticate")


if __name__ == "__main__":
    setup_google_calendar()
