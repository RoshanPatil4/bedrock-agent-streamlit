from invoke_agent import invoke
import streamlit as st
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw
import os


# Streamlit page configuration
st.set_page_config(page_title="Cloud Policy Assistant", page_icon="☁️", layout="wide")

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Title
st.markdown("<h1 style='text-align:center;'>Cloud Policy Assistant</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center; color:silver'>Ask about cloud, IT, or policy guidelines from RBI & MeitY.</h5>", unsafe_allow_html=True)
st.markdown("---")

prompt = st.text_area(
    "Ask your question",
    placeholder="e.g., What are RBI’s guidelines for cloud outsourcing?",
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
    st.write("1️⃣ You ask a question about RBI/MeitY cloud or IT policy.")
    st.write("2️⃣ The assistant searches the uploaded government policy documents.")
    st.write("3️⃣ It gives an answer with proper source citations.")
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
    response = invoke(prompt)
    
    response_data = response  # Already a parsed dict
    print("TRACE & RESPONSE DATA ->", response_data)

    try:
        all_data = format_response(response_data.get("trace", ""))  # Display trace in sidebar
        the_response = response_data.get("message", "No response received.")

        # Add citations at the end of the assistant message
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
    st.info("Session has been reset.")
    st.session_state['history'].clear()

# Display conversation history
st.write("## Conversation History")

# Load images outside the loop to optimize performance
BASE_DIR = os.path.dirname(__file__)
human_image = Image.open(os.path.join(BASE_DIR, "human.png"))
robot_image = Image.open(os.path.join(BASE_DIR, "robot.png"))
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

# Example Prompts Section (Cloud & Policy-Focused)
# Creating a list of prompts for the Knowledge Base section
knowledge_base_prompts = [
    {"Prompt": "What are RBI's guidelines for outsourcing cloud services?"},
    {"Prompt": "What does MeitY say about developing cloud-ready applications?"},
    {"Prompt": "Explain RBI's requirements for setting up a Security Operations Center (SOC)."},
    {"Prompt": "What is the role of the IT Strategy Committee in banks?"},
    {"Prompt": "Give a summary of the e-Kranti framework under the Digital India initiative."}
]

# Creating a list of prompts for the Action Group section (leave empty or remove if not used)
action_group_prompts = []

st.markdown("---")
# --- Example Prompts Section ---
st.markdown("## Example Queries")

# Display prompts in bullet format instead of table (more readable)
for item in knowledge_base_prompts:
    st.markdown(f"- **{item['Prompt']}**")

# Optional: Skip if action group is disabled
if action_group_prompts:
    st.markdown("---")
    st.markdown("## ⚙️ Example Action Queries")
    for item in action_group_prompts:
        st.markdown(f"- **{item['Prompt']}**")
