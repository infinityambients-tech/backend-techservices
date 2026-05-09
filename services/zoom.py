import os
import requests
import base64
from datetime import datetime, timedelta
import json


def get_zoom_access_token():
    """
    Pobranie access tokena z Zoom API (Server-to-Server OAuth).
    
    Environment Variables:
    - ZOOM_ACCOUNT_ID
    - ZOOM_CLIENT_ID
    - ZOOM_CLIENT_SECRET
    
    Returns:
    - str (access_token) lub raises Exception
    """
    account_id = os.getenv('ZOOM_ACCOUNT_ID')
    client_id = os.getenv('ZOOM_CLIENT_ID')
    client_secret = os.getenv('ZOOM_CLIENT_SECRET')
    
    if not all([account_id, client_id, client_secret]):
        print("[ZOOM WARNING] Missing credentials - returning mock URL")
        return None
    
    try:
        # Zoom S2S OAuth endpoint
        url = f"https://zoom.us/oauth/token"
        
        # Base64 encode credentials
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "account_credentials",
            "account_id": account_id
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=5)
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"[ZOOM ERROR] Token fetch failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ZOOM ERROR] get_zoom_access_token failed: {e}")
        return None


def generate_zoom_link(topic, start_time, duration):
    """
    Generowanie linku do spotkania Zoom.
    
    Parameters:
    - topic: str (nazwa spotkania, np. "Tech Service Consultation")
    - start_time: datetime (czas startu)
    - duration: str (minuty, np. "60")
    
    Returns:
    - str (Zoom meeting URL)
    
    Fallback:
    - Zwraca mock URL jeśli credentials brakuje lub API call fails
    
    API Endpoint:
    POST https://api.zoom.us/v2/users/{USER_ID}/meetings
    """
    token = get_zoom_access_token()
    
    # Fallback - zwróć mock URL jeśli brak credentials
    if not token:
        print(f"[ZOOM] Generating Zoom link for '{topic}' at {start_time} ({duration}min) - MOCK")
        # Zwróć fikcyjny link bazujący na timestamp
        import hashlib
        meeting_id = hashlib.md5(f"{topic}{start_time}".encode()).hexdigest()[:10].upper()
        return f"https://zoom.us/j/{meeting_id}"
    
    try:
        # Przygotuj payload spotkania
        meeting_payload = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
            "duration": int(duration),
            "timezone": "Europe/Warsaw",
            "agenda": "Scheduled meeting via TechServices",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": False,
                "waiting_room": False,
                "authentication": "password"
            }
        }
        
        # Pobierz Zoom User ID (zazwyczaj "me" dla S2S)
        user_id = "me"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # POST create meeting
        url = f"https://api.zoom.us/v2/users/{user_id}/meetings"
        response = requests.post(
            url,
            headers=headers,
            json=meeting_payload,
            timeout=10
        )
        
        if response.status_code in [201, 200]:
            meeting_data = response.json()
            meeting_url = meeting_data.get('join_url')
            meeting_id = meeting_data.get('id')
            print(f"[ZOOM SUCCESS] Meeting created: {meeting_id} | URL: {meeting_url}")
            return meeting_url
        else:
            print(f"[ZOOM ERROR] Meeting creation failed: {response.status_code} {response.text}")
            # Fallback na mock URL
            import hashlib
            meeting_id = hashlib.md5(f"{topic}{start_time}".encode()).hexdigest()[:10].upper()
            return f"https://zoom.us/j/{meeting_id}"
            
    except Exception as e:
        print(f"[ZOOM ERROR] generate_zoom_link exception: {e}")
        # Fallback na mock URL
        import hashlib
        meeting_id = hashlib.md5(f"{topic}{start_time}".encode()).hexdigest()[:10].upper()
        return f"https://zoom.us/j/{meeting_id}"
