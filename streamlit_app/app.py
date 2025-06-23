import invoke_agent as agenthelper
import streamlit as st
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw

# Streamlit page configuration
st.set_page_config(page_title="Banking Buddy", page_icon="🏦", layout="wide")

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Title
st.markdown("<h1 style='text-align:center;'>Banking Buddy</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center; color:silver'>Ask anything about banking and get answers with cited sources.</h5>", unsafe_allow_html=True)
st.markdown("---")

prompt = st.text_area(
    "Ask your question",
    placeholder="e.g., What is the penalty for premature withdrawal of a fixed deposit?",
    height=68,  # starting height
    max_chars=2000
)
# Strip only if something was entered
prompt = prompt.strip() if prompt else ""



# Add some vertical spacing
st.markdown("")

# Display buttons side-by-side with spacing and icons
col1, col2 = st.columns([2.2, 15])

with col1:
    submit_button = st.button("Ask Question", type="primary")
with col2:
    end_session_button = st.button("Reset Session")
st.markdown("---")

# Sidebar for user input
# --- Sidebar (context + instructions) ---
with st.sidebar:
    st.header("How it works")
    st.write("1️⃣ You ask a banking-related question.")
    st.write("2️⃣ The Banking Buddy queries our policy document knowledge base.")
    st.write("3️⃣ It returns an answer with cited sources.")
    st.markdown("---")
    st.header("Trace Data")


# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Function to parse and format response
def format_response(response_body):
    try:
        # Try to load the response as JSON
        data = json.loads(response_body)
        # If it's a list, convert it to a DataFrame for better visualization
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        # If response is not JSON, return as is
        return response_body

# Handling user input and responses
if submit_button and prompt:
    event = {
        "sessionId": "MYSESSION",
        "question": prompt
    }
    response = agenthelper.lambda_handler(event, None)
    
    try:
        # Parse the JSON string
        if response and 'body' in response and response['body']:
            response_data = json.loads(response['body'])
            print("TRACE & RESPONSE DATA ->  ", response_data)
        else:
            print("Invalid or empty response received")
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
        response_data = None 
    
    try:
        all_data = format_response(response_data['response'])
        the_response = response_data.get('trace_data', '')

        # Add citations at the end of the response
        citations = response_data.get('citations', [])
        if citations:
            the_response += "\n\n### 📚 Sources:\n"
            for source in citations:
                title = source.get("documentTitle", "Untitled Document")
                link = source.get("documentLink", "#")
                the_response += f"- [{title}]({link})\n"
    except:
        all_data = "..."
        the_response = "Apologies, but an error occurred. Please rerun the application"
 

    # Use trace_data and formatted_response as needed
    st.sidebar.text_area("", value=all_data, height=300)
    st.session_state['history'].append({"question": prompt, "answer": the_response})
    st.session_state['trace_data'] = the_response
  

if end_session_button:
    st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using AnyCompany Support Agent!"})
    event = {
        "sessionId": "MYSESSION",
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()

# Display conversation history
st.write("## Conversation History")

# Load images outside the loop to optimize performance
human_image = Image.open('human.png')
robot_image = Image.open('robot.png')
circular_human_image = crop_to_circle(human_image)
circular_robot_image = crop_to_circle(robot_image)

for index, chat in enumerate(reversed(st.session_state['history'])):
    # Creating columns for Question
    col1_q, col2_q = st.columns([1, 16])
    with col1_q:
        st.image(circular_human_image, width=80)
    with col2_q:
        # Generate a unique key for each question text area
        st.text_area("You:", value=chat["question"], height=68, key=f"question_{index}", disabled=True)

    # Creating columns for Answer
    col1_a, col2_a = st.columns([1, 16])
    if isinstance(chat["answer"], pd.DataFrame):
        with col1_a:
            st.image(circular_robot_image, width=80)
        with col2_a:
            # Generate a unique key for each answer dataframe
            st.dataframe(chat["answer"], key=f"answer_df_{index}")
    else:
        with col1_a:
            st.image(circular_robot_image, width=80)
        with col2_a:
            # Generate a unique key for each answer text area
            st.text_area("Buddy:", value=chat["answer"], height=100, key=f"answer_{index}")

# Example Prompts Section
# Creating a list of prompts for the Knowledge Base section
knowledge_base_prompts = [
    {"Prompt": "What is the maximum withdrawal limit for savings accounts as per RBI guidelines?"},
    {"Prompt": "Explain the RBI rules on premature withdrawal of fixed deposits."},
    {"Prompt": "What are the KYC requirements for opening a bank account in India?"},
    {"Prompt": "Give me a summary of RBI's policy on digital lending."},
    {"Prompt": "Are there RBI rules about ATM transaction limits or charges?"}
]

# Creating a list of prompts for the Action Group section
action_group_prompts = [
    {"Prompt": "Calculate EMI for a ₹5 lakh loan at 10% interest for 5 years."},
    {"Prompt": "What will be the total interest paid on a ₹2 lakh loan at 9.5% for 3 years?"},
    {"Prompt": "Calculate loan eligibility for ₹50,000 monthly salary."},
    {"Prompt": "I want to apply for a home loan. What documents are needed?"},
    {"Prompt": "Create a summary of my loan repayments over 12 months."}
]

st.markdown("---")
# --- Example Prompts Section ---
st.markdown("## Example Knowledge Base Queries")

# Display prompts in bullet format instead of table (more readable)
for item in knowledge_base_prompts:
    st.markdown(f"- **{item['Prompt']}**")

st.markdown("---")

# --- Action Group Test Prompts ---
st.markdown("## Example Action Group Queries")


for item in action_group_prompts:
    st.markdown(f"- **{item['Prompt']}**")
