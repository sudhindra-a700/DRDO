import os
import random
import sqlite3
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# Load environment variables from .env file
load_dotenv(r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\.env")

DB_PATH = r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Backend\DRDO_Normalized_Updated_Names.db"
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
print(f"DEBUG: Loaded FAST2SMS_API_KEY = {FAST2SMS_API_KEY if FAST2SMS_API_KEY else 'Not Found'}")

def generate_otp():
    return random.randint(100000, 999999)

def send_sms(phone_number, message):
    if not FAST2SMS_API_KEY:
        print("❌ FAST2SMS_API_KEY not set in environment variables.")
        return {"return": False, "message": "SMS service configuration error: API key missing"}

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "message": message,
        "language": "english",
        "route": "q",
        "numbers": phone_number,
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Configure retries with backoff
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    print(f"📤 Sending SMS to {phone_number} with message: {message}")
    try:
        response = session.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        print(f"✅ SMS API Response: {response_data}")

        if isinstance(response_data, dict) and response_data.get("return", False):
            return {"return": True, "message": "SMS sent successfully"}
        else:
            error_msg = response_data.get("message", "Unknown API error") if isinstance(response_data, dict) else "Invalid response format"
            print(f"❌ API returned error: {error_msg}")
            return {"return": False, "message": error_msg}

    except requests.exceptions.HTTPError as e:
        error_text = e.response.text if hasattr(e, 'response') and hasattr(e.response, 'text') else str(e)
        print(f"❌ HTTP Error: {error_text}")
        return {"return": False, "message": f"HTTP error: {error_text}"}
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return {"return": False, "message": "SMS service timed out"}
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return {"return": False, "message": "Failed to connect to SMS service: Network or DNS issue"}
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return {"return": False, "message": f"Request error: {str(e)}"}

def send_otp(phone_number, role):
    # Validate phone number format (10 digits)
    if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
        print(f"❌ Invalid phone number: {phone_number}")
        return {"return": False, "message": "Invalid phone number: Must be 10 digits"}

    otp = generate_otp()
    message = f"Your OTP for {role} login is {otp}. Valid for 5 minutes."
    response = send_sms(phone_number, message)

    if response["return"]:
        print(f"✅ OTP {otp} generated and sent to {phone_number}")
        return {"return": True, "otp": otp}
    else:
        print(f"❌ Failed to send OTP to {phone_number}: {response['message']}")
        return response  # Propagate the error without fallback

def generate_candidate_id():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Interviewee")
        count = cursor.fetchone()[0]
        candidate_id = f"CAND{count + 1:04d}"
    return candidate_id

def store_candidate_data(candidate_id, name, email, phone, age, experience, gate_score, core_field):
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Interviewee (interviewee_id, name, email, phone)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(interviewee_id) DO UPDATE SET 
                    name = excluded.name,
                    email = excluded.email,
                    phone = excluded.phone
            """, (candidate_id, name, email, phone))
            cursor.execute("""
                INSERT INTO Interviewee_Interests (interviewee_id, field_of_interest)
                VALUES (?, ?)
            """, (candidate_id, core_field))
            conn.commit()
        print(f"✅ Candidate {candidate_id} data stored successfully.")
    except sqlite3.Error as e:
        print(f"❌ Error storing candidate data: {e}")
        raise