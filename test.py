from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build

# Define the API scope
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


# Authenticate and authorize
def authenticate():
    flow = Flow.from_client_secrets_file("credentials.json", SCOPES, redirect_uri="http://localhost:8080")

    # Get the authorization URL
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")

    print("Please go to this URL and authorize the application:")
    print(auth_url)

    # After getting the code, you can paste it here
    code = input("Enter the authorization code: ")

    flow.fetch_token(code=code)
    credentials = flow.credentials
    return credentials


creds = authenticate()

# Build the servicfe object to interact with the Calendar API

service = build("calendar", "v3", credentials=creds)
events_result = (
    service.events().list(calendarId="primary", maxResults=10, singleEvents=True, orderBy="startTime").execute()
)

print(events_result)
