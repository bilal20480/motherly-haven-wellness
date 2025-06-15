# Pregnancy Wellness Planner
# Adapted from Autism Wellness Planner

import streamlit as st
import google.generativeai as genai
import base64
import os
import re
from io import BytesIO
from xhtml2pdf import pisa
import markdown2

# --- Background Image Loader ---
def get_base64_image():
    for ext in ["webp", "jpg", "jpeg", "png"]:
        image_path = f"background.{ext}"
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    return None

bg_img = get_base64_image()

# --- Page Setup ---
st.set_page_config(page_title="Pregnancy Wellness Planner", layout="centered")

if bg_img:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image;base64,{bg_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.7);
            padding: 2rem 3rem;
            border-radius: 18px;
            margin-top: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333333;
            font-family: 'Segoe UI', sans-serif;
        }}
        .export-buttons {{
            margin-top: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- App Title ---
st.title("🤰 Pregnancy & Postpartum Wellness Planner")

# --- API Configuration ---
genai.configure(api_key="AIzaSyBqx7s51Swc_l8jJILSjWjqyeNYvJXnFj0")

# --- State Initialization ---
if "step" not in st.session_state:
    st.session_state.step = 0
if "name" not in st.session_state:
    st.session_state.name = ""
if "month" not in st.session_state:
    st.session_state.month = ""
if "phase" not in st.session_state:
    st.session_state.phase = "pregnancy"
if "answers" not in st.session_state:
    st.session_state.answers = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "planner_generated" not in st.session_state:
    st.session_state.planner_generated = False

# --- Replay all messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Utilities ---
def chat_bot(message):
    with st.chat_message("assistant"):
        st.markdown(message)
    st.session_state.messages.append({"role": "assistant", "content": message})

def user_message(message):
    with st.chat_message("user"):
        st.markdown(message)
    st.session_state.messages.append({"role": "user", "content": message})

# --- Questions ---
questions = {
    "pregnancy": [
        "How many weeks along are you currently?",
        "How are you feeling physically and emotionally these days?",
        "Are there any pregnancy symptoms or conditions you’re dealing with (e.g., nausea, back pain, gestational diabetes)?",
        "How would you describe your sleep quality and routine lately?",
        "Do you have any preferred ways to stay active, like yoga, walking, or dancing?",
        "Would you like help managing stress or mood changes during pregnancy?"
    ],
    "postpartum": [
        "How many weeks postpartum are you?",
        "How is your energy level throughout the day?",
        "How are you feeling mentally and emotionally after delivery?",
        "Are you experiencing any pain, sleep disruptions, or healing-related concerns?",
        "Would you like to focus more on physical recovery or mental wellness activities right now?",
        "Do you have a support system or need ideas for bonding and self-care while caring for the baby?"
    ]
}

# --- Initial Greeting ---
if st.session_state.step == 0:
    chat_bot("👋 Hello, mama! I'm here to guide you to feel your best. Are you currently pregnant or in the postpartum phase?")
    st.session_state.step = 1

# --- Input Field ---
user_input = st.chat_input("Type your answer...")

# --- Main Logic ---
if user_input:
    user_message(user_input)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if st.session_state.step == 1:
        if "pregnant" in user_input.lower():
            st.session_state.phase = "pregnancy"
        elif "postpartum" in user_input.lower():
            st.session_state.phase = "postpartum"
        else:
            chat_bot("Please type either 'pregnant' or 'postpartum' so I know what plan to build.")
            st.stop()
        chat_bot("Great! Let's get to know you better. What's your name?")
        st.session_state.step = 2

    elif st.session_state.step == 2:
        name_match = re.search(r"[A-Z][a-z]+", user_input)
        st.session_state.name = name_match.group(0) if name_match else "You"
        chat_bot(f"Nice to meet you, {st.session_state.name}! Let's continue.")
        chat_bot(questions[st.session_state.phase][0])
        st.session_state.step = 3

    elif st.session_state.step - 3 < len(questions[st.session_state.phase]):
        q_index = st.session_state.step - 3
        answer = user_input
        st.session_state.answers.append(answer)

        prev_q = questions[st.session_state.phase][q_index]
        feedback_prompt = (
            f"You are a kind assistant supporting a {st.session_state.phase} woman named {st.session_state.name}.\n"
            f"She answered the question:\n"
            f"Q: {prev_q}\nA: {answer}\n"
            f"Give a short, kind and encouraging sentence."
        )
        feedback_response = model.generate_content(feedback_prompt)
        chat_bot(feedback_response.text.strip())

        next_index = q_index + 1
        if next_index < len(questions[st.session_state.phase]):
            chat_bot(questions[st.session_state.phase][next_index])
        st.session_state.step += 1

    if not st.session_state.planner_generated and st.session_state.step >= len(questions[st.session_state.phase]) + 3:
        st.session_state.planner_generated = True

        prompt = (
            f"Create a 7-day wellness plan for a {st.session_state.phase} woman named {st.session_state.name}.\n\n"
        )
        for i, ans in enumerate(st.session_state.answers):
            prompt += f"Q: {questions[st.session_state.phase][i]}\nA: {ans}\n\n"
        prompt += (
            """Create a weekly wellness planner for a pregnant woman, covering all 7 days from Monday to Sunday. For each day, organize the schedule into four parts: Morning, Afternoon, Evening, and Night. Present this schedule in a clean table format, where each row represents a day and columns show activities for each time slot. Include gentle and supportive activities such as pelvic stretches, hydration reminders, prenatal vitamins, mindful walking, meditation, light chores, journaling, bonding time, and balanced meal suggestions. Ensure all activities are safe, calming, and appropriate for a pregnant woman (assume she is in the second trimester unless otherwise noted). After the table, add a short, uplifting paragraph that describes how the woman might feel emotionally during the day — supported, calm, and hopeful. Avoid headings, introductions, or extra explanations — just return the table and the emotional narrative."""
        )

        chat_bot("🪄 Generating your custom wellness planner...")
        response = model.generate_content(prompt)
        content = response.text.strip()
        chat_bot(content)

        def convert_markdown_to_pdf(md_text):
            html_body = markdown2.markdown(md_text)
            html = f"<html><body>{html_body}</body></html>"
            result = BytesIO()
            pisa.CreatePDF(html, dest=result)
            result.seek(0)
            return result

        pdf_data = convert_markdown_to_pdf(content)

        st.download_button(
            label="📄 Download Wellness Plan as PDF",
            data=pdf_data,
            file_name=f"{st.session_state.name}_wellness_plan.pdf",
            mime="application/pdf"
        )