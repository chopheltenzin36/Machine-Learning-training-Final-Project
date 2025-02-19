
import gradio as gr
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCnCsZ4V-vW9qOjkqY_qaVXWMsPUGmgrxI"  # Your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# Define the API scope for Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# System instructions (editable only by the developer)
SYSTEM_INSTRUCTION = """
You are a helpful AI assistant for EaseAI, a tool designed to improve mental health and well-being in professional environments.
Your role is to provide personalized recommendations for breaks, time management strategies, and wellbeing tips based on the user's workload and Google Calendar data.
You will analyze the user's weekly work schedule, including regular working hours and any additional hours worked beyond standard office hours, to identify patterns of overworking or underworking.
You will also access the user's Google Calendar to retrieve weekly meeting schedules, important events, and personal appointments, using this data to detect potential stressors and provide reminders for upcoming events.
Your recommendations should include:
- Break Time Suggestions: Tailored to the user's specific schedule to reduce stress and improve productivity. Suggest taking breaks with healthy snacks like nuts, fruits, or energy balls to maintain energy levels and focus.
- Management Strategies: Advice on managing workload, prioritizing tasks, and optimizing time management. Identify days where the user has overworked and suggest strategies to mitigate these situations, such as delegating tasks or adjusting deadlines. Also, identify days where the user has underworked and recommend using these days to prepare for upcoming tasks, attend professional development workshops, or catch up on pending work to avoid overworking on other days.
- Wellbeing Tips: Personalized suggestions for stress-reduction techniques, physical activity, and mindfulness exercises aligned with the user's schedule and preferences.
- Overworking and Underworking Detection: Identify instances of both overworking and underworking. For overworking, suggest mitigation strategies. For underworking, recommend ways to utilize spare time effectively to maintain a balanced workload across the week and prevent excessive work on other days.
- Calendar Event Reminders: Remind users of important events, meetings, and deadlines to help plan ahead.
- Social and Recreational Reminders: Encourage users to attend social events like birthdays or anniversaries to foster a sense of community and support.
- Rescheduling Recommendations: If the user's schedule appears unsustainable, suggest rescheduling meetings or tasks with HR or team members to achieve a more balanced workload.
- Healthy Snack Recommendations: During breaks, suggest consuming healthy snacks such as mixed nuts, dried fruits, whole grain crackers, or Greek yogurt to maintain energy levels and support overall well-being.
Always respond in a friendly, professional, and empathetic tone.
"""

# Initialize Gemini model with system instructions
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# Your authenticate function for Google Calendar
def authenticate():
    flow = Flow.from_client_secrets_file("credentials.json", SCOPES, redirect_uri="http://127.0.0.1:8080")
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    print("Please go to this URL and authorize the application:")
    print(auth_url)
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

# Function to generate analysis and recommendations using Gemini
def generate_analysis_and_recommendations(standard_hours, daily_hours, calendar_data):
    # Prepare the prompt for Gemini
    prompt = f"""
    The user's standard working hours are:
    - Monday to Friday: {standard_hours['Monday']} hours/day
    - Saturday: {standard_hours.get('Saturday', 0)} hours

    Their actual working hours this week are:
    - Monday: {daily_hours['Monday']} hours
    - Tuesday: {daily_hours['Tuesday']} hours
    - Wednesday: {daily_hours['Wednesday']} hours
    - Thursday: {daily_hours['Thursday']} hours
    - Friday: {daily_hours['Friday']} hours
    - Saturday: {daily_hours.get('Saturday', 0)} hours

    Their Google Calendar events for the week are:
    {calendar_data}

    Analyze their workload, identify overworking or underworking patterns, and provide recommendations for breaks, time management strategies, and wellbeing tips.
    """
    response = model.generate_content(prompt)
    return response.text

# Function to handle chat interactions
def chat_with_model(message, chat_history):
    response = model.generate_content(message)
    chat_history.append((message, response.text))
    return "", chat_history

# Main interface function
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

        # Fetch calendar data if requested
        calendar_data = ""
        if include_calendar:
            credentials = authenticate()
            calendar_data = fetch_calendar_events(credentials)

        # Generate analysis and recommendations using Gemini
        output = generate_analysis_and_recommendations(standard_hours, daily_hours, calendar_data)

        return output
    
    except ValueError:
        return "Error: Please enter valid numeric values for hours."

# Define the function to update Saturday fields visibility
def update_saturday_fields(saturday_working):
    if saturday_working == "Yes":
        return gr.update(visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)

# Gradio interface setup
with gr.Blocks(theme=gr.themes.Soft()) as interface:
    gr.Markdown(
        """
        # 🧠 **EaseAI: Workload Analysis Tool**
        Welcome to EaseAI! This tool helps you analyze your weekly workload, identify overworking or underworking patterns, and provides personalized recommendations for breaks, time management, and wellbeing.
        """
    )

    with gr.Row():
        with gr.Column():
            gr.Markdown("### ⏰ **Standard Working Hours**")
            standard_hours_weekday = gr.Textbox(label="Standard Hours (Weekday)", value="8", placeholder="Enter standard hours per weekday")
            saturday_working = gr.Radio(
                label="Working on Saturday?", 
                choices=["Yes", "No"], 
                value="No", 
                interactive=True
            )
            standard_hours_saturday = gr.Textbox(label="Standard Hours (Saturday)", value="4", placeholder="Enter standard hours for Saturday", visible=False)
            saturday_hours = gr.Textbox(label="Saturday Hours", value="0", placeholder="Enter hours worked on Saturday", visible=False)
            saturday_working.change(update_saturday_fields, saturday_working, [standard_hours_saturday, saturday_hours])

        with gr.Column():
            gr.Markdown("### 📅 **Actual Working Hours**")
            monday_hours = gr.Textbox(label="Monday Hours", value="", placeholder="Enter hours worked on Monday")
            tuesday_hours = gr.Textbox(label="Tuesday Hours", value="", placeholder="Enter hours worked on Tuesday")
            wednesday_hours = gr.Textbox(label="Wednesday Hours", value="", placeholder="Enter hours worked on Wednesday")
            thursday_hours = gr.Textbox(label="Thursday Hours", value="", placeholder="Enter hours worked on Thursday")
            friday_hours = gr.Textbox(label="Friday Hours", value="", placeholder="Enter hours worked on Friday")

    with gr.Row():
        include_calendar = gr.Checkbox(label="Include Google Calendar Data?", value=True)

    with gr.Row():
        analyze_button = gr.Button("Analyze Workload", variant="primary")

    with gr.Row():
        output = gr.Textbox(label="Analysis and Recommendations", lines=15, placeholder="Your analysis will appear here...")

    # Chat interface for follow-up questions
    with gr.Row():
        chatbot = gr.Chatbot(label="Chat with EaseAI")
        msg = gr.Textbox(label="Ask a follow-up question", placeholder="Type your question here...")
        clear = gr.Button("Clear Chat")

    # Function to handle chat interactions
    def respond(message, chat_history):
        response = model.generate_content(message)
        chat_history.append((message, response.text))
        return "", chat_history

    # Connect the chat interface
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: [], None, chatbot, queue=False)

    analyze_button.click(
        easeai_interface,
        [standard_hours_weekday, monday_hours, tuesday_hours, wednesday_hours, thursday_hours, friday_hours, 
         saturday_working, standard_hours_saturday, saturday_hours, include_calendar],
        output
    )

# Launch the app
interface.launch(server_port=8080)