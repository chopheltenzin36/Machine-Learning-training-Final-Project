import gradio as gr
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Define the API scope
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Your authenticate function
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

# Function to fetch Google Calendar events
def fetch_calendar_events(credentials):
    service = build("calendar", "v3", credentials=credentials)
    events_result = (
        service.events()
        .list(calendarId="primary", maxResults=10, singleEvents=True, orderBy="startTime")
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        return "No upcoming events found."

    # Displaying events
    return "\n".join([f"{event['summary']} at {event['start'].get('dateTime', event['start'].get('date'))}" for event in events])

# Enhanced analysis and recommendation logic
def daily_extra_hours_analysis(daily_hours, standard_hours):
    daily_reviews = {}
    for day, hours in daily_hours.items():
        std_hours = standard_hours.get(day, 0)
        extra_hours = max(0, hours - std_hours)
        daily_reviews[day] = {
            "extra_hours": extra_hours,
            "recommendation": ""
        }

        if extra_hours > 2:
            daily_reviews[day]["recommendation"] = (
                "⚠️ You’ve worked more than 2 extra hours today. Consider:\n"
                "  - Setting boundaries on work hours\n"
                "  - Taking breaks to prevent burnout\n"
                "  - Discussing workload with your supervisor if this becomes a habit"
            )
        elif extra_hours > 0:
            daily_reviews[day]["recommendation"] = (
                "⏳ You've worked extra hours today. Consider:\n"
                "  - Prioritizing tasks to avoid extra work\n"
                "  - Reviewing your schedule for a better balance"
            )
        else:
            daily_reviews[day]["recommendation"] = (
                "✅ You've worked within your standard hours today. Keep up the good balance!"
            )

    return daily_reviews

def generate_daily_reviews_and_recommendations(daily_hours, standard_hours):
    daily_reviews = daily_extra_hours_analysis(daily_hours, standard_hours)

    daily_review_output = "\n🔍 Daily Extra Hours Review\n"
    for day, review in daily_reviews.items():
        daily_review_output += f"\n{day}: {review['extra_hours']} extra hours worked"
        daily_review_output += f"\n  Recommendation: {review['recommendation']}\n"

    return daily_review_output

def analyze_workload(standard_hours, daily_hours):
    total_hours = sum(daily_hours.values())
    total_extra_hours = sum(max(0, hours - standard_hours.get(day, 0)) for day, hours in daily_hours.items())
    days_overworked = sum(1 for day, hours in daily_hours.items() if hours > standard_hours.get(day, 0))

    return {
        "total_hours": total_hours,
        "total_extra_hours": total_extra_hours,
        "days_overworked": days_overworked
    }

# Main interface function with enhanced daily review on extra hours
def easeai_interface(
    standard_hours_weekday,
    monday_hours, tuesday_hours, wednesday_hours, thursday_hours, friday_hours,
    saturday_working, standard_hours_saturday, saturday_hours, include_calendar
):
    try:
        standard_hours = {
            'Monday': float(standard_hours_weekday),
            'Tuesday': float(standard_hours_weekday),
            'Wednesday': float(standard_hours_weekday),
            'Thursday': float(standard_hours_weekday),
            'Friday': float(standard_hours_weekday)
        }

        daily_hours = {
            'Monday': float(monday_hours),
            'Tuesday': float(tuesday_hours),
            'Wednesday': float(wednesday_hours),
            'Thursday': float(thursday_hours),
            'Friday': float(friday_hours)
        }

        if saturday_working == "Yes":
            standard_hours['Saturday'] = float(standard_hours_saturday)
            daily_hours['Saturday'] = float(saturday_hours)
        else:
            standard_hours['Saturday'] = 0
            daily_hours['Saturday'] = 0

        workload_analysis = analyze_workload(standard_hours, daily_hours)
        daily_review_output = generate_daily_reviews_and_recommendations(daily_hours, standard_hours)

        output = "📊 **Weekly Work Analysis**\n\n"
        output += f"📅 **Standard working hours per weekday**: {standard_hours_weekday} hours/day\n"
        if saturday_working == "Yes":
            output += f"📅 **Standard working hours on Saturday**: {standard_hours_saturday} hours\n"
        output += f"⏱️ **Total hours worked**: {workload_analysis['total_hours']} hours\n"
        output += f"📉 **Extra hours worked**: {workload_analysis['total_extra_hours']} hours\n"
        output += f"⚠️ **Days with overwork**: {workload_analysis['days_overworked']}\n"
        output += daily_review_output

        if include_calendar:
            credentials = authenticate()
            calendar_data = fetch_calendar_events(credentials)
            output += f"\n📅 **Google Calendar Events**:\n{calendar_data}"

        return output
    
    except ValueError:
        return "Error: Please enter valid numeric values for hours."

# Define the function to update Saturday fields visibility
def update_saturday_fields(saturday_working):
    if saturday_working == "Yes":
        return gr.update(visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)

# Gradio interface setup
with gr.Blocks() as interface:
    gr.Markdown("## Weekly Work Analysis Tool")
    with gr.Row():
        standard_hours_weekday = gr.Textbox(label="Standard Hours (Weekday)", value="")
    with gr.Column():
        monday_hours = gr.Textbox(label="Monday Hours", value="")
        tuesday_hours = gr.Textbox(label="Tuesday Hours", value="")
        wednesday_hours = gr.Textbox(label="Wednesday Hours", value="")
        thursday_hours = gr.Textbox(label="Thursday Hours", value="")
        friday_hours = gr.Textbox(label="Friday Hours", value="")
    with gr.Row():
        saturday_working = gr.Radio(
            label="Working on Saturday?", 
            choices=["Yes", "No"], 
            value="No", 
            interactive=True
        )
        standard_hours_saturday = gr.Textbox(label="Standard Hours (Saturday)", value="", visible=False)
        saturday_hours = gr.Textbox(label="Saturday Hours", value="", visible=False)
    saturday_working.change(update_saturday_fields, saturday_working, [standard_hours_saturday, saturday_hours])
    with gr.Row():
        include_calendar = gr.Checkbox(label="Include Google Calendar Data?")
    with gr.Row():
        output = gr.Textbox(label="Analysis", lines=15)
    gr.Button("Analyze").click(
        easeai_interface,
        [standard_hours_weekday, monday_hours, tuesday_hours, wednesday_hours, thursday_hours, friday_hours, 
        saturday_working, standard_hours_saturday, saturday_hours, include_calendar],
        output
    )

# Launch the app
interface.launch()
