import streamlit as st
import json
import os
import requests
import queue
from google.cloud import pubsub_v1

# Setup
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "prompt-wars-bengaluru-2026")
SUBSCRIPTION_NAME = "omnibridge-hitl-queue-sub"
TOPIC_NAME = "omnibridge-hitl-queue"

# Create subscriber client
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)

st.set_page_config(
    page_title="Omni-Bridge Command Center",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Omni-Bridge Real-time Command Center")
st.markdown("---")

# Session state for incoming incidents
if 'incidents' not in st.session_state:
    st.session_state.incidents = []

# Sidebar: Skill Toggles
st.sidebar.header("🛠️ Agent Configuration (Skills)")
skill_security = st.sidebar.toggle("Security & Governance Skill", value=False)
skill_memory = st.sidebar.toggle("Memory Management Skill", value=False)

# Pull from Pub/Sub
def callback(message):
    data = json.loads(message.data.decode("utf-8"))
    st.session_state.incidents.insert(0, data)
    message.ack()

def pull_messages():
    try:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 5},
            timeout=2.0
        )
        for msg in response.received_messages:
            data = json.loads(msg.message.data.decode("utf-8"))
            st.session_state.incidents.insert(0, data)
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": [msg.ack_id]}
            )
    except Exception as e:
        # Silently fail if no messages or other errors
        pass

# Dashboard Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📡 Inbound Execution Payloads (HITL Queue)")
    if st.button("Refresh Queue"):
        pull_messages()
    
    for i, inc in enumerate(st.session_state.incidents[:10]):
        with st.expander(f"Incident: {inc.get('incident_id', 'Unknown')}"):
            st.json(inc)

with col2:
    st.subheader("🧪 Test Execution (With Active Skills)")
    
    test_text = st.text_area("Input Text (Simulate Incident)", "My SSN is 123-45-6789 and I see a fire near 12.5 lat 77.5 long.")
    
    if st.button("Simulate Pipeline Execution"):
        # Headers to load skills
        headers = {}
        active_skills = []
        if skill_security: active_skills.append("security")
        if skill_memory: active_skills.append("memory")
        if active_skills:
            # We assume our updated main.py looks for this header
            headers["X-Omni-Skills"] = ",".join(active_skills)
        
        # Call Backend (Assume localhost for Dev)
        try:
            # Note: We'll use multipart/form-data as per main.py
            files = {"text": (None, test_text)}
            # We assume main.py is running on port 8080 (Cloud Run / Local)
            res = requests.post("http://localhost:8080/v1/incident/ingest", files=files, headers=headers)
            if res.status_code == 200:
                st.success("Successfully processed with active skills!")
                st.json(res.json())
            else:
                st.error(f"Error: {res.status_code} - {res.text}")
        except Exception as e:
            st.error(f"Failed to connect to Omni-Bridge Backend: {e}")

st.sidebar.markdown("---")
st.sidebar.info("This Command Center acts as the HITL gateway for unverified payloads.")
