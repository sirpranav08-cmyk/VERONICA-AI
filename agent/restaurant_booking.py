"""
VERONICA Restaurant Booking via Twilio
Automatically calls restaurant and speaks booking details
"""
from twilio.rest import Client
import os

# Your Twilio credentials — add to .env file
ACCOUNT_SID = os.getenv("TWILIO_SID", "your_account_sid")
AUTH_TOKEN  = os.getenv("TWILIO_TOKEN", "your_auth_token")
FROM_NUMBER = os.getenv("TWILIO_PHONE", "+1234567890")  # Your Twilio number

def book_table(
    restaurant_phone: str,
    restaurant_name: str,
    guest_name: str,
    date: str,
    time: str,
    guests: int
) -> str:
    """Make automated call to restaurant and speak booking details."""
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)

        # TwiML — what VERONICA will say during the call
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Pause length="2"/>
    <Say voice="Polly.Aditi" rate="slow">
        Hello! This is an automated booking call from VERONICA AI assistant.
        I would like to book a table at {restaurant_name}.
        The booking details are as follows.
        Name: {guest_name}.
        Date: {date}.
        Time: {time}.
        Number of guests: {guests}.
        Please confirm this reservation.
        Thank you very much. Have a wonderful day!
    </Say>
    <Pause length="3"/>
    <Say voice="Polly.Aditi">
        If you need to reach us, please call back on the number that called you.
        Thank you. Goodbye!
    </Say>
</Response>"""

        call = client.calls.create(
            twiml=twiml,
            to=restaurant_phone,
            from_=FROM_NUMBER
        )

        return (f"Call initiated to {restaurant_name} ({restaurant_phone}), Sir. "
                f"Booking for {guest_name}, {guests} guests on {date} at {time}. "
                f"Call SID: {call.sid}")

    except Exception as e:
        return f"Booking call failed, Sir: {str(e)}"


def search_restaurant_number(restaurant_name: str, location: str) -> str:
    """Search for restaurant phone number online."""
    import urllib.request
    import urllib.parse
    query = f"{restaurant_name} restaurant {location} phone number"
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
    try:
        r = urllib.request.urlopen(url, timeout=8)
        import json
        data = json.loads(r.read())
        abstract = data.get("AbstractText", "")
        return abstract[:300] if abstract else f"Could not find number for {restaurant_name}. Please provide the phone number manually."
    except:
        return "Search failed. Please provide restaurant phone number manually."


if __name__ == "__main__":
    # Test
    result = book_table(
        restaurant_phone="+919876543210",
        restaurant_name="Hotel Saravana Bhavan",
        guest_name="Pranav",
        date="July 25 2026",
        time="7:30 PM",
        guests=4
    )
    print(result)